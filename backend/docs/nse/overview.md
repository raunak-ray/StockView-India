# NSE — Overview & Endpoints

**Plain words:** talks **directly to NSE India** for data Yahoo doesn't
offer well: official quotes, the full **options chain**, and **FII/DII
money flows** (what big institutions bought/sold in ₹ crores).

## Endpoints

| Method & path | What it does | Cache |
|---|---|---|
| `GET /api/v1/nse/quote/{symbol}` | Official NSE quote | 60s |
| `GET /api/v1/nse/option-chain/{symbol}` | Options + PCR + max pain | 120s |
| `GET /api/v1/nse/fii-dii` | Institutional flows | 300s |
| `GET /api/v1/nse/advances-declines` | Market breadth | 120s |

## The jargon, translated

- **PCR** (put-call ratio): crowd fear vs greed in one number.
- **Max pain**: the price where option buyers lose most — a magnet near expiry.
- **Advances/declines**: how many stocks rose vs fell today.

## Where the code lives

`backend/app/modules/nse/`. Tests: `backend/tests/test_nse.py`.

## Good to know

Outside India, NSE usually blocks API calls → the site shows "unavailable".
That's expected; the same code works from Indian IPs. Details:
[fallback-chains.md](fallback-chains.md).
