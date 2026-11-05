"""Score stored news articles with FinBERT and roll the results up.

Phase 2. Phase 1 (`scrape_news.py`) only collects and stores headlines; this is
where the AI actually runs — once, offline, over the whole corpus. After this,
no user request ever loads the model.

Usage from `backend/`:

    python -m scripts.score_sentiment --status          # what is scored so far
    python -m scripts.score_sentiment --score --aggregate
    python -m scripts.score_sentiment --score --symbol ADANIENT.NS
    python -m scripts.score_sentiment --score --aggregate --batch-size 32

Idempotent: articles that already have a score are skipped, so re-running is
free and an interrupted run continues where it stopped.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time

from app.core.db import init_db
from app.core.news_db import init_news_db
from app.modules.news.sentiment import service

logger = logging.getLogger("score_sentiment")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="score_sentiment",
        description="Score stored articles with FinBERT and aggregate per stock.",
    )
    parser.add_argument(
        "--score",
        action="store_true",
        help="Score every article that has no sentiment row yet.",
    )
    parser.add_argument(
        "--aggregate",
        action="store_true",
        help="Rebuild the per-stock summaries and the 1M/3M/1Y/3Y period cards.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show how much of the corpus is scored, then exit.",
    )
    parser.add_argument("--symbol", default=None, help="Restrict to one symbol.")
    parser.add_argument("--limit", type=int, default=None, help="Cap articles scored.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="FinBERT inference batch size (default: 64; bigger = faster on CPU).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    return parser.parse_args(argv)


async def _run(args: argparse.Namespace) -> int:
    print("[*] Connecting to databases and verifying schema...")
    # Create tables if absent — idempotent, and lets --status work on a
    # database that has never been scored.
    await init_news_db()
    await init_db()

    if args.status or not (args.score or args.aggregate):
        print("[*] Fetching corpus status...")
        status = await service.scoring_status()
        print("\n── scoring status ──")
        print(f"  articles total   : {status['articles_total']:,}")
        print(f"  articles scored  : {status['articles_scored']:,}")
        print(f"  articles pending : {status['articles_pending']:,}")
        print(f"  symbols summarised: {status['symbols_summarised']}")
        print(f"  period rows       : {status['period_rows']:,}")
        if status["model_versions"]:
            print(f"  model versions    : {status['model_versions']}")
        if not (args.score or args.aggregate):
            print("\n(nothing to do — pass --score and/or --aggregate)")
        return 0

    started = time.perf_counter()

    if args.score:
        target_str = f" for {args.symbol.upper()}" if args.symbol else " across all stocks"
        limit_str = f" (capped at {args.limit:,})" if args.limit else ""
        print(f"\n[*] Starting FinBERT scoring{target_str}{limit_str} [batch size: {args.batch_size}]...")
        result = await service.score_pending(
            symbol=args.symbol, limit=args.limit, batch_size=args.batch_size
        )
        print("\n── scoring ──")
        print(f"  unscored seen    : {result.unscored_seen:,}")
        print(f"  scored           : {result.scored:,}")
        if result.keyword_fallback:
            print(f"  keyword fallback : {result.keyword_fallback:,}")

    aggregate = None
    if args.aggregate:
        target_str = f" for {args.symbol.upper()}" if args.symbol else " across all stocks"
        print(f"\n[*] Aggregating sentiment summaries & fetching price trends{target_str}...")
        aggregate = await service.aggregate_symbols(args.symbol)
        print("\n── aggregation ──")
        print(f"  symbols          : {aggregate['symbols']}")
        print(f"  period rows      : {aggregate['period_rows']:,}")
        print(f"  priced symbols   : {aggregate['priced_symbols']:,}")

    print(f"\n  duration         : {time.perf_counter() - started:.1f}s")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    if not args.status and not (args.score or args.aggregate):
        print("error: pass --score, --aggregate or --status", file=sys.stderr)
        return 2
    asyncio.run(_run(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())