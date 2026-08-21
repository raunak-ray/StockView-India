import {
  Activity,
  Blocks,
  BrainCircuit,
  CandlestickChart,
  LineChart,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

export interface Feature {
  icon: LucideIcon;
  title: string;
  desc: string;
}

export const FEATURES: Feature[] = [
  {
    icon: CandlestickChart,
    title: "TradingView-style terminal",
    desc: "Candlesticks, S&R, SMC zones, verdict rails and marker overlays for NSE/BSE instruments.",
  },
  {
    icon: BrainCircuit,
    title: "Signal engine + ML",
    desc: "45/40/15 rule fusion with SHAP explanations, LSTM, FinBERT sentiment and walk-forward evaluation.",
  },
  {
    icon: Blocks,
    title: "Backtest & paper trade",
    desc: "Six-strategy engine with equity curves, monthly heatmaps and a ₹1,00,000 paper portfolio.",
  },
  {
    icon: Activity,
    title: "Live NSE data",
    desc: "Quotes, FII/DII, advances/declines, options PCR and max-pain — with graceful fallbacks.",
  },
  {
    icon: LineChart,
    title: "Sector & market maps",
    desc: "NIFTY 50 sector treemaps, gainers/losers and cross-symbol comparison in one place.",
  },
  {
    icon: ShieldCheck,
    title: "Immutable signal ledger",
    desc: "Every signal fingerprinted onto a proof-of-work chain you can verify and export.",
  },
];

export const HOW_IT_WORKS_STEPS: ReadonlyArray<
  readonly [step: string, title: string, desc: string]
> = [
  ["01", "Search", "Any NSE/BSE instrument or index"],
  ["02", "Analyze", "Indicators, SMC zones, news sentiment, ML"],
  ["03", "Backtest", "Six strategies with walk-forward checks"],
  ["04", "Trade", "Paper trade with a ₹1,00,000 portfolio"],
] as const;
