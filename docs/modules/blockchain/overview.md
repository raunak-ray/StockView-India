# Blockchain — what it is

The blockchain module writes every prediction to an Ethereum-compatible
chain and reads it back. The point is **immutability**: once a prediction
for TCS.NS is on the chain, nobody — not the user, not the backend, not
the database — can quietly edit it to a different number.

It is a **write-once ledger of predictions**, not a trading system. It
does not move money, does not hold keys, and does not decide what to buy.

## What gets stored

One `Prediction` struct per write:

| Field | Type | Example | Note |
|---|---|---|---|
| `stockName` | `string` | `"RELIANCE.NS"` | Yahoo ticker, as typed |
| `currentPrice` | `uint256` | `116770` | **stored ×100** — see below |
| `predictedPrice` | `uint256` | `118137` | **stored ×100** |
| `direction` | `string` | `"NEUTRAL"` | BUY / HOLD / SELL |
| `confidence` | `uint256` | `68` | already a percentage |
| `upProbability` | `uint256` | `68` | already a percentage |
| `downProbability` | `uint256` | `32` | already a percentage |
| `signalScore` | `int256` | `11` | **stored ×100**, signed |
| `stopLoss` | `uint256` | `114610` | **stored ×100** |
| `targetPrice` | `uint256` | `153772` | **stored ×100** |
| `timestamp` | `uint256` | `1790922130` | set by the contract |

### Why prices are ×100

Solidity has no decimal type. `uint256` cannot hold ₹1167.70 — it would
truncate to `1167`, losing 70 paise. So every price and score is
multiplied by 100 before the write and divided by 100 after the read.

```
write:  ₹1167.70  →  round(1167.70 × 100)  →  116770  →  on chain
read:   116770     →  116770 ÷ 100          →  1167.70
```

Two decimal places is all an NSE stock price ever needs, and the
round-trip is exact for anything under ₹9.2 crore.

`signalScore` is the one **signed** field. The fusion score runs from
−1.0 to +1.0, so it needs `int256` — `uint256` would reject a negative
verdict.

## What you can do

Four endpoints, all under `/api/v1/blockchain`, all requiring a login:

- `GET /blockchain/status` — is the chain up, what block is it on, which
  account signs.
- `POST /blockchain/predictions` — write one prediction you supply
  yourself.
- `POST /blockchain/predictions/auto` — compute a prediction from the
  other modules and write it. **This is what the UI calls.**
- `GET /blockchain/predictions/latest` — read the newest prediction on
  the whole chain.

There is no "delete prediction" endpoint, and there is no "update
prediction" endpoint. That is the point. A changed prediction is a **new**
entry, so the history of what the model said over time stays intact.

## The duplicate rule

Auto-save compares the prediction it just computed against the newest
prediction **for that same symbol**. If all ten fields match, it returns
the existing block number and writes nothing.

```
POST /predictions/auto {"symbol": "RELIANCE.NS"}   (1st time)
→ saved: true,  block_number: 2,  tx: 0xe937…

POST /predictions/auto {"symbol": "RELIANCE.NS"}   (2nd time, nothing changed)
→ saved: false, block_number: 2,  tx: null
```

Why this matters: the UI posts on every page view. Without the check,
reloading a stock page ten times would write ten transactions and burn
ten times the gas for identical data. With it, the chain only grows when
the prediction actually **changed**.

The comparison is exact — all ten fields, after rounding to the same
precision the chain stores. A price that moved from ₹1167.70 to ₹1167.71
is a different prediction and does get written.

## Where the numbers come from

`predictions/auto` does not invent anything. It calls four existing
modules and assembles their output:

| Field | Source module | Call |
|---|---|---|
| `currentPrice` | market-data | `get_quote(symbol)` |
| `predictedPrice` | ML | `predict(symbol, use_lstm=False)` |
| `confidence`, `upProbability`, `downProbability` | ML | same call |
| `direction`, `signalScore` | signals | `get_fusion(symbol, "1d", "2y")` |
| `stopLoss` | analytics | nearest support, else `price × 0.98` |
| `targetPrice` | analytics | nearest resistance, else `price × 1.03` |

