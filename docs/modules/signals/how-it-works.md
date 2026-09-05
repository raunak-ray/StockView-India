# Signals — how it works

This page walks through the rule engine, the marker generator, and the fusion
blend. Read it once and the rest of the file is mechanical.

## The big picture — two endpoints, two pipelines

```mermaid
flowchart LR
    subgraph "/signals"
        A1[candles via market_data] --> A2[add_indicators]
        A2 --> A3[compute_signal: 10 rules]
        A3 --> A4[verdict + score + confidence + rules + reasons]
        A2 --> A5[generate_markers: MACD crossovers]
        A5 --> A6[chart arrows]
    end
    subgraph "/signals/fusion"
        B1[technical signal] --> B4[compute_fusion]
        B2[ml.predict] --> B4
        B3[news sentiment] --> B4
        B4 --> B5[fused_score + final_label + confidence_tier]
    end
```

`/signals` is self-contained. `/signals/fusion` calls `/signals` internally, plus
ML and news, then blends.

## The rule engine — `compute_signal(df)`

Takes the indicator-enriched DataFrame from `analytics.add_indicators`. Returns
a dict with `verdict`, `score`, `confidence`, `signals`, `reasons`.

### The ten rules

```mermaid
flowchart TD
    Start[Indicator frame] --> R1{RSI < 30?}
    R1 -->|yes| B1[buy +2: RSI Oversold]
    R1 -->|no| R2{RSI > 70?}
    R2 -->|yes| S1[sell -2: RSI Overbought]
    R2 -->|no| R3{RSI 40-60?}
    R3 -->|yes| N1[neut: RSI Neutral]
    R3 -->|no| R4{RSI > 60?}
    R4 -->|yes| B2[buy +1: RSI Bullish]
    R4 -->|no| S2[sell -1: RSI Bearish]
    B1 & S1 & N1 & B2 & S2 --> M{MACD cross?}
    M -->|bullish cross| B3[buy +3: MACD Up Cross]
    M -->|bearish cross| S3[sell -3: MACD Down Cross]
    M -->|above signal| B4[buy +1: MACD Bullish]
    M -->|below signal| S4[sell -1: MACD Bearish]
    B3 & S3 & B4 & S4 --> G{SMA20 vs SMA50 cross?}
    G -->|golden cross| B5[buy +4: Golden Cross]
    G -->|death cross| S5[sell -4: Death Cross]
    G -->|above| B6[buy +1: Above SMA50]
    G -->|below| S6[sell -1: Below SMA50]
    B5 & S5 & B6 & S6 --> SMA20{close vs SMA20?}
    SMA20 -->|+2%| B7[buy +1]
    SMA20 -->|-2%| S7[sell -1]
    SMA20 -->|near| N2[neut: Near SMA20]
    B7 & S7 & N2 --> BB{close vs Bollinger?}
    BB -->|above upper| B8[buy +2: BB Breakout]
    BB -->|below lower| S8[sell -2: BB Breakdown]
    BB -->|inside| N3[neut: Inside BB]
    B8 & S8 & N3 --> VOL{volume vs 20-day avg?}
    VOL -->|>1.5x and up day| B9[buy +2: High Vol + Up]
    VOL -->|>1.5x and down day| S9[sell -2: High Vol + Down]
    VOL -->|normal| N4[neut: Normal Volume]
    B9 & S9 & N4 --> Sum[Sum the votes = score]
```

The score range is roughly **−18 to +18** (worst case: all bearish rules fire
with maximum weight). In practice, scores cluster between −6 and +6.

### Verdict from score

| Score | Verdict |
|---|---|
| ≥ +5 | `BUY` |
| +2 to +4 | `WEAK BUY` |
| −1 to +1 | `HOLD` |
| −4 to −2 | `WEAK SELL` |
| ≤ −5 | `SELL` |

### Confidence

```python
directional = [(label, kind) for label, kind in signals if kind in ("buy", "sell")]
if directional:
    dominant = "buy" if score >= 0 else "sell"
    agree = sum(1 for _, k in directional if k == dominant)
    agreement_ratio = agree / len(directional)
else:
    agreement_ratio = 0.5

score_norm = min(abs(score) / 7.0, 1.0)
raw_conf = 0.60 * agreement_ratio + 0.40 * score_norm
confidence = 0.50 + 0.50 * raw_conf
```

Two ingredients:

- **Agreement ratio** (60% weight): how many directional rules voted with the
  dominant side.
- **Score magnitude** (40% weight): how big the score is (capped at 7).

Final is floored at 0.50 — even an all-overbought bearish score on a quiet day
shows ≥ 0.5 confidence. Floor protects the UI from showing "30% confident"
which users read as "broken".

### Reasons

Every rule that votes with weight (≥ 2) appends a human-readable line to
`reasons`. Neutral and ±1 votes do not — keeps the list short and meaningful.
Examples:

- `"RSI 28.4 < 30 — oversold zone"`
- `"SMA20 × SMA50 Golden Cross"`
- `"Volume 1.7× avg with price up"`

## Markers — `generate_markers(df)`

Returns the buy/sell arrows for the chart, one per MACD crossover.

