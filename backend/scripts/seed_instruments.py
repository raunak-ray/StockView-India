"""Extract the instrument master from the frozen app.py into a JSON asset.

Per plan/01 §10.3: the instrument master must be extracted from ALL_STOCKS and
_NIFTY50_STOCKS in app.py exactly (verbatim), never regenerated. This script
parses app.py with ast and evaluates only those two dict literals, so no
Streamlit/yfinance code ever runs.

Usage (from backend/):
    .venv/bin/python scripts/seed_instruments.py [path/to/app.py]

Output: app/modules/instruments/data/instrument_master.json
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

TARGETS = ("ALL_STOCKS", "_NIFTY50_STOCKS")
DEFAULT_APP_PY = Path(__file__).resolve().parents[2] / "app.py"
OUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "modules"
    / "instruments"
    / "data"
    / "instrument_master.json"
)


def _validate(name: str, value: object) -> None:
    if not isinstance(value, dict) or not value:
        raise SystemExit(f"{name} is not a non-empty dict")
    for key, entry in value.items():
        if not isinstance(key, str):
            raise SystemExit(f"{name} has non-str key {key!r}")
        if name == "ALL_STOCKS" and not isinstance(entry, str):
            raise SystemExit(f"ALL_STOCKS[{key!r}] is not a str ticker")
        if name == "_NIFTY50_STOCKS":
            ok = (
                isinstance(entry, list)
                and all(
                    isinstance(t, tuple)
                    and len(t) == 3
                    and isinstance(t[0], str)
                    and isinstance(t[1], str)
                    and isinstance(t[2], int)
                    for t in entry
                )
            )
            if not ok:
                raise SystemExit(
                    f"_NIFTY50_STOCKS[{key!r}] is not list[(ticker, label, mcap)]"
                )


def _extract_dicts(app_py: Path) -> dict[str, object]:
    tree = ast.parse(app_py.read_text(encoding="utf-8"), filename=str(app_py))
    found: dict[str, dict[str, str]] = {}

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in TARGETS:
                    if target.id in found:                        raise SystemExit(
                            f"{app_py}: duplicate assignment for {target.id}"
                        )
                    value = ast.literal_eval(node.value)
                    _validate(target.id, value)
                    found[target.id] = value

    Visitor().visit(tree)

    missing = [name for name in TARGETS if name not in found]
    if missing:
        raise SystemExit(f"Could not find {missing} in {app_py}")
    return found


def main() -> None:
    app_py = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_APP_PY
    dicts = _extract_dicts(app_py)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "stocks": dicts["ALL_STOCKS"],
        "nifty50_sectors": dicts["_NIFTY50_STOCKS"],
    }
    OUT_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(payload['stocks'])} stocks and "
          f"{len(payload['nifty50_sectors'])} sectors to {OUT_PATH}")


if __name__ == "__main__":
    main()
