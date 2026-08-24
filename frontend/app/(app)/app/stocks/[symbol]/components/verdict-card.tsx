"use client";

import { BarChart3, Brain, Newspaper, Shield } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { VerdictBadge } from "@/components/signals/verdict-badge";
import { InfoTip } from "@/components/info-tip";
import { useFusion } from "@/lib/hooks/use-analytics";
import type { Timeframe } from "../constants";
import { cn } from "@/lib/utils";

function BlendBar({
  label,
  icon,
  score,
  weight,
  available = true,
  tooltip,
}: {
  label: string;
  icon: React.ReactNode;
  score: number;
  weight: number;
  available?: boolean;
  tooltip: string;
}) {
  const pct = Math.round(((score + 1) / 2) * 100);
  const barLeft = Math.min(pct, 50);
  const barWidth = Math.abs(pct - 50);
  const color =
    score > 0.05 ? "bg-up" : score < -0.05 ? "bg-down" : "bg-gold";
  const sign = score > 0 ? "+" : "";

  return (
    <div className={cn("space-y-1", !available && "opacity-40")}>
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
          {icon}
          {label}
          <span className="font-mono text-[10px] text-muted-foreground/60">
            {Math.round(weight * 100)}%
          </span>
          <InfoTip side="top">{tooltip}</InfoTip>
        </span>
        <span className="font-mono text-xs font-semibold tabular-nums text-muted-foreground">
          {sign}
          {score.toFixed(2)}
        </span>
      </div>
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <span
          className="absolute left-1/2 top-0 h-full w-px bg-border"
          aria-hidden
        />
        <span
          className={cn(
            "absolute top-0 h-full rounded-full",
            color,
          )}
          style={{ left: `${barLeft}%`, width: `${barWidth}%` }}
        />
      </div>
    </div>
  );
}

function ConfidenceBadge({
  tier,
  tone,
}: {
  tier: string;
  tone: string;
}) {
  const color =
    tier === "HIGH"
      ? "bg-up/10 text-up border-up/20"
      : tier === "MEDIUM"
        ? "bg-gold/10 text-gold border-gold/20"
        : "bg-muted text-muted-foreground border-border";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-mono text-[10px] font-semibold uppercase tracking-wider",
        color,
      )}
      title={tone}
    >
      <Shield className="size-3" />
      {tier}
    </span>
  );
}

/** Fused verdict card — technical + ML + news blend. */
export function VerdictCard({
  symbol,
  timeframe,
}: {
  symbol: string;
  timeframe: Timeframe;
}) {
  const fusion = useFusion(symbol, timeframe.interval, timeframe.period);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <BarChart3 className="size-4 text-ai" /> Fusion verdict
          </span>
          {fusion.data && (
            <ConfidenceBadge
              tier={fusion.data.confidence_tier}
              tone={fusion.data.confidence_tone}
            />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5">
        {fusion.isLoading ? (
          <>
            <Skeleton className="h-7 w-28 rounded-full" />
            <Skeleton className="h-2 w-full rounded-full" />
            <Skeleton className="h-16 w-full rounded-lg" />
            <Skeleton className="h-16 w-full rounded-lg" />
          </>
        ) : fusion.isError || !fusion.data ? (
          <p className="py-4 text-center text-sm text-muted-foreground">
            Verdict unavailable right now.
          </p>
        ) : (
          <>
            {/* ── Verdict + gauge ── */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <VerdictBadge verdict={fusion.data.final_label} size="lg" />
                <span className="font-mono text-lg font-bold tabular-nums text-muted-foreground">
                  {fusion.data.fused_score > 0 ? "+" : ""}
                  {fusion.data.fused_score.toFixed(2)}
                </span>
              </div>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {fusion.data.final_desc}
              </p>
            </div>

            {/* ── 3-layer blend ── */}
            <div className="space-y-3">
              <div className="flex items-center gap-1.5">
                <span className="font-mono text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Layer weights
                </span>
                <InfoTip side="right">
                  Technical rules contribute 45%, the ML ensemble 40%, and news
                  sentiment 15% to the fused verdict. If a layer is missing, the
                  remaining layers are re-weighted proportionally.
                </InfoTip>
              </div>

              <BlendBar
                label="Technical"
                icon={<BarChart3 className="size-3" />}
                score={fusion.data.layers.technical.score}
                weight={fusion.data.layers.technical.weight}
                tooltip="10 indicator rules (RSI, MACD, SMA cross, Bollinger, volume, momentum) blended into a single -1…+1 score."
              />

              <BlendBar
                label="ML ensemble"
                icon={<Brain className="size-3" />}
                score={fusion.data.layers.ml.score}
                weight={fusion.data.layers.ml.weight}
                available={fusion.data.layers.ml.available}
                tooltip={
                  fusion.data.layers.ml.available
                    ? `XGBoost + LightGBM + CatBoost vote. ${fusion.data.layers.ml.active_models}. Walk-forward accuracy: ${fusion.data.layers.ml.walk_fwd_acc}%`
                    : "ML prediction unavailable — not enough training data."
                }
              />

              <BlendBar
                label="News NLP"
                icon={<Newspaper className="size-3" />}
                score={fusion.data.layers.news.score}
                weight={fusion.data.layers.news.weight}
                available={fusion.data.layers.news.available}
                tooltip={
                  fusion.data.layers.news.available
                    ? `${fusion.data.layers.news.detail.length} headlines scored (FinBERT + keyword blend).`
                    : "No recent headlines fetched — technical analysis only."
                }
              />
            </div>

            {/* ── What's missing ── */}
            {fusion.data.missing.length > 0 && (
              <div className="rounded-lg border border-dashed border-border bg-muted/40 px-3 py-2">
                {fusion.data.missing.map((msg) => (
                  <p
                    key={msg}
                    className="text-[11px] leading-relaxed text-muted-foreground"
                  >
                    {msg}
                  </p>
                ))}
              </div>
            )}

            {/* ── Technical signals (top 6) ── */}
            {fusion.data.layers.technical.signals.length > 0 && (
              <div className="space-y-1.5">
                <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Active rules
                </p>
                {fusion.data.layers.technical.signals.slice(0, 6).map((sig) => (
                  <div
                    key={sig.rule}
                    className="flex items-center gap-2 text-xs text-muted-foreground"
                  >
                    <span
                      aria-hidden
                      className={cn(
                        "size-1.5 shrink-0 rounded-full",
                        sig.kind === "buy"
                          ? "bg-up"
                          : sig.kind === "sell"
                            ? "bg-down"
                            : "bg-muted-foreground",
                      )}
                    />
                    <span>{sig.rule}</span>
                  </div>
                ))}
              </div>
            )}

            {/* ── Reasons ── */}
            {fusion.data.layers.technical.reasons.length > 0 && (
              <div
                className="space-y-1 rounded-lg bg-muted/60 p-3"
                aria-label="Why this verdict"
              >
                <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
                  Why
                </p>
                {fusion.data.layers.technical.reasons.map((reason) => (
                  <p key={reason} className="text-xs leading-relaxed">
                    {reason}
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
