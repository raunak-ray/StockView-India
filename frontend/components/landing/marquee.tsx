"use client";

import { Marquee } from "@/components/motion/marquee";

const TICKERS = [
  "NIFTY 50 ▲ 0.84%",
  "SENSEX ▲ 0.91%",
  "NIFTY BANK ▲ 1.12%",
  "RELIANCE ▲ 1.34%",
  "TCS ▼ 0.42%",
  "HDFCBANK ▲ 0.97%",
  "INFY ▼ 0.18%",
  "BHARTIARTL ▲ 2.05%",
];

export function MarketTickerMarquee() {
  return (
    <div className="border-y border-border bg-card/40 py-3">
      <Marquee gap="48px" fade className="[--duration:40s]">
        {TICKERS.map((t) => (
          <span
            key={t}
            className="font-mono text-sm text-muted-foreground [&:has(▼)]:text-red-400 [&:has(▲)]:text-emerald-400"
          >
            {t}
          </span>
        ))}
      </Marquee>
    </div>
  );
}