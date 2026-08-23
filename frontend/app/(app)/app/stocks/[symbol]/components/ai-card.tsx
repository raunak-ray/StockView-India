"use client";

import { BrainCircuit, TrendingDown, TrendingUp } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { useLstmForecast, useMlCapabilities, useMlPredict } from "@/lib/hooks/use-ml";
import { formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

import type { Timeframe } from "../constants";

function ProbGauge({ upProb }: { upProb: number }) {
  const up = upProb >= 50;
  return (
    <div className="space-y-1.5">
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-down/30">
        <div
          className="h-full rounded-full bg-up transition-all duration-500"
          style={{ width: `${upProb}%` }}
        />
        <span aria-hidden className="absolute top-0 left-1/2 h-full w-px bg-border" />
      </div>
      <div className="flex justify-between font-mono text-[11px] text-muted-foreground">
        <span className="text-down">{(100 - upProb).toFixed(1)}% down</span>
        <span className={cn("font-semibold", up ? "text-up" : "text-up")}>
          {upProb.toFixed(1)}% up
        </span>
      </div>
    </div>
  );
}

/** AI prediction — ensemble verdict, model accuracies, LSTM price forecast. */
export function AiCard({ symbol, timeframe }: { symbol: string; timeframe: Timeframe }) {
  const caps = useMlCapabilities();
  const predict = useMlPredict(symbol);
  const lstm = useLstmForecast(symbol, timeframe.interval, timeframe.period);

  if (predict.isLoading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-14 text-muted-foreground">
          <Loader variant="dots" size={24} label="Training prediction models" />
          <p className="text-sm">
            Training {caps.data?.active_ensemble.join(" · ") ?? "models"} on{" "}
            {symbol.replace(/\.(NS|BO)$/, "")}…
          </p>
          <p className="text-xs text-muted-foreground/70">
            This can take up to a minute the first time.
          </p>
        </CardContent>
      </Card>
    );
  }

  if (predict.isError || !predict.data) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          AI prediction unavailable right now — try again shortly.
        </CardContent>
      </Card>
    );
  }

  const r = predict.data;
  const up = r.direction === "up";

  return (
    <div className="space-y-4">
      {/* Capability strip */}
      {caps.data ? (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Ensemble:</span>
          {caps.data.active_ensemble.map((m) => (
            <span
              key={m}
              className="rounded-full border border-ai/30 bg-ai/10 px-2 py-0.5 font-mono text-[11px] font-semibold text-ai"
            >
              {m}
            </span>
          ))}
        </div>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[1fr_340px]">
        {/* Verdict panel */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-1.5 text-sm">
              <BrainCircuit className="size-4 text-ai" />
              Next 5 days — ensemble verdict
              <InfoTip label="What is the ensemble verdict?">
                Several independent models each learn from ~2 years of price
                history and vote on whether the price closes higher in 5
                trading days. The bar shows the weighted probability of
                &quot;up&quot;. Estimates, not guarantees.
              </InfoTip>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 font-mono text-lg font-bold",
                  up ? "bg-up/15 text-up" : "bg-down/15 text-down",
                )}
              >
                {up ? <TrendingUp className="size-5" /> : <TrendingDown className="size-5" />}
                {r.prediction}
              </span>
              <span
                className={cn(
                  "rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-semibold",
                  r.conf_tier.tier === "HIGH" && "border-up/30 bg-up/10 text-up",
                  r.conf_tier.tier === "MEDIUM" && "border-gold/30 bg-gold/10 text-gold",
                  r.conf_tier.tier === "LOW" && "border-down/30 bg-down/10 text-down",
                )}
              >
                {r.conf_tier.tier} confidence · {r.confidence.toFixed(0)}%
              </span>
              {r.predicted_price ? (
                <span className="font-mono text-sm text-muted-foreground">
                  next candle ≈ ₹{formatNumber(r.predicted_price)}
                </span>
              ) : null}
            </div>

            <ProbGauge upProb={r.up_prob} />

            {/* Horizons */}
            <div className="grid grid-cols-3 gap-2">
              {Object.entries(r.horizon).map(([h, p]) => (
                <div
                  key={h}
                  className="flex items-center justify-between rounded-lg bg-muted/60 px-3 py-2"
                >
                  <span className="text-xs text-muted-foreground">{h}d</span>
                  <span
                    className={cn(
                      "font-mono text-sm font-semibold",
                      p.direction === "up" ? "text-up" : "text-down",
                    )}
                  >
                    {p.prob.toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1">
                walk-forward {r.walk_fwd_acc.toFixed(1)}%
                <InfoTip label="What is walk-forward accuracy?">
                  The model is tested on time periods it never saw during
                  training, five times over. This is its honest hit-rate —
                  50% would be coin-flip level.
                </InfoTip>
              </span>
              <span>train {r.n_train}</span>
              <span>test {r.n_test}</span>
            </div>
          </CardContent>
        </Card>

        {/* Right rail: models + LSTM + features */}
        <div className="flex flex-col gap-4">
          {/* Model accuracies */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">
                Model accuracy
                <span className="ml-1.5 font-mono text-xs font-normal text-muted-foreground">
                  holdout %
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-1.5">
              {Object.entries(r.model_accs).map(([name, acc]) => (
                <span
                  key={name}
                  className={cn(
                    "rounded-md border px-2 py-1 font-mono text-xs",
                    acc >= 55
                      ? "border-up/30 bg-up/10 text-up"
                      : acc >= 50
                        ? "border-border bg-muted text-muted-foreground"
                        : "border-down/30 bg-down/10 text-down",
                  )}
                >
                  {name} {acc.toFixed(1)}
                </span>
              ))}
            </CardContent>
          </Card>

          {/* LSTM price forecast (from plan/lstm.py) */}
          {lstm.data?.available ? (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-1.5 text-sm">
                  Tomorrow&apos;s price — LSTM
                  <InfoTip label="What is this LSTM forecast?">
                    A neural network that reads the last 60 daily closes and
                    predicts the next day&apos;s closing price in ₹. It learns
                    price patterns only — treat it as one opinion, not a
                    promise.
                  </InfoTip>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex items-baseline gap-3">
                <span
                  className={cn(
                    "font-mono text-xl font-semibold",
                    (lstm.data.expected_change_pct ?? 0) >= 0 ? "text-up" : "text-down",
                  )}
                >
                  ₹{formatNumber(lstm.data.predicted_close ?? 0)}
                </span>
                <span
                  className={cn(
                    "font-mono text-xs",
                    (lstm.data.expected_change_pct ?? 0) >= 0 ? "text-up" : "text-down",
                  )}
                >
                  {(lstm.data.expected_change_pct ?? 0) >= 0 ? "+" : ""}
                  {lstm.data.expected_change_pct?.toFixed(2)}% vs today
                </span>
              </CardContent>
            </Card>
          ) : null}

          {/* Top features */}
          {r.top_features.length > 0 ? (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-1.5 text-sm">
                  What the models look at
                  <InfoTip label="What does this mean?">
                    The inputs that most influenced the prediction — recent
                    momentum, RSI zone, MACD distance and so on.
                  </InfoTip>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-1.5">
                {r.top_features.map((f) => (
                  <div key={f.feature} className="flex items-center gap-2">
                    <span className="w-24 shrink-0 font-mono text-[11px] text-muted-foreground">
                      {f.feature}
                    </span>
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-ai/70"
                        style={{
                          width: `${Math.min(100, f.importance * 400)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}
        </div>
      </div>

      <p className="text-[11px] text-muted-foreground/60">
        Model estimates, not investment advice — trained on historical prices only.
      </p>
    </div>
  );
}
