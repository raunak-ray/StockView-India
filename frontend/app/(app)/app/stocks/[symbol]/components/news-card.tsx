"use client";

import { Newspaper } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { useSentimentScore } from "@/lib/hooks/use-sentiment";
import type { Interval, Period } from "@/lib/api/market";
import { cn } from "@/lib/utils";

import type { Timeframe } from "../constants";

type Tone = "up" | "down" | "flat";

function toneOf(label: string): Tone {
  const l = label.toUpperCase();
  if (l === "BULLISH" || l === "POSITIVE") return "up";
  if (l === "BEARISH" || l === "NEGATIVE") return "down";
  return "flat";
}

const toneText: Record<Tone, string> = {
  up: "text-up",
  down: "text-down",
  flat: "text-muted-foreground",
};

/** Meter from −1 … +1 with a centre notch; marker sits at the score. */
function MoodMeter({ score, tone }: { score: number; tone: Tone }) {
  const pos = ((Math.max(-1, Math.min(1, score)) + 1) / 2) * 100;
  return (
    <div className="relative h-2 w-full rounded-full bg-gradient-to-r from-down/50 via-muted to-up/50">
      <span aria-hidden className="absolute top-0 left-1/2 h-full w-px bg-border" />
      <span
        className={cn(
          "absolute top-1/2 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background shadow",
          tone === "up" && "bg-up",
          tone === "down" && "bg-down",
          tone === "flat" && "bg-muted-foreground",
        )}
        style={{ left: `${pos}%` }}
      />
    </div>
  );
}

function MoodCard({
  title,
  score,
  label,
  tip,
  footer,
}: {
  title: string;
  score: number;
  label: string;
  tip: string;
  footer?: React.ReactNode;
}) {
  const tone = toneOf(label);
  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          {title}
          <InfoTip label={`What is ${title}?`}>{tip}</InfoTip>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline justify-between">
          <span className={cn("font-mono text-xl font-semibold", toneText[tone])}>
            {label}
          </span>
          <span className="font-mono text-xs text-muted-foreground">
            {score >= 0 ? "+" : ""}
            {score.toFixed(2)}
          </span>
        </div>
        <MoodMeter score={score} tone={tone} />
        {footer}
      </CardContent>
    </Card>
  );
}

/** News & mood — headlines with tone badges plus news/technical mood meters. */
export function NewsCard({
  symbol,
  timeframe,
}: {
  symbol: string;
  timeframe: Timeframe;
}) {
  const { data, isLoading, isError } = useSentimentScore(
    symbol,
    timeframe.interval as Interval,
    timeframe.period as Period,
  );

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-3 py-14 text-muted-foreground">
          <Loader variant="dots" size={24} label="Loading news and mood" />
          <p className="text-sm">Loading news &amp; mood…</p>
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className="border-dashed">
        <CardContent className="py-10 text-center text-sm text-muted-foreground">
          News &amp; mood unavailable right now — check back shortly.
        </CardContent>
      </Card>
    );
  }

  const headlines = data?.news.detail ?? [];
  const topSignals = (data?.technical.signals ?? [])
    .filter((s) => s.tone !== "NEUTRAL")
    .slice(0, 3);

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      {/* Mood meters */}
      <div className="flex flex-col gap-4">
        <MoodCard
          title="News mood"
          score={data?.news.score ?? 0}
          label={data?.news.label ?? "NEUTRAL"}
          tip="Average tone of today's headlines about this stock, from −1 (very negative) to +1 (very positive). Scored by a financial language model when available, otherwise by keyword analysis."
        />
        <MoodCard
          title="Chart mood"
          score={data?.technical.score ?? 0}
          label={data?.technical.label ?? "NEUTRAL"}
          tip="What the chart itself implies: ten indicator checks (RSI, MACD, moving averages, volume, momentum…) averaged into one opinion from −1 to +1."
          footer={
            topSignals.length > 0 ? (
              <ul className="space-y-1.5">
                {topSignals.map((s) => (
                  <li
                    key={s.name + s.message}
                    className="flex items-center gap-2 text-xs text-muted-foreground"
                  >
                    <span
                      className={cn(
                        "size-1.5 shrink-0 rounded-full",
                        toneOf(s.tone) === "up" && "bg-up",
                        toneOf(s.tone) === "down" && "bg-down",
                        toneOf(s.tone) === "flat" && "bg-muted-foreground",
                      )}
                    />
                    <span className="truncate">{s.message}</span>
                  </li>
                ))}
              </ul>
            ) : null
          }
        />
      </div>

      {/* Headlines */}
      <Card className="h-fit">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-1.5 text-sm">
            <Newspaper className="size-4 text-muted-foreground" />
            Latest headlines
            <span className="ml-1 font-mono text-xs font-normal text-muted-foreground">
              {headlines.length}
            </span>
            <InfoTip label="How are headlines scored?">
              Each headline gets a tone badge from its sentiment score. Green
              suggests positive news, red negative, grey neutral. Tone can move
              prices, so it feeds the overall news mood.
            </InfoTip>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {headlines.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              No recent headlines found for {symbol.replace(/\.(NS|BO)$/, "")}.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {headlines.map((h, i) => {
                const tone = toneOf(h.label);
                return (
                  <li
                    key={`${i}-${h.headline.slice(0, 24)}`}
                    className="flex items-start gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
                  >
                    <span
                      className={cn(
                        "mt-0.5 inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase",
                        tone === "up" && "border-up/30 bg-up/10 text-up",
                        tone === "down" && "border-down/30 bg-down/10 text-down",
                        tone === "flat" &&
                          "border-border bg-muted text-muted-foreground",
                      )}
                    >
                      {tone === "up" ? "+" : tone === "down" ? "−" : "="}
                      {Math.round(Math.abs(h.score) * 100)}
                    </span>
                    <span className="text-sm leading-relaxed">{h.headline}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
