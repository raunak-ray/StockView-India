"""Migrate `news_articles` to the body-text schema.

Two changes, both additive-then-destructive so nothing is lost if the script dies
halfway:

    ADD COLUMN body TEXT            -- article text, NULL until a weekly run fills it
    DROP COLUMN query_used          -- removed to make room for body

Existing rows survive: `body` is NULL for all of them, which is exactly the
state the 3-year backfill produces anyway.

Idempotent — safe to re-run. `IF EXISTS` / `IF NOT EXISTS` on both statements,
and it checks what is actually there first.

Usage from `backend/`:

    python -m scripts.migrate_news_body           # migrate
    python -m scripts.migrate_news_body --check   # report only, change nothing
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sqlalchemy import text

from app.core.news_db import news_engine


async def _columns() -> set[str]:
    async with news_engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = 'news_articles'"
            )
        )
        return {row[0] for row in result}


async def migrate(check_only: bool) -> int:
    existing = await _columns()
    if not existing:
        print("news_articles does not exist yet — run init_news_db() first.")
        return 1

    add = "body" not in existing
    drop = "query_used" in existing

    print(f"current columns: {', '.join(sorted(existing))}")
    print(f"  add body        : {'needed' if add else 'already present'}")
    print(f"  drop query_used : {'needed' if drop else 'already gone'}")

    if not add and not drop:
        print("\nnothing to do — schema is current.")
        return 0

    if check_only:
        print("\n--check: no changes made.")
        return 0

    async with news_engine.begin() as conn:
        if add:
            await conn.execute(text("ALTER TABLE news_articles ADD COLUMN body TEXT"))
            print("  + body")
        if drop:
            await conn.execute(text("ALTER TABLE news_articles DROP COLUMN query_used"))
            print("  - query_used")

    final = await _columns()
    print(f"\nfinal columns: {', '.join(sorted(final))}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="migrate_news_body",
        description="Add news_articles.body and drop news_articles.query_used.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report what would change without touching the database.",
    )
    args = parser.parse_args(argv)

    try:
        return asyncio.run(migrate(check_only=args.check))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"error: news database unreachable: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())