```mermaid
flowchart TD
    Start[Indicator frame] --> Loop[i = 1 to N-1]
    Loop --> Diff[macd - signal at i-1 and i]
    Diff --> SignCheck{crossed zero?}
    SignCheck -->|negative to positive| RSI{current RSI < 65?}
    SignCheck -->|positive to negative| RSI2{current RSI > 35?}
    RSI -->|yes| Buy[BUY arrow at close * 0.993 below bar]
    RSI2 -->|yes| Sell[SELL arrow at close * 1.007 above bar]
    RSI -->|no| Skip[skip this crossover]
    RSI2 -->|no| Skip
    Buy & Sell & Skip --> Loop
```

The RSI filter (`< 65` for buys, `> 35` for sells) blocks crossovers that happen
in extreme momentum — those are usually continuations, not reversals. The price
multipliers (`0.993`, `1.007`) nudge the marker slightly off the candle so the
arrow is visible.

Output: a list of `{ time, position: "belowBar"|"aboveBar", kind: "buy"|"sell", price }`
sorted by time.

## Fusion — `compute_fusion(tech, ml_result, news_result)`

The three layers are computed independently, then blended.

### Step 1: Normalise each layer to −1..+1

| Layer | Raw value | Normalised |
|---|---|---|
| Technical | `score` (int, typically −18..+18) | `clip(score / 12, -1, 1)` |
| ML | `up_prob` (0–100) | `(up_prob − 50) / 50` |
| News | `score` (float, −1..+1 from sentiment) | as-is |

The technical normalisation uses 12 as the "saturated" score because that
captures roughly the strongest realistic signal without extreme-case bonus.

### Step 2: Re-weight if a layer is missing

```mermaid
flowchart LR
    A[technical always available] --> C[available_weights list]
    B[ML available?] --> C
    D[news available?] --> C
    C --> E[sum weights]
    E --> F[divide each weight by sum]
    F --> G[fused_score = sum w_norm * layer_score]
```

If ML and news are both missing, only technical is in the list, its weight is
1.0, and the fused score equals the technical score.

A layer is "missing" when:

- ML: `ml_result is None` (training failed or symbol not in any model's training
  set).
- News: `news_result is None` **or** `news_result["score"] == 0.0` (no
  headlines, or all neutral).

### Step 3: Map fused score to final label

| Fused score | Final label |
|---|---|
| ≥ +0.35 | `STRONG BUY` |
| +0.12 to +0.34 | `BUY` |
| −0.11 to +0.11 | `NEUTRAL` |
| −0.34 to −0.12 | `SELL` |
| ≤ −0.35 | `STRONG SELL` |

Each label has a fixed description (e.g. "All 3 layers aligned bullish. High
conviction upside expected.").

### Step 4: Confidence tier

```python
direction_labels = [l for l in [ts_label, ml_label, ns_label] if l != "NEUTRAL"]
if not direction_labels:
    tier = "LOW"
elif all agree:
    tier = "HIGH"
else:
    tier = "MEDIUM"
```

- `HIGH`: every layer with a direction agrees (e.g. technical BULLISH, ML
  BULLISH, news BULLISH).
- `MEDIUM`: at least one layer has a direction and disagrees with the others.
- `LOW`: no layer has a direction (everything is NEUTRAL or missing).

### Step 5: "What's missing" flags

If ML is missing: `"ML prediction not available — training data insufficient."`
If news is missing: `"News sentiment unavailable — no headlines fetched."`

These show up in the UI so the user knows why confidence is not HIGH.

## Async API

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant Sig as signals router
    participant Tech as compute_signal
    participant ML as ml.predict
    participant News as sentiment

    Note over Sig: GET /signals/fusion?symbol=...
    Sig->>Tech: get_signal (technical verdict)
    Tech-->>Sig: tech dict
    Sig->>ML: predict(symbol, use_lstm=False) wrapped in try
    alt ML succeeds
        ML-->>Sig: ml_result
    else ML fails
        Note over Sig: ml_result = None
    end
    Sig->>News: get_headlines + get_sentiment_score wrapped in try
    alt news has headlines
        News-->>Sig: news_result
    else news fails or empty
        Note over Sig: news_result = None
    end
    Sig->>Sig: compute_fusion (in threadpool)
    Sig-->>FE: FusionResponse
```

The ML and news calls are wrapped in `try/except` with bare `pass` — failures
are **expected**. Missing layers are a feature, not an error. The whole point
of the re-weighting is to give a useful answer when one layer is down.

## What can go wrong

| Symptom | Cause |
|---|---|
| Verdict stuck at HOLD | All rules vote neutral or the score is in −1..+1 |
| Score is huge (±15) | Multiple strong signals aligned — uncommon but valid (e.g. golden cross + RSI oversold + volume spike) |
| `markers` empty | No MACD crossovers in the chosen period |
| Fusion always `NEUTRAL` | All layers return score 0 or all missing |
| Fusion `LOW` confidence with `HIGH` technical | News and ML both missing — only technical carries weight |
| `fused_score > 0.35` but tech verdict is `HOLD` | ML or news is strongly bullish enough to overcome neutral technical |

Related: [implementation](implementation.md) for the file map and helper details.