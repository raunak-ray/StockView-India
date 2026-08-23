"use client";

import Link from "next/link";
import { useState } from "react";
import {
  ArrowLeft,
  ArrowDownRight,
  ArrowUpRight,
  RefreshCw,
} from "lucide-react";
import { motion } from "motion/react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { MarketStatusChip } from "@/components/market/market-status-chip";
import { useQuote, useStockInfo } from "@/lib/hooks/use-market";
import { ApiError } from "@/lib/api/client";
import {
  formatCompact,
  formatINR,
  formatNumber,
  formatPct,
  formatSigned,
  toneBadgeClass,
  toneTextClass,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils";

import {
  DEFAULT_REFRESH_INTERVAL,
  DEFAULT_TIMEFRAME,
  REFRESH_INTERVALS,
  type RefreshInterval,
  type Timeframe,
} from "../constants";
import { useDocumentTitle } from "../hooks/use-document-title";
import { AiCard } from "./ai-card";
import { ChartSection } from "./chart-section";
import { NewsCard } from "./news-card";
import { VerdictCard } from "./verdict-card";
import { WatchlistStar } from "./watchlist-star";

function exchangeOf(symbol: string): string {
  if (symbol.startsWith("^")) return "INDEX";
  if (symbol.endsWith(".BO")) return "BSE";
  return "NSE";
}

function infoNumber(info: Record<string, unknown>, key: string): number | null {
  const v = info[key];
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

function infoString(info: Record<string, unknown>, key: string): string | null {
  const v = info[key];
  return typeof v === "string" && v.length > 0 ? v : null;
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-muted/60 px-3 py-2">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="font-mono text-sm font-medium">{value}</span>
    </div>
  );
}

export function QuoteView({ symbol }: { symbol: string }) {
  const [intervalSec, setIntervalSec] =
    useState<RefreshInterval>(DEFAULT_REFRESH_INTERVAL);
  const [timeframe, setTimeframe] = useState<Timeframe>(DEFAULT_TIMEFRAME);
  const quote = useQuote(symbol, intervalSec);
  const info = useStockInfo(symbol);

  useDocumentTitle(symbol);

  const meta = info.data?.info ?? {};
  const name =
    infoString(meta, "longName") ??
    infoString(meta, "shortName") ??
    symbol.replace(/\.(NS|BO)$/, "");
  const changePct = quote.data?.change_pct ?? null;
  const up = (changePct ?? 0) >= 0;
  const notFound = quote.error instanceof ApiError && quote.error.status === 404;

  if (notFound) {
    return (
      <div className="mx-auto flex max-w-6xl flex-col gap-4">
        <BackLink />
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <p className="text-sm font-medium">
              We couldn&apos;t find “{symbol}”
            </p>
            <p className="text-sm text-muted-foreground">
              Check the ticker and try the search bar again.
            </p>
            <Button asChild variant="outline" size="sm" className="mt-2">
              <Link href="/app">Back to dashboard</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <BackLink />

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: "easeOut" }}
        className="flex flex-wrap items-end justify-between gap-4"
      >
        <div>
          <h1 className="text-xl font-semibold">{name}</h1>
          <div className="mt-1 flex items-center gap-2">
            <span className="font-mono text-sm text-muted-foreground">
              {symbol}
            </span>
            <Badge variant="secondary" className="font-mono text-[11px]">
              {exchangeOf(symbol)}
            </Badge>
            <MarketStatusChip />
          </div>
          <div className="mt-4 flex flex-wrap items-baseline gap-3">
            {quote.isLoading ? (
              <Skeleton className="h-9 w-40" />
            ) : (
              <span
                className={cn(
                  "font-mono text-3xl font-semibold",
                  !quote.isFetching && toneTextClass[up ? "up" : "down"],
                )}
              >
                {quote.data ? `₹${formatNumber(quote.data.price)}` : "—"}
              </span>
            )}
            {changePct !== null && (
              <span
                className={cn(
                  "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 font-mono text-sm font-semibold",
                  toneBadgeClass[up ? "up" : "down"],
                )}
              >
                {up ? (
                  <ArrowUpRight className="size-4" />
                ) : (
                  <ArrowDownRight className="size-4" />
                )}
                {formatPct(changePct)}
                <span className="opacity-70">
                  ({formatSigned(quote.data?.change)})
                </span>
              </span>
            )}
            {quote.isFetching && !quote.isLoading && (
              <RefreshCw className="size-3.5 animate-spin text-muted-foreground" />
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <WatchlistStar ticker={symbol} />
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            {REFRESH_INTERVALS.map((sec) => (
            <button
              key={sec}
              type="button"
              onClick={() => setIntervalSec(sec)}
              aria-label={`Refresh every ${sec} seconds`}
              aria-pressed={intervalSec === sec}
              className={cn(
                "rounded-md px-2.5 py-1 font-mono text-xs transition-colors",
                intervalSec === sec
                  ? "bg-secondary text-secondary-foreground"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {sec}s
            </button>
          ))}
        </div>
        </div>
      </motion.div>

      <ChartSection
        symbol={symbol}
        timeframe={timeframe}
        onTimeframeChange={setTimeframe}
      />

      {/* Key stats + verdict rail */}
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm">Today</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {info.isLoading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-10 rounded-lg" />
              ))
            ) : (
              <>
                <Stat
                  label="Open"
                  value={
                    infoNumber(meta, "open") !== null
                      ? formatINR(infoNumber(meta, "open"))
                      : quote.data
                        ? formatINR(quote.data.price)
                        : "—"
                  }
                />
                <Stat
                  label="Prev close"
                  value={formatINR(
                    quote.data?.previous_close ?? infoNumber(meta, "previousClose"),
                  )}
                />
                <Stat
                  label="Day high"
                  value={formatINR(infoNumber(meta, "dayHigh"))}
                />
                <Stat
                  label="Day low"
                  value={formatINR(infoNumber(meta, "dayLow"))}
                />
                <Stat
                  label="Volume"
                  value={formatCompact(infoNumber(meta, "volume"))}
                />
                <Stat
                  label="Avg volume (10D)"
                  value={formatCompact(infoNumber(meta, "averageVolume10Day"))}
                />
              </>
            )}
          </CardContent>
        </Card>

        <div className="flex flex-col gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm">52-week range</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {info.isLoading ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <>
                  <div className="flex items-center justify-between font-mono text-sm">
                    <span className="text-down">
                      {formatINR(infoNumber(meta, "fiftyTwoWeekLow"))}
                    </span>
                    <span className="text-up">
                      {formatINR(infoNumber(meta, "fiftyTwoWeekHigh"))}
                    </span>
                  </div>
                  <RangeBar
                    low={infoNumber(meta, "fiftyTwoWeekLow")}
                    high={infoNumber(meta, "fiftyTwoWeekHigh")}
                    current={quote.data?.price ?? null}
                  />
                  <Stat
                    label="Market cap"
                    value={
                      infoNumber(meta, "marketCap") !== null
                        ? `${formatCompact(infoNumber(meta, "marketCap"))}`
                        : "—"
                    }
                  />
                </>
              )}
            </CardContent>
          </Card>

          <VerdictCard symbol={symbol} timeframe={timeframe} />
        </div>
      </div>

      {/* News + mood */}
      <NewsCard symbol={symbol} timeframe={timeframe} />

      {/* AI prediction */}
      <AiCard symbol={symbol} timeframe={timeframe} />
    </div>
  );
}

function RangeBar({
  low,
  high,
  current,
}: {
  low: number | null;
  high: number | null;
  current: number | null;
}) {
  if (low === null || high === null || current === null || high <= low) {
    return <Skeleton className="h-1.5 w-full rounded-full" />;
  }
  const pos = Math.min(100, Math.max(0, ((current - low) / (high - low)) * 100));
  return (
    <div className="relative h-1.5 w-full rounded-full bg-gradient-to-r from-down/60 via-gold/60 to-up/60">
      <span
        className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background bg-foreground shadow"
        style={{ left: `${pos}%` }}
        title={formatINR(current)}
      />
    </div>
  );
}

function BackLink() {
  return (
    <Link
      href="/app"
      className="inline-flex w-fit items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
    >
      <ArrowLeft className="size-4" /> Dashboard
    </Link>
  );
}
