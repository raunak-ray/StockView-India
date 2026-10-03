"""Scrape news headlines into the isolated news database.

Phase 1: collection and storage only (no FinBERT).

Usage from `backend/`:

    # the whole Nifty 100 universe, last 7 days (the weekly refresh)
    python -m scripts.scrape_news --days 7

    # one-time 3-year backfill, a few symbols at a time to bound runtime
    python -m scripts.scrape_news --days 1095 --max-symbols 20

    # specific symbols
    python -m scripts.scrape_news --days 30 --symbols RELIANCE.NS TCS.NS

The scrape is idempotent: identical headlines for a symbol are stored once, so
re-running is always safe and never duplicates rows.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.core.news_db import init_news_db
from app.modules.news import symbols as symbols_mod
from app.modules.news.service import MAX_DAYS, scrape


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scrape_news",
        description="Scrape Google News headlines into the news database.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help=(
            "Look-back window per symbol (default: 7). Sliced one day at a time "
            "because a single wide query truncates. Use 1095 for a 3-year backfill."
        ),
    )
    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="Optional symbol subset (e.g. RELIANCE.NS TCS). Omit for the full universe.",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        default=None,
        help="Cap how many symbols to process (useful for long windows).",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=8,
        help=(
            "How many day-windows may be in flight at once (default: 8). This "
            "only hides latency — the real cap is --rate."
        ),
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1.5,
        help=(
            "Global requests/second cap (default: 1.5). Google returns 503 for "
            "everything if a long run hammers it faster than this. Lower is "
            "safer; higher is faster until it isn't."
        ),
    )
    parser.add_argument(
        "--list-universe",
        action="store_true",
        help="Print the scrape universe and exit.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> int:
    if args.list_universe:
        coverage = symbols_mod.coverage()
        print(f"Source : {coverage['source']} (snapshot {coverage['fetched_on']})")
        print(
            f"Covered: {coverage['covered']} of {coverage['nifty100_total']} Nifty 100 symbols"
        )
        for target in symbols_mod.targets():
            print(f"  {target.symbol:<16} {target.industry:<34} {target.display_name}")
        return 0

    if not 1 <= args.days <= MAX_DAYS:
        print(f"error: --days must be between 1 and {MAX_DAYS}", file=sys.stderr)
        return 2

    await init_news_db()
    stats = await scrape(
        days=args.days,
        symbols=args.symbols,
        max_symbols=args.max_symbols,
        concurrency=args.concurrency,
        requests_per_second=args.rate,
    )

    result = stats.as_dict()
    print("\n── scrape complete ──")
    print(f"  requests        : {result['requests']:,}")
    print(f"  articles seen   : {result['articles_seen']:,}")
    print(f"  articles stored : {result['articles_new']:,}")
    print(f"  duplicates      : {result['duplicates']:,}")
    print(f"  rejected        : {result['rejected']:,}")
    print(f"  symbols hit     : {result['symbols_processed']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    )
    return asyncio.run(_main(args))


if __name__ == "__main__":
    raise SystemExit(main())