import Link from "next/link";
import {
  Activity,
  Blocks,
  BrainCircuit,
  CandlestickChart,
  LineChart,
  ShieldCheck,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { TextReveal } from "@/components/motion/text-reveal";
import { HeroCta } from "@/components/landing/hero-cta";
import { MarketTickerMarquee } from "@/components/landing/marquee";

const FEATURES = [
  {
    icon: CandlestickChart,
    title: "TradingView-style terminal",
    desc: "Candlesticks, S&R, SMC zones, verdict rails and marker overlays for 1,500+ NSE/BSE instruments.",
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

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-6xl items-center gap-6 px-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
              SV
            </span>
            <span className="text-sm font-semibold">StockView India</span>
          </Link>
          <nav className="ml-auto hidden items-center gap-5 text-sm text-muted-foreground md:flex">
            <Link href="#features" className="hover:text-foreground">
              Features
            </Link>
            <Link href="#how" className="hover:text-foreground">
              How it works
            </Link>
          </nav>
          <div className="ml-auto flex items-center gap-2 md:ml-0">
            <Button asChild variant="ghost" size="sm">
              <Link href="/login">Log in</Link>
            </Button>
            <Button asChild size="sm">
              <Link href="/register">Get started</Link>
            </Button>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <section className="relative overflow-hidden">
          <div
            aria-hidden
            className="dot-grid absolute inset-0 [mask-image:radial-gradient(ellipse_55%_45%_at_50%_35%,black_25%,transparent_75%)]"
          />
          <div
            aria-hidden
            className="absolute -top-32 left-1/2 h-80 w-[40rem] -translate-x-1/2 rounded-full bg-primary/15 blur-3xl"
          />
          <div className="relative mx-auto flex w-full max-w-6xl flex-col items-center px-4 pb-20 pt-24 text-center">
            <TextReveal
              as="p"
              text="India's open-source trading terminal"
              className="text-xs font-medium uppercase tracking-[0.25em] text-primary"
            />
            <TextReveal
              as="h1"
              text={[
                "Research. Signal.",
                "Backtest. Trade.",
              ]}
              className="mt-6 text-4xl font-bold tracking-tight sm:text-6xl"
            />
            <TextReveal
              as="p"
              text="The TradingView-style terminal for Indian markets — indicators, SMC zones, ML verdicts, backtests and paper trading, all free."
              className="mt-6 max-w-xl text-base text-muted-foreground sm:text-lg"
            />
            <HeroCta />
          </div>
        </section>

        <MarketTickerMarquee />

        <section id="features" className="mx-auto w-full max-w-6xl px-4 py-20">
          <h2 className="text-center text-2xl font-semibold sm:text-3xl">
            Everything a trader needs
          </h2>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className="group rounded-xl border border-border bg-card/50 p-6 transition-colors hover:border-primary/40"
              >
                <f.icon className="size-5 text-primary" />
                <h3 className="mt-4 font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="mx-auto w-full max-w-6xl px-4 pb-24">
          <div className="rounded-2xl border border-border bg-card/50 p-8 text-center sm:p-12">
            <h2 className="text-2xl font-semibold sm:text-3xl">
              From ticker to verdict in four steps
            </h2>
            <div className="mt-8 grid gap-4 text-left sm:grid-cols-4">
              {[
                ["01", "Search", "Any of ~1,500 NSE/BSE instruments"],
                ["02", "Analyze", "Indicators, SMC zones, news sentiment, ML"],
                ["03", "Backtest", "Six strategies with walk-forward checks"],
                ["04", "Trade", "Paper trade with a ₹1,00,000 portfolio"],
              ].map(([step, title, desc]) => (
                <div key={step} className="rounded-xl border border-border p-5">
                  <span className="font-mono text-xs text-primary">{step}</span>
                  <h3 className="mt-2 font-semibold">{title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-border py-6">
        <p className="text-center text-xs text-muted-foreground">
          StockView India — for research and education only. Not investment advice.
        </p>
      </footer>
    </div>
  );
}