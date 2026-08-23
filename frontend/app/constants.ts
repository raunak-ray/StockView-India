import {
  Activity,
  Blocks,
  BrainCircuit,
  CandlestickChart,
  LineChart,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

/* ============================================================================
 * LANDING PAGE CONTENT — edit everything below right here.
 * No code knowledge needed: change the text between the quotes, save, done.
 * ==========================================================================*/

/** Top navigation links (label shown in the header, href = where it scrolls). */
export const NAV_LINKS: ReadonlyArray<{ readonly label: string; readonly href: string }> = [
  { label: "Features", href: "#features" },
  { label: "How it works", href: "#how" },
  { label: "Team", href: "#team" },
] as const;

/** Hero section — the big opening screen. */
export const HERO = {
  badge: "India's open-source trading terminal",
  titleLines: ["Research. Signal.", "Backtest. Trade."],
  // The word "Trade." gets the animated gradient — keep it last & short.
  gradientWord: "Trade.",
  subtitle:
    "The TradingView-style terminal for Indian markets — indicators, SMC zones, ML verdicts, backtests and paper trading, all free.",
  primaryCta: "Start trading free",
  secondaryCta: "Try the demo account",
} as const;

/** Small trust numbers shown under the hero buttons. */
export const HERO_STATS: ReadonlyArray<readonly [value: string, label: string]> = [
  ["646", "NSE instruments"],
  ["40+", "Indicators & overlays"],
  ["6", "Backtest strategies"],
  ["₹1L", "Paper trading capital"],
] as const;

/** Feature cards — the bento grid on the landing page. */
export interface Feature {
  icon: LucideIcon;
  title: string;
  desc: string;
  // Which mini illustration to draw (picked in bento-features.tsx):
  // terminal | signal | ml | smc | nse | backtest | sectors | ledger
  graphic: string;
}

export const FEATURES: Feature[] = [
  {
    icon: CandlestickChart,
    title: "TradingView-style terminal",
    desc: "Candlesticks, S&R, SMC zones, verdict rails and marker overlays for NSE/BSE instruments.",
    graphic: "terminal",
  },
  {
    icon: BrainCircuit,
    title: "Signal engine + ML",
    desc: "45/40/15 rule fusion with SHAP explanations, LSTM, FinBERT sentiment and walk-forward evaluation.",
    graphic: "signal",
  },
  {
    icon: Activity,
    title: "Live NSE data",
    desc: "Quotes, FII/DII, advances/declines, options PCR and max-pain — with graceful fallbacks.",
    graphic: "nse",
  },
  {
    icon: Blocks,
    title: "Backtest & paper trade",
    desc: "Six-strategy engine with equity curves, monthly heatmaps and a ₹1,00,000 paper portfolio.",
    graphic: "backtest",
  },
  {
    icon: LineChart,
    title: "Sector & market maps",
    desc: "NIFTY 50 sector treemaps, gainers/losers and cross-symbol comparison in one place.",
    graphic: "sectors",
  },
  {
    icon: ShieldCheck,
    title: "Immutable signal ledger",
    desc: "Every signal fingerprinted onto a proof-of-work chain you can verify and export.",
    graphic: "ledger",
  },
];

/** "How it works" — the four steps strip. */
export const HOW_IT_WORKS_STEPS: ReadonlyArray<
  readonly [step: string, title: string, desc: string]
> = [
  ["01", "Search", "Any NSE/BSE instrument or index"],
  ["02", "Analyze", "Indicators, SMC zones, news sentiment, ML"],
  ["03", "Backtest", "Six strategies with walk-forward checks"],
  ["04", "Trade", "Paper trade with a ₹1,00,000 portfolio"],
] as const;

/* 👇 TEAM SECTION — replace the placeholder names/roles with your team. */
export interface TeamMember {
  name: string;
  role: string;
  /** Short one-liner shown under the name. */
  bio: string;
  /** Optional link (GitHub/LinkedIn). Use "#" for none. */
  href: string;
}

export const TEAM_MEMBERS: TeamMember[] = [
  {
    name: "Team Member One",
    role: "Team Lead · Backend",
    bio: "APIs, market data pipelines and the ML engine.",
    href: "#",
  },
  {
    name: "Team Member Two",
    role: "Frontend Engineer",
    bio: "Charts, design system and the landing experience.",
    href: "#",
  },
  {
    name: "Team Member Three",
    role: "ML / Data",
    bio: "Prediction models, backtesting and evaluation.",
    href: "#",
  },
  {
    name: "Team Member Four",
    role: "Research & QA",
    bio: "Market research, testing and documentation.",
    href: "#",
  },
];

/** Final call-to-action band above the footer. */
export const CTA_BAND = {
  title: "Start paper trading in under a minute",
  subtitle:
    "Create a free account, search any NSE stock and get your first verdict — no card, no broker, no risk.",
  button: "Create free account",
} as const;

/* 👇 FOOTER — link groups shown in the big footer. */
export const FOOTER = {
  tagline:
    "The open-source trading terminal for Indian markets. Research, signal, backtest and paper trade — free forever.",
  // Each group becomes one column of links.
  groups: [
    {
      title: "Product",
      links: [
        { label: "Features", href: "#features" },
        { label: "How it works", href: "#how" },
        { label: "Markets", href: "/app/markets" },
        { label: "Sectors", href: "/app/sectors" },
      ],
    },
    {
      title: "Account",
      links: [
        { label: "Log in", href: "/login" },
        { label: "Create account", href: "/register" },
        { label: "Dashboard", href: "/app" },
      ],
    },
    {
      title: "Resources",
      links: [
        { label: "API playground", href: "http://localhost:8000/docs" },
        { label: "How it works", href: "#how" },
        { label: "Team", href: "#team" },
      ],
    },
    {
      title: "Legal",
      links: [
        { label: "Disclaimer", href: "#disclaimer" },
        { label: "Education only", href: "#disclaimer" },
      ],
    },
  ],
  // Shown in the footer bottom bar.
  copyright: "StockView India",
  disclaimer:
    "StockView India is a research and education tool. Nothing here is investment advice. Market data may be delayed. Paper trading uses virtual money only.",
} as const;

/** Social icons in the footer (href = profile URL, or "#" as placeholder). */
export const FOOTER_SOCIALS: ReadonlyArray<{
  readonly label: string;
  readonly href: string;
  readonly icon: "github" | "twitter" | "linkedin";
}> = [
  { label: "GitHub", href: "#", icon: "github" },
  { label: "Twitter / X", href: "#", icon: "twitter" },
  { label: "LinkedIn", href: "#", icon: "linkedin" },
] as const;
