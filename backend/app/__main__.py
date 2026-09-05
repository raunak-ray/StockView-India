"""stockview-backend CLI.

Mirrors the npm-style "one line to run" feel of the frontend.
After `pip install -e ".[dev]"` you can run:

    stockview-backend dev      # uvicorn with --reload on :8000
    stockview-backend start    # uvicorn without reload on :8000
    stockview-backend migrate  # create all tables (idempotent)
    stockview-backend seed     # insert demo data (idempotent)
    stockview-backend test     # pytest
    stockview-backend lint     # ruff check
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import uvicorn

from app.core.db import init_db

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def _run(cmd: list[str]) -> None:
    """Run a subprocess, inheriting stdio so the user sees the live output."""
    result = subprocess.run(cmd, cwd=BACKEND_ROOT)
    sys.exit(result.returncode)


def dev() -> None:
    """Start the dev server with hot reload on :8000."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


def start() -> None:
    """Start the production-style server (no reload) on :8000."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)


def migrate() -> None:
    """Create all tables declared in the SQLAlchemy models.

    Idempotent — uses `Base.metadata.create_all`, so existing tables
    are left alone. This is the project's schema bootstrap.

    (The project doesn't use Alembic yet — schema changes are made by
    editing the models and re-running this command. For real schema
    migrations, set up Alembic.)
    """
    asyncio.run(init_db())
    print("✓ Tables are up to date.")


def seed() -> None:
    """Run the demo seed script (idempotent)."""
    _run([sys.executable, "scripts/seed.py"])


def test() -> None:
    """Run the test suite."""
    _run([sys.executable, "-m", "pytest", "tests/", "-v"])


def lint() -> None:
    """Run ruff on the app and tests."""
    _run([sys.executable, "-m", "ruff", "check", "app", "tests"])


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1]
    commands = {
        "dev": dev,
        "start": start,
        "migrate": migrate,
        "seed": seed,
        "test": test,
        "lint": lint,
    }

    if command not in commands:
        print(f"Unknown command: {command!r}")
        print("Available: " + ", ".join(commands))
        sys.exit(1)

    commands[command]()


if __name__ == "__main__":
    main()