If the ML call returns no price, the module falls back to the current
price rather than writing a null. If analytics has no support level, the
2% / 3% fallback keeps the record complete — a prediction with a missing
stop-loss is not useful to read back later.

## Which chain

**Ganache**, a local Ethereum-compatible node. It runs in Docker and
listens on host port `7545` (internal `8545`). No real money, no gas
fees, no testnet account needed.

```
Docker ──▶ Ganache :7545 ──▶ truffle migrate ──▶ StockPrediction contract
                                              │
                              FastAPI ────────┘ via web3.py over JSON-RPC
```

The chain is **wiped when Ganache restarts.** That is the single most
common source of confusion — see [known issues](#known-issues).

## Why a local chain

- **Free and instant.** No faucet, no gas, no waiting for confirmations.
- **Deterministic.** Ganache's `--wallet.deterministic` flag always
  produces the same accounts, so the first deploy lands on the same
  address every time.
- **No accounts needed.** Real chains need a funded wallet, an RPC
  provider key, and nonce management. Not worth it to prove a write path
  works.

The cost is that none of it is permanent. This module demonstrates
*that* predictions can be written immutably, not *where* they live in
production.

## Where it lives in the codebase

- Smart contract: `blockchain/contracts/StockPrediction.sol`
- Truffle setup: `blockchain/truffle-config.js`,
  `blockchain/migrations/2_deploy_contract.js`
- Deploy helper: `blockchain/deploy.sh`
- Compiled ABI: `backend/app/modules/blockchain/abi/StockPrediction.json`
- Backend: `backend/app/modules/blockchain/`
  - `service.py` — web3 calls, the duplicate check, the auto-save pipeline
  - `router.py` — the four endpoints
  - `schemas.py` — request/response models
- Config: `blockchain_rpc_url` + `blockchain_contract_address` in
  `backend/app/core/config.py`
- Frontend API client: `frontend/lib/api/blockchain.ts`
- Frontend consumer: the verdict card on the stock terminal

## Consumed by (frontend pages and other modules)

- [Stock terminal](../../pages/stock-terminal/overview.md) — the fusion
  verdict card shows the verification status.
- Nothing reads it server-side. The blockchain module **depends on**
  market-data, ML, signals and analytics, but none of them know it
  exists. The dependency arrow points one way.

## What it does not do

- **No real chain.** Ganache only. No Ethereum, no Polygon, no testnet.
- **No private keys.** Signing uses Ganache's unlocked first account.
  There is no keystore and no key management.
- **No gas management.** Ganache does not meter it. On a real chain this
  would need a gas strategy.
- **No historical reads by symbol.** Only "latest overall" and the
  newest-for-one-symbol. There is no endpoint that returns the full
  history of TCS.NS.
- **No authentication on the contract.** `addPrediction` is `public` with
  no access control. On a real chain anyone could write. Fine for a local
  demo; would need an `onlyOwner` modifier in production.
- **No off-chain index.** The chain is the only store. Querying it is
  slow as records accumulate.

## Known issues

- **Ganache restart wipes the chain.** Block numbers restart at 0 and the
  contract address in `backend/.env` points at nothing. Re-run
  `blockchain/deploy.sh` after every Ganache restart.
- **The duplicate check is a linear scan.** It walks backwards from the
  newest prediction until it finds a matching symbol. Fine for tens of
  records, slow for thousands. See
  [implementation](implementation.md#9-performance-the-linear-scan).
- **The verdict card writes on every page view.** The `useEffect` fires
  on mount. The duplicate check absorbs the repeats, but it is still a
  POST per view.
- **No automated tests.** The other 13 modules have a `tests/test_*.py`.
  This one is verified by the live chain walkthrough in
  [how it works](how-it-works.md#verifying-it-by-hand), not by pytest.

## Related pages in this folder

- [How it works](how-it-works.md) — the write path, the ×100 scaling, the
  duplicate check, the auto-save pipeline, failure modes.
- [Implementation](implementation.md) — file map, every function, request
  traces, the Solidity source, gotchas.
