"use client";

import { useState } from "react";
import { CandlestickChart, LineChart, RefreshCw } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PriceChart, type SRLevel } from "@/components/charts/price-chart";
import { useHistory } from "@/lib/hooks/use-market";
import {
  useIndicators,
  useSignal,
  useSupportResistance,
} from "@/lib/hooks/use-analytics";
import { ApiError } from "@/lib/api/client";
import { TIMEFRAMES, type Timeframe } from "../constants";
import { cn } from "@/lib/utils";

function Toggle({
  active,
  onClick,
  children,
  label,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "rounded-md px-2.5 py-1 font-mono text-xs transition-colors",
        active
          ? "bg-secondary text-secondary-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

export function ChartSection({
  symbol,
  timeframe,
  onTimeframeChange,
}: {
  symbol: string;
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
}) {
  const [style, setStyle] = useState<"candles" | "line">("candles");
  // Panel defaults follow the Streamlit sidebar (app.py:991-1000, 1017).
  const [showSma20, setShowSma20] = useState(true);
  const [showSma50, setShowSma50] = useState(true);
  const [showBB, setShowBB] = useState(false);
  const [showRsi, setShowRsi] = useState(true);
  const [showMacd, setShowMacd] = useState(false);
  const [showSR, setShowSR] = useState(true);
  const [showMarkers, setShowMarkers] = useState(true);

  const history = useHistory(symbol, timeframe.interval, timeframe.period);
  const indicators = useIndicators(symbol, timeframe.interval, timeframe.period);
  const sr = useSupportResistance(symbol, timeframe.interval, timeframe.period);
  const signal = useSignal(symbol, timeframe.interval, timeframe.period);

  const notFound =
    history.error instanceof ApiError && history.error.status === 404;

  const srLevels: SRLevel[] = showSR
    ? [
        ...(sr.data?.supports ?? []).map((price) => ({
          price,
          kind: "support" as const,
        })),
        ...(sr.data?.resistances ?? []).map((price) => ({
          price,
          kind: "resistance" as const,
        })),
      ]
    : [];

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <CardTitle className="text-sm">Price chart</CardTitle>
        <div className="flex flex-wrap items-center gap-2">
          {/* Timeframe presets */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            {TIMEFRAMES.map((tf) => (
              <Toggle
                key={tf.label}
                label={`${tf.label} timeframe`}
                active={timeframe.label === tf.label}
                onClick={() => onTimeframeChange(tf)}
              >
                {tf.label}
              </Toggle>
            ))}
          </div>
          {/* Chart style */}
          <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
            <Toggle
              label="Candlestick chart"
              active={style === "candles"}
              onClick={() => setStyle("candles")}
            >
              <CandlestickChart className="size-3.5" />
            </Toggle>
            <Toggle
              label="Line chart"
              active={style === "line"}
              onClick={() => setStyle("line")}
            >
              <LineChart className="size-3.5" />
            </Toggle>
          </div>
          {/* Overlays */}
          <div className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-card p-1">
            <Toggle
              label="Toggle SMA 20 overlay"
              active={showSma20}
              onClick={() => setShowSma20((v) => !v)}
            >
              SMA 20
            </Toggle>
            <Toggle
              label="Toggle SMA 50 overlay"
              active={showSma50}
              onClick={() => setShowSma50((v) => !v)}
            >
              SMA 50
            </Toggle>
            <Toggle
              label="Toggle Bollinger Bands overlay"
              active={showBB}
              onClick={() => setShowBB((v) => !v)}
            >
              BB
            </Toggle>
          </div>
          {/* Panels */}
          <div className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-card p-1">
            <Toggle
              label="Toggle RSI panel"
              active={showRsi}
              onClick={() => setShowRsi((v) => !v)}
            >
              RSI
            </Toggle>
            <Toggle
              label="Toggle MACD panel"
              active={showMacd}
              onClick={() => setShowMacd((v) => !v)}
            >
              MACD
            </Toggle>
            <Toggle
              label="Toggle support and resistance lines"
              active={showSR}
              onClick={() => setShowSR((v) => !v)}
            >
              S/R
            </Toggle>
            <Toggle
              label="Toggle buy sell markers"
              active={showMarkers}
              onClick={() => setShowMarkers((v) => !v)}
            >
              Signals
            </Toggle>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {history.isLoading ? (
          <Skeleton className="h-[420px] w-full rounded-lg" />
        ) : history.isError ? (
          <div className="flex h-[420px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-border">
            <p className="text-sm text-muted-foreground">
              {notFound
                ? `No chart data available for ${symbol}.`
                : "Could not load chart data right now."}
            </p>
            {!notFound && (
              <Button variant="outline" size="sm" onClick={() => history.refetch()}>
                <RefreshCw className="size-4" /> Retry
              </Button>
            )}
          </div>
        ) : !history.data || history.data.candles.length === 0 ? (
          <div className="flex h-[420px] items-center justify-center rounded-lg border border-dashed border-border">
            <p className="text-sm text-muted-foreground">No data in range.</p>
          </div>
        ) : (
          <>
            <PriceChart
              candles={history.data.candles}
              indicators={indicators.data}
              markers={signal.data?.markers ?? []}
              srLevels={srLevels}
              chartStyle={style}
              showVolume
              showSma20={showSma20}
              showSma50={showSma50}
              showBB={showBB}
              showRsi={showRsi}
              showMacd={showMacd}
            />
            <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[11px] text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="h-0.5 w-4 bg-gold" /> SMA 20
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-0.5 w-4 bg-info" /> SMA 50
              </span>
              {showBB && (
                <span className="flex items-center gap-1.5">
                  <span className="h-0.5 w-4 bg-ai" /> Bollinger
                </span>
              )}
              {srLevels.length > 0 && (
                <>
                  <span className="flex items-center gap-1.5">
                    <span className="h-0 w-4 border-t-2 border-dashed border-up" />
                    Support
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="h-0 w-4 border-t-2 border-dashed border-down" />
                    Resistance
                  </span>
                </>
              )}
              <span>{history.data.count} bars</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
