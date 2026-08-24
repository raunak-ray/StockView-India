"use client";

import { cn } from "@/lib/utils";

const VERDICT_TONES: Record<string, string> = {
  "STRONG BUY": "border-up/30 bg-up/10 text-up",
  BUY: "border-up/30 bg-up/10 text-up",
  "WEAK BUY": "border-up/30 bg-up/10 text-up",
  HOLD: "border-gold/30 bg-gold/10 text-gold",
  NEUTRAL: "border-gold/30 bg-gold/10 text-gold",
  "WEAK SELL": "border-down/30 bg-down/10 text-down",
  SELL: "border-down/30 bg-down/10 text-down",
  "STRONG SELL": "border-down/30 bg-down/10 text-down",
};

function glyph(verdict: string): string {
  if (verdict.endsWith("BUY")) return "▲";
  if (verdict.endsWith("SELL")) return "▼";
  return "◆";
}

/** Verdict pill — teal BUY family, gold HOLD, red SELL family (plan/03 §4). */
export function VerdictBadge({
  verdict,
  size = "sm",
}: {
  verdict: string;
  size?: "sm" | "lg";
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border font-mono font-semibold tracking-wide",
        size === "lg" ? "px-3 py-1 text-sm" : "px-2.5 py-0.5 text-xs",
        VERDICT_TONES[verdict] ?? "border-border bg-muted text-muted-foreground",
      )}
    >
      {glyph(verdict)} {verdict}
    </span>
  );
}
