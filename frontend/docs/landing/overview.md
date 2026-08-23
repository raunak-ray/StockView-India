# Landing — Overview

**Plain words:** the public homepage people see before logging in — the
shop window of StockView.

## Sections, top to bottom

```mermaid
flowchart TB
    H[Header — logo, links, theme toggle, auth buttons]
    HERO[Hero — title over animated aurora light, CTAs, stats, terminal mock]
    TIC[Ticker marquee — scrolling decorative prices]
    B[Bento features — 6 cards with animated SVG illustrations]
    W[How it works — Search → Analyze → Backtest → Trade]
    T[Team — 4 member cards]
    C[CTA band — “Start paper trading in under a minute”]
    F[Footer — link columns, socials, disclaimer, sweeping light beam]
    H --> HERO --> TIC --> B --> W --> T --> C --> F
```

## Feel

Modern and calm, not flashy: one animated light in the hero, quick entrance
fades, gently pulsing dots, slowly drawing chart lines. Everything goes
static if your OS asks for reduced motion.

## Where the code lives

- Assembly: `frontend/app/page.tsx`
- Sections: `frontend/app/components/` (hero-, bento-, team-, cta-, footer-…)
- Hero shader: `app/components/hero-shader.tsx` (raw WebGL, no libraries)
- Bento illustrations: `app/components/bento-graphics.tsx`

Edit the content yourself: [customize.md](customize.md).
