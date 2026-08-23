# SMC — Overview

**Plain words:** "Smart Money Concepts" — a chart-reading style that tries to
follow the big institutional players by finding their footprints on the price
chart.

## Endpoint

`GET /api/v1/smc?symbol=&interval=&period=&swing_len=&int_len=&ob_count=`

Tweak `swing_len` (zig-zag sensitivity) and `ob_count` (max order blocks) —
same slider ranges as the old app.

## What it finds

- **Swing pivots** — the zig-zag tops/bottoms of price
- **BOS / CHoCH** — moments the trend confirms or flips
- **Order blocks** — zones where institutions likely placed orders
- **FVGs** — gaps price left behind, often revisited
- **Premium / discount** — is price expensive or cheap vs its recent range

## Where the code lives

`backend/app/modules/smc/`. Tests: `backend/tests/test_smc.py`.

## Good to know

Off by default on the chart (it's busy). Enable SMC, then individually toggle
zones / order blocks / FVGs. Concept dictionary: [concepts.md](concepts.md).
