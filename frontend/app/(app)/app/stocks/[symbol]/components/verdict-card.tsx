"use client";

import { Lightbulb } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScoreBar, ScoreValue } from "@/components/signals/score-bar";
import { VerdictBadge } from "@/components/signals/verdict-badge";
import { useSignal } from "@/lib/hooks/use-analytics";
import type { Timeframe } from "../constants";
import { cn } from "@/lib/utils";

const KIND_DOT: Record<string, string> = {
  buy: "bg-up",
  sell: "bg-down",
  neut: "bg-muted-foreground",
};

/** AI verdict rail card — verdict badge, score gauge and rule chips. */
export function VerdictCard({
  symbol,
  timeframe,
}: {
  symbol: string;
  timeframe: Timeframe;
}) {
  const signal = useSignal(symbol, timeframe.interval, timeframe.period);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <Lightbulb className="size-4 text-ai" /> Rule verdict
          </span>
          {signal.data && (
            <ScoreValue score={signal.data.score} className="text-sm" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {signal.isLoading ? (
          <>
            <Skeleton className="h-7 w-28 rounded-full" />
            <Skeleton className="h-2 w-full rounded-full" />
            <Skeleton className="h-12 w-full rounded-lg" />
          </>
        ) : signal.isError || !signal.data ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            Verdict unavailable right now.
          </p>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <VerdictBadge verdict={signal.data.verdict} size="lg" />
              <span className="font-mono text-xs text-muted-foreground">
                {Math.round(signal.data.confidence * 100)}% confidence
              </span>
            </div>

            <ScoreBar score={signal.data.score} />

            <ul className="space-y-1.5" aria-label="Signal rules">
              {signal.data.rules.map((rule) => (
                <li
                  key={rule.rule}
                  className="flex items-center gap-2 text-xs text-muted-foreground"
                >
                  <span
                    aria-hidden
                    className={cn(
                      "size-1.5 shrink-0 rounded-full",
                      KIND_DOT[rule.kind],
                    )}
                  />
                  <span>{rule.rule}</span>
                </li>
              ))}
            </ul>

            {signal.data.reasons.length > 0 && (
              <div
                className="space-y-1 rounded-lg bg-muted/60 p-3"
                aria-label="Why this verdict"
              >
                <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  Why
                </p>
                {signal.data.reasons.map((reason) => (
                  <p key={reason} className="text-xs leading-relaxed">
                    • {reason}
                  </p>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
