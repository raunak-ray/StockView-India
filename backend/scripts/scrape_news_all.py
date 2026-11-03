"""Refresh news for every symbol already stored in the news database.

Runs the single-symbol scraper for each distinct symbol present in
`news_articles`, using the given look-back window. Useful for periodic
refreshes (default 30 days) instead of re-running full 3-year backfills.

Usage from `backend/`:

    # refresh all stored symbols, last 30 days (default)
    python -m scripts.scrape_news_all

    # refresh all stored symbols, last 7 days
    python -m scripts.scrape_news_all --days 7

Exit codes: 0 success, 2 bad arguments.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from app.core.news_db import init_news_db
from app.modules.news.service import MAX_DAYS, scrape_all


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scrape_news_all",
        description="Refresh news for every symbol already stored in the news database.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Look-back window in days for every stored symbol (default: 30).",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING"],
    )
    return parser.parse_args(argv)


async def _main(args: argparse.Namespace) -> int:
    if not 1 <= args.days <= MAX_DAYS:
        print(f"error: --days must be between 1 and {MAX_DAYS}", file=sys.stderr)
        return 2

    await init_news_db()

    try:
        stats = await scrape_all(days=args.days)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = stats.as_dict()
    print(f"\n── refresh complete ──")
    print(f"  symbols processed : {result['symbols_processed']:,}")
    print(f"  requests          : {result['requests']:,}")
    print(f"  articles seen     : {result['articles_seen']:,}")
    print(f"  articles stored   : {result['articles_new']:,}")
    print(f"  duplicates        : {result['duplicates']:,}")
    print(f"  rejected          : {result['rejected']:,}")
    print(f"  errors            : {result['errors']:,}")
    print(f"  per symbol        : {result['per_symbol']}")
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
PY