"use client";

import { cn } from "@/lib/utils";

/**
 * 5-segment SELL→BUY gauge with a marker at the score
 * (plan/03 §4 ScoreBar; score scale ±15 from compute_signal).
 */
export function ScoreBar({ score }: { score: number }) {
  const clamped = Math.max(-15, Math.min(15, score));
  const pct = ((clamped + 15) / 30) * 100;

  return (
    <div className="space-y-1">
      <div className="relative h-2 w-full overflow-visible rounded-full bg-gradient-to-r from-down via-gold to-up">
        <span
          className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-foreground shadow"
          style={{ left: `${pct}%` }}
          aria-hidden
        />
      </div>
      <div
        className="flex justify-between font-mono text-[10px] uppercase tracking-wider text-muted-foreground"
        aria-label={`Score ${score} of plus-minus 15`}
      >
        <span className="text-down">SELL</span>
        <span>HOLD</span>
        <span className="text-up">BUY</span>
      </div>
    </div>
  );
}

export function ScoreValue({
  score,
  className,
}: {
  score: number;
  className?: string;
}) {
  const sign = score > 0 ? "+" : "";
  const tone =
    score > 0 ? "text-up" : score < 0 ? "text-down" : "text-muted-foreground";
  return (
    <span className={cn("font-mono font-semibold", tone, className)}>
      {sign}
      {score}
    </span>
  );
}
