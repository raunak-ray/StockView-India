import { TextReveal } from "@/components/motion/text-reveal";

import { FeaturesSection } from "./components/features-section";
import { HeroCta } from "./components/hero-cta";
import { HowItWorksSection } from "./components/how-it-works";
import { MarketTickerMarquee } from "./components/ticker-marquee";
import { SiteFooter } from "./components/site-footer";
import { SiteHeader } from "./components/site-header";

export default function LandingPage() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <SiteHeader />

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
              text={["Research. Signal.", "Backtest. Trade."]}
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
        <FeaturesSection />
        <HowItWorksSection />
      </main>

      <SiteFooter />
    </div>
  );
}
