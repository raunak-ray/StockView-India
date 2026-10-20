"""Scrape news for one stock into the isolated news database.

One stock per invocation, one look-back window. That is deliberate: Google News
throttles by IP, so a run that tries to cover all 86 stocks invites the 503 that
kills the crawl, while a single-symbol run either finishes or fails cleanly and
can just be re-run. Dedupe makes re-running free.

Usage from `backend/`:

    # one stock, last 7 days — the weekly refresh, also fills article bodies
    python -m scripts.scrape_news --symbol RELIANCE.NS --days 7

    # one stock, 3 years — the backfill, headlines only
    python -m scripts.scrape_news --symbol RELIANCE.NS --days 1095

    # bare NSE symbols work too
    python -m scripts.scrape_news --symbol TCS --days 30

Exit codes: 0 success, 2 bad arguments, 3 upstream unavailable (Google News is
throttling or blocking this IP — wait, then re-run the identical command).

The full 86-stock checklist lives in `plan/stock_todo.md`.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.core.news_db import init_news_db
from app.modules.news import symbols as symbols_mod
from app.modules.news.service import MAX_DAYS, ScrapeAborted, scrape


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scrape_news",
        description="Scrape Google News articles for ONE stock into the news database.",
    )
    parser.add_argument(
        "--symbol",
        required=False,
        help="Stock to scrape, e.g. RELIANCE.NS or RELIANCE. Omit only with --list-universe.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help=(
            "Look-back window (default: 7). Sliced one day at a time because a "
            "single wide query truncates and loses ~75%% of results. Use 1095 for "
            "the 3-year backfill."
        ),
    )
    parser.add_argument(
        "--list-universe",
        action="store_true",
        help="Print the scrape universe (86 symbols) and exit.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    return parser.parse_args(argv)


def _print_universe() -> int:
    coverage = symbols_mod.coverage()
    print(f"Source : {coverage['source']} (snapshot {coverage['fetched_on']})")
    print(f"Covered: {coverage['covered']} of {coverage['nifty100_total']} Nifty 100 symbols\n")
    for target in symbols_mod.targets():
        print(f"  {target.symbol:<16} {target.industry:<34} {target.display_name}")
    print("\nScrape one with:  python -m scripts.scrape_news --symbol <SYMBOL> --days 1095")
    return 0


async def _main(args: argparse.Namespace) -> int:
    if args.list_universe:
        return _print_universe()

    if not args.symbol:
        print("error: --symbol is required (or use --list-universe)", file=sys.stderr)
        return 2

    if not 1 <= args.days <= MAX_DAYS:
        print(f"error: --days must be between 1 and {MAX_DAYS}", file=sys.stderr)
        return 2

    await init_news_db()

    try:
        stats = await scrape(symbol=args.symbol, days=args.days)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except ScrapeAborted as exc:
        print(f"\n── scrape stopped ──\n  {exc}", file=sys.stderr)
        print(
            "\n  Google News is throttling or blocking this IP.\n"
            "  Everything collected in completed 30-day checkpoints is already\n"
            "  stored — only the partial chunk in flight was lost. Wait ~30-60\n"
            "  minutes, then re-run the identical command: dedupe skips everything\n"
            "  already saved, so the retry only fetches the days still missing.",
            file=sys.stderr,
        )
        return 3

    result = stats.as_dict()
    print(f"\n── scrape complete: {result['symbol']} ──")
    print(f"  requests        : {result['requests']:,}")
    print(f"  articles seen   : {result['articles_seen']:,}")
    print(f"  articles stored : {result['articles_new']:,}")
    print(f"  duplicates      : {result['duplicates']:,}")
    print(f"  rejected        : {result['rejected']:,}")
    print(f"  bodies stored   : {result['bodies_stored']:,}")
    print(f"  bodies skipped  : {result['bodies_failed']:,}")
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