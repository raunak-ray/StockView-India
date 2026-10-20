"use client";

import { History, Newspaper, Radio } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { useSentimentInsight } from "@/lib/hooks/use-sentiment";
import type { Interval, Period } from "@/lib/api/market";
import type {
  SentimentPeriodCard,
  StoredArticle,
} from "@/lib/api/sentiment";
import { formatDate, formatPct, toneBadgeClass } from "@/lib/utils/format";
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

/** The period cards, in the order the UI shows them. */
const PERIOD_ORDER = ["1m", "3m", "1y", "3y"] as const;

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

/** One period card — how the news read over 1M / 3M / 1Y / 3Y. */
function PeriodCard({ card }: { card: SentimentPeriodCard }) {
  const tone = toneOf(card.label);
  const changed = card.sentiment_change ?? null;

  if (!card.available) {
    return (
      <div className="rounded-lg border border-dashed border-border p-3">
        <p className="text-xs font-medium text-muted-foreground">{card.title}</p>
        <p className="mt-1 text-xs text-muted-foreground">
          No stored articles in this window
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-muted/30 p-3">
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium">{card.title}</span>
        <span className="font-mono text-[10px] text-muted-foreground">
          {card.article_count} stories
        </span>
      </div>
      <div className="mt-1.5 flex items-baseline justify-between">
        <span className={cn("font-mono text-sm font-semibold", toneText[tone])}>
          {card.label}
        </span>
        <span className="font-mono text-xs text-muted-foreground">
          {card.score !== null && `${card.score >= 0 ? "+" : ""}${card.score.toFixed(2)}`}
        </span>
      </div>
      <div className="mt-2 flex items-center justify-between text-[11px] text-muted-foreground">
        <span>News {formatPct(changed)}</span>
        <span>Price {formatPct(card.price_change_pct)}</span>
      </div>
    </div>
  );
}

/** The four period cards side by side. */
function PeriodStrip({
  periods,
}: {
  periods: Record<string, SentimentPeriodCard>;
}) {
  return (
    <Card className="h-fit">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          <History className="size-4 text-muted-foreground" />
          News over time
          <InfoTip label="How is this window read?">
            Each card averages every stored article published inside that window.
            “News” is the change in average tone across the window; “Price” is
            the share price change over the same days.
          </InfoTip>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {PERIOD_ORDER.map((key) =>
          periods[key] ? (
            <PeriodCard key={key} card={periods[key]} />
          ) : null,
        )}
      </CardContent>
    </Card>
  );
}

/** A stored story: title, where it came from, when, and how it scored. */
function StoryRow({ article }: { article: StoredArticle }) {
  const tone = toneOf(article.label);
  const body = (
    <div className="flex items-start gap-3 py-2.5">
      <span
        className={cn(
          "mt-0.5 inline-flex shrink-0 items-center rounded-full border px-2 py-0.5 font-mono text-[10px] font-semibold uppercase",
          toneBadgeClass[tone],
        )}
      >
        {tone === "up" ? "+" : tone === "down" ? "−" : "="}
        {Math.round(Math.abs(article.score) * 100)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm leading-relaxed">{article.title}</span>
        <span className="mt-0.5 block font-mono text-[11px] text-muted-foreground">
          {[article.source, formatDate(article.published_at)]
            .filter(Boolean)
            .join(" · ")}
        </span>
      </span>
    </div>
  );

  if (!article.url) return body;
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block transition-colors hover:bg-muted/40"
    >
      {body}
    </a>
  );
}

/** The strongest positive and negative stories of the stored archive. */
function ExtremesCard({
  positive,
  negative,
}: {
  positive: StoredArticle[];
  negative: StoredArticle[];
}) {
  const stories = [...positive, ...negative];
  if (stories.length === 0) return null;

  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          Biggest stories
          <span className="ml-1 font-mono text-xs font-normal text-muted-foreground">
            {stories.length}
          </span>
          <InfoTip label="What are these?">
            The most positive and the most negative stories we have scored for
            this stock — the ones that moved the tone the furthest.
          </InfoTip>
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <ul className="divide-y divide-border">
          {stories.map((article, i) => (
            <li key={`${article.id ?? "ext"}-${i}`} className="px-4">
              <StoryRow article={article} />
            </li>
          ))}
        </ul>
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
  const { data, isLoading, isError } = useSentimentInsight(
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

  const isStored = data?.isStoredData ?? false;
  const headlines = data?.news.detail ?? [];
  const topSignals = (data?.technical.signals ?? [])
    .filter((s) => s.tone !== "NEUTRAL")
    .slice(0, 3);
  const articles = data?.top_articles ?? [];
  const coverage = data?.news;

  return (
    <div className="grid gap-4 lg:grid-cols-[300px_1fr]">
      {/* Mood meters */}
      <div className="flex flex-col gap-4">
        <MoodCard
          title="News mood"
          score={data?.news.score ?? 0}
          label={data?.news.label ?? "NEUTRAL"}
          tip="Average tone of the news about this stock, from −1 (very negative) to +1 (very positive). Scored by a financial language model."
          footer={
            <div className="space-y-1 text-xs text-muted-foreground">
              <p>
                {isStored
                  ? `From our archive: ${coverage?.article_count ?? 0} scored articles.`
                  : "Live headlines — this stock is not in our archive yet."}
              </p>
              {isStored && coverage?.window?.start && (
                <p className="font-mono">
                  {formatDate(coverage.window.start)} –{" "}
                  {formatDate(coverage.window.end)}
                </p>
              )}
            </div>
          }
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

      {/* Right column */}
      <div className="space-y-4">
        {isStored && (
          <>
            <PeriodStrip periods={data?.periods ?? {}} />
            <ExtremesCard
              positive={data?.top_positive ?? []}
              negative={data?.top_negative ?? []}
            />
          </>
        )}

        <Card className="h-fit">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-1.5 text-sm">
              {isStored ? (
                <Newspaper className="size-4 text-muted-foreground" />
              ) : (
                <Radio className="size-4 text-muted-foreground" />
              )}
              {isStored ? "Latest headlines" : "Live headlines"}
              <span className="ml-1 font-mono text-xs font-normal text-muted-foreground">
                {isStored ? articles.length : headlines.length}
              </span>
              <InfoTip label="How are headlines scored?">
                Each headline gets a tone badge from its sentiment score. Green
                suggests positive news, red negative, grey neutral. Tone can move
                prices, so it feeds the overall news mood.
              </InfoTip>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {isStored ? (
              articles.length === 0 ? (
                <p className="py-10 text-center text-sm text-muted-foreground">
                  No stored articles found for {symbol.replace(/\.(NS|BO)$/, "")}.
                </p>
              ) : (
                <ul className="divide-y divide-border">
                  {articles.map((article, i) => (
                    <li key={`${article.id ?? "a"}-${i}`} className="px-4">
                      <StoryRow article={article} />
                    </li>
                  ))}
                </ul>
              )
            ) : headlines.length === 0 ? (
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
                          toneBadgeClass[tone],
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

        {isStored && coverage && coverage.article_count > 0 && (
          <p className="px-1 text-[11px] text-muted-foreground">
            Scored with {data?.model_version ?? "our sentiment model"} · archive
            last updated {formatDate(data?.updated_at)}
          </p>
        )}
        {!isStored && (
          <p className="px-1 text-[11px] text-muted-foreground">
            These headlines were fetched live just now. Once we archive this
            stock, the card will show its full history instead.
          </p>
        )}
      </div>
    </div>
  );
}
