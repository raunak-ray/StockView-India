# StockView India — Frontend (Next.js)

React 19 / Next.js 16 frontend for the StockView India trading terminal. Tailwind CSS, Radix UI, React Query, lightweight-charts.

---

## Prerequisites

| | Linux (Ubuntu/Debian) | macOS | Windows (PowerShell) |
|---|---|---|---|
| **Node.js 18+** | `curl -fsSL https://deb.nodesource.com/setup_20.x \| sudo bash - && sudo apt install nodejs` | `brew install node@20` | Download from [nodejs.org](https://nodejs.org/) LTS |
| **npm** | Comes with Node.js | Comes with Node.js | Comes with Node.js |

Verify:
```bash
node -v    # should be 18.18+ (we use 20+)
npm -v
```

---

## 1. Clone & enter

```bash
git clone <repo-url>
cd StockView
```

## 2. Install dependencies

```bash
cd frontend
npm install
```

## 3. Run the dev server

```bash
npm run dev
```

Open http://localhost:3000.

> The backend API must be running at http://localhost:8000 for full functionality. See `backend/README.md`.

## 4. Lint

```bash
npm run lint
```

## 5. Production build

```bash
npm run build
npm start
```

---

## Project structure

```
frontend/
├── app/
│   ├── (app)/app/               # Authenticated terminal pages
│   │   ├── page.tsx             # Dashboard (index)
│   │   ├── stocks/[symbol]/     # Stock terminal (chart, ML, fusion, news)
│   │   ├── markets/             # Markets overview (NSE, options, FII/DII)
│   │   ├── sectors/             # Sector treemap
│   │   ├── compare/             # Symbol comparison
│   │   ├── backtest/            # Backtesting config + results
│   │   ├── paper-trading/       # Paper trading
│   │   ├── alerts/              # Price alerts
│   │   └── settings/            # User settings
│   ├── (marketing)/             # Landing page, login, register
│   └── layout.tsx               # Root layout (theme provider, QueryClient)
├── components/                  # Shared UI (shadcn pattern)
├── lib/
│   ├── api/                     # API fetchers (one file per module)
│   ├── hooks/                   # React Query hooks (one file per module)
│   └── utils.ts                 # cn() helper
└── public/                      # Static assets
```

## Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Landing | Marketing page with hero, features, team |
| `/login` | Login | Email + password |
| `/register` | Register | Create account |
| `/app` | Dashboard | Market indices, movers, watchlist |
| `/app/stocks/[symbol]` | Terminal | Chart + analytics + ML + fusion + news |
| `/app/markets` | Markets | NSE quote chain, options PCR, FII/DII |
| `/app/sectors` | Sectors | Nifty sector treemap |
| `/app/compare` | Compare | Two symbols side-by-side |
| `/app/backtest` | Backtest | Strategy config + equity curve + trades |
| `/app/paper-trading` | Paper Trading | Virtual portfolio (₹1L starting cash) |
| `/app/alerts` | Alerts | Price alerts CRUD |
| `/app/settings` | Settings | Profile, theme, preferences |

## Key libraries

| Library | Purpose |
|---------|---------|
| **Next.js 16** | App Router, Turbopack, React Server Components |
| **React Query** | All server state (data fetching, caching, mutations) |
| **Radix UI** | Accessible primitives (Select, Dialog, Dropdown, etc.) |
| **Tailwind CSS** | Utility-first styling + design tokens |
| **lightweight-charts** | TradingView-style price charts |
| **cmdk** | Command palette (⌘K) |
| **sonner** | Toast notifications |
| **motion** | Subtle animations (landing page) |

## Design tokens

| Token | Light | Dark | Usage |
|-------|-------|------|-------|
| Primary | `#047857` (emerald-700) | `#34d399` (emerald-400) | Buttons, links, accents |
| AI accent | `#06b6d4` (cyan-500) | `#22d3ee` (cyan-400) | ML/AI indicators |
| Up | `#34d399` | `#34d399` | Profit, buy, positive |
| Down | `#ef4444` | `#ef4444` | Loss, sell, negative |
| Gold | `#eab308` | `#eab308` | Hold, neutral, alerts |
| Info | `#3b82f6` | `#3b82f6` | Informational |
