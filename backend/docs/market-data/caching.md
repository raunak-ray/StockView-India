# Market Data — How Caching Works

**Plain words:** answers are remembered for a short time so repeat requests
are instant and we don't get blocked by Yahoo for asking too often.

```mermaid
sequenceDiagram
    actor UI as Website
    participant R as router.py
    participant C as Redis cache
    participant Y as Yahoo Finance
    UI->>R: GET /market/quote?symbol=RELIANCE.NS
    R->>C: cached copy?
    alt still fresh (30s)
        C-->>R: cached quote
    else expired / missing
        R->>Y: fetch (in a worker thread)
        Y-->>R: fresh data
        R->>C: store with TTL
    end
    R-->>UI: same JSON either way
```

## TTLs per endpoint

- Quotes **30s** · market summary & gainers **60s**
- History & sectors **300s** · company info **600s**

Same numbers as the old prototype — parity on purpose.

## If Redis is down

The cache "fails open": the app skips caching and still answers from Yahoo.
Nothing breaks, it's just slower until Redis returns.
