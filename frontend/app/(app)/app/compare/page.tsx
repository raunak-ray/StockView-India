"use client";

import { useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CircleHelp,
  Loader2,
  Plus,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { InfoTip } from "@/components/info-tip";
import { StockPickerModal } from "@/components/stock-picker-modal";
import { useCompare } from "@/lib/hooks/use-compare";
import type { SymbolSnapshot } from "@/lib/api/compare";
import { cn } from "@/lib/utils";

const COLORS = ["#34d399", "#ef4444", "#3b82f6", "#eab308"];

function fmt(n: number | null, opts?: Intl.NumberFormatOptions): string {
  if (n == null) return "—";
  return n.toLocaleString("en-IN", opts);
}

function fmtCap(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1e12) return `₹${(n / 1e12).toFixed(1)}T`;
  if (n >= 1e9) return `₹${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(1)}Cr`;
  return `₹${n.toLocaleString("en-IN")}`;
}

function rsiLabel(rsi: number | null): string {
  if (rsi == null) return "—";
  if (rsi > 70) return "Overbought";
  if (rsi < 30) return "Oversold";
  return "Neutral";
}

/* ── Empty slot card ──────────────────────────────────────────────────── */

function EmptySlot({
  onClick,
  index,
}: {
  onClick: () => void;
  index: number;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "group flex min-h-[240px] flex-col items-center justify-center gap-4 rounded-2xl border-2 border-dashed border-border p-6 transition-all",
        "hover:border-emerald-500/50 hover:bg-emerald-500/5",
      )}
    >
      <div className="rounded-full bg-muted p-4 transition-colors group-hover:bg-emerald-500/10">
        <Plus className="size-6 text-muted-foreground transition-colors group-hover:text-emerald-500" />
      </div>
      <div className="text-center">
        <p className="text-sm font-medium text-muted-foreground group-hover:text-foreground">
          Select a stock to compare
        </p>
        <p className="mt-1 text-xs text-muted-foreground">
          Slot {index + 1} of 4
        </p>
      </div>
    </button>
  );
}

/* ── Filled snapshot card ──────────────────────────────────────────────── */

function SnapshotCard({
  s,
  color,
  onRemove,
  canRemove,
}: {
  s: SymbolSnapshot;
  color: string;
  onRemove: () => void;
  canRemove: boolean;
}) {
  return (
    <Card className="relative overflow-hidden">
      <div className="h-1.5" style={{ background: color }} />
      {canRemove && (
        <button
          onClick={onRemove}
          className="absolute right-3 top-3 rounded-full p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          title="Remove from comparison"
        >
          <X className="size-3.5" />
        </button>
      )}
      <CardHeader className="pb-2">
        <CardTitle>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold" style={{ color }}>
              {s.symbol.replace(".NS", "")}
            </span>
          </div>
          <p className="mt-0.5 truncate text-xs font-normal text-muted-foreground">
            {s.name}
          </p>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex items-baseline justify-between">
          <span className="font-mono text-2xl font-bold">
            ₹{fmt(s.last_price)}
          </span>
          <span
            className={cn(
              "flex items-center gap-0.5 rounded-full px-2 py-0.5 font-mono text-xs font-semibold",
              s.change_pct >= 0
                ? "bg-up/10 text-up"
                : "bg-down/10 text-down",
            )}
          >
            {s.change_pct >= 0 ? (
              <ArrowUpRight className="size-3" />
            ) : (
              <ArrowDownRight className="size-3" />
            )}
            {s.change_pct >= 0 ? "+" : ""}
            {s.change_pct.toFixed(2)}%
          </span>
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
          <Row label="Volume" value={fmt(s.volume)} />
          <Row label="Mkt Cap" value={fmtCap(s.market_cap)} />
          <Row label="P/E Ratio" value={s.pe_ratio?.toFixed(1) ?? "—"} />
          <Row
            label="RSI"
            value={`${s.rsi?.toFixed(0) ?? "—"} ${rsiLabel(s.rsi)}`}
          />
          <Row
            label="52w High"
            value={s.high_52w ? `₹${fmt(s.high_52w)}` : "—"}
          />
          <Row
            label="52w Low"
            value={s.low_52w ? `₹${fmt(s.low_52w)}` : "—"}
          />
        </div>

        <div className="border-t border-border pt-2">
          <div className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Trend indicators
            <InfoTip side="right">
              SMA 20/50 show the average price over 20 and 50 days. When the
              short-term average crosses above the long-term, it&apos;s a bullish
              signal.
            </InfoTip>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
            <Row
              label="SMA 20"
              value={s.sma_20 ? `₹${fmt(s.sma_20)}` : "—"}
            />
            <Row
              label="SMA 50"
              value={s.sma_50 ? `₹${fmt(s.sma_50)}` : "—"}
            />
            <Row label="MACD" value={s.macd?.toFixed(2) ?? "—"} />
            <Row label="Signal" value={s.macd_signal?.toFixed(2) ?? "—"} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <>
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-mono">{value}</span>
    </>
  );
}

/* ── Normalised chart ──────────────────────────────────────────────────── */

function NormalizedChart({
  data,
  symbols,
}: {
  data: { date: string; values: Record<string, number> }[];
  symbols: string[];
}) {
  if (!data.length) return null;

  const allVals = data.flatMap((d) => Object.values(d.values));
  const min = Math.min(...allVals);
  const max = Math.max(...allVals);
  const range = max - min || 1;
  const h = 180;
  const w = 600;
  const pad = 40;

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="size-4 text-muted-foreground" />
          Normalised performance
          <InfoTip side="right">
            Each stock starts at 100 on the earliest date shown. A value of 120
            means the stock gained 20% over that period. This lets you compare
            stocks with very different prices on the same scale.
          </InfoTip>
          <span className="ml-auto font-mono text-[10px] font-normal text-muted-foreground">
            Base = 100
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Legend */}
        <div className="flex flex-wrap gap-4">
          {symbols.map((sym, i) => (
            <div key={sym} className="flex items-center gap-1.5 text-xs">
              <span
                className="size-2.5 rounded-full"
                style={{ background: COLORS[i % COLORS.length] }}
              />
              <span className="font-mono text-muted-foreground">
                {sym.replace(".NS", "")}
              </span>
            </div>
          ))}
        </div>

        {/* Chart */}
        <svg
          viewBox={`0 0 ${w} ${h}`}
          className="w-full"
          preserveAspectRatio="none"
        >
          {/* Grid */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct) => {
            const val = min + pct * range;
            const y = pad + (1 - pct) * (h - 2 * pad);
            return (
              <g key={pct}>
                <line
                  x1={pad}
                  y1={y}
                  x2={w - pad}
                  y2={y}
                  stroke="currentColor"
                  className="text-border"
                  strokeWidth={0.5}
                />
                <text
                  x={pad - 4}
                  y={y + 3}
                  textAnchor="end"
                  className="fill-muted-foreground"
                  fontSize={8}
                >
                  {val.toFixed(0)}
                </text>
              </g>
            );
          })}

          {/* Lines */}
          {symbols.map((sym, si) => {
            const pts = data
              .map((d, i) => {
                const v = d.values[sym];
                if (v == null) return null;
                const x = pad + (i / (data.length - 1)) * (w - 2 * pad);
                const y = pad + (1 - (v - min) / range) * (h - 2 * pad);
                return `${x},${y}`;
              })
              .filter(Boolean)
              .join(" ");
            return (
              <polyline
                key={sym}
                points={pts}
                fill="none"
                stroke={COLORS[si % COLORS.length]}
                strokeWidth={2}
              />
            );
          })}
        </svg>
      </CardContent>
    </Card>
  );
}

/* ── Main page ────────────────────────────────────────────────────────── */

export default function ComparePage() {
  const [symbols, setSymbols] = useState<string[]>([]);
  const [period, setPeriod] = useState("1y");
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerSlot, setPickerSlot] = useState(0);

  const { data, isLoading, isError } = useCompare(symbols, period);

  const openPicker = (slot: number) => {
    setPickerSlot(slot);
    setPickerOpen(true);
  };

  const handleSelect = (ticker: string) => {
    const next = [...symbols];
    if (pickerSlot < next.length) {
      next[pickerSlot] = ticker;
    } else {
      next.push(ticker);
    }
    setSymbols(next);
  };

  const removeSymbol = (sym: string) => {
    setSymbols(symbols.filter((s) => s !== sym));
  };

  const filled = data?.symbols ?? [];
  const emptySlots = Math.max(0, 2 - symbols.length);

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Compare</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Pick 2–4 stocks to see them side by side.
          </p>
        </div>
        {symbols.length > 0 && (
          <div className="flex items-center gap-3">
            <div className="w-28">
              <Label className="text-xs">Period</Label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="h-8 font-mono text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1mo">1 Month</SelectItem>
                  <SelectItem value="3mo">3 Months</SelectItem>
                  <SelectItem value="6mo">6 Months</SelectItem>
                  <SelectItem value="1y">1 Year</SelectItem>
                  <SelectItem value="3y">3 Years</SelectItem>
                  <SelectItem value="5y">5 Years</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSymbols([])}
              className="mt-5"
            >
              Clear all
            </Button>
          </div>
        )}
      </div>

      {/* ── Slot cards ── */}
      <div className="grid gap-4 sm:grid-cols-2">
        {symbols.map((sym, i) => {
          const snap = filled.find((s) => s.symbol === sym);
          return snap ? (
            <SnapshotCard
              key={sym}
              s={snap}
              color={COLORS[i]}
              onRemove={() => removeSymbol(sym)}
              canRemove={symbols.length > 2}
            />
          ) : (
            <div key={sym} className="flex items-center justify-center">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          );
        })}

        {symbols.length < 2 &&
          Array.from({ length: emptySlots }).map((_, i) => (
            <EmptySlot
              key={`empty-${i}`}
              index={symbols.length + i}
              onClick={() => openPicker(symbols.length + i)}
            />
          ))}

        {symbols.length >= 2 && symbols.length < 4 && (
          <button
            onClick={() => openPicker(symbols.length)}
            className={cn(
              "flex min-h-[240px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border p-6 transition-all",
              "hover:border-emerald-500/50 hover:bg-emerald-500/5",
            )}
          >
            <Plus className="size-5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              Add another stock
            </span>
          </button>
        )}
      </div>

      {/* ── Loading ── */}
      {isLoading && symbols.length >= 2 && (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      )}

      {/* ── Error ── */}
      {isError && symbols.length >= 2 && (
        <div className="rounded-2xl border border-down/20 bg-down/5 p-4 text-sm text-down">
          Failed to fetch comparison data. Check that the symbols are valid NSE
          stocks.
        </div>
      )}

      {/* ── Chart + table ── */}
      {data && data.normalized.length > 0 && (
        <div className="space-y-6">
          <NormalizedChart
            data={data.normalized}
            symbols={data.symbols.map((s) => s.symbol)}
          />

          {/* Side-by-side table */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-sm">
                Side-by-side comparison
                <InfoTip side="right">
                  All key metrics in one table so you can compare at a glance.
                  Tap any column header to highlight it.
                </InfoTip>
              </CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2.5 pr-4 text-left font-semibold text-muted-foreground">
                      Metric
                    </th>
                    {data.symbols.map((s, i) => (
                      <th
                        key={s.symbol}
                        className="py-2.5 px-3 text-right font-mono font-semibold"
                        style={{ color: COLORS[i] }}
                      >
                        {s.symbol.replace(".NS", "")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {[
                    {
                      label: "Price",
                      fn: (s: SymbolSnapshot) => `₹${fmt(s.last_price)}`,
                    },
                    {
                      label: "Change",
                      fn: (s: SymbolSnapshot) =>
                        `${s.change_pct >= 0 ? "+" : ""}${s.change_pct.toFixed(2)}%`,
                      cls: (s: SymbolSnapshot) =>
                        s.change_pct >= 0 ? "text-up" : "text-down",
                    },
                    {
                      label: "Volume",
                      fn: (s: SymbolSnapshot) => fmt(s.volume),
                    },
                    {
                      label: "Market Cap",
                      fn: (s: SymbolSnapshot) => fmtCap(s.market_cap),
                    },
                    {
                      label: "P/E Ratio",
                      fn: (s: SymbolSnapshot) => s.pe_ratio?.toFixed(1) ?? "—",
                    },
                    {
                      label: "RSI",
                      fn: (s: SymbolSnapshot) =>
                        `${s.rsi?.toFixed(0) ?? "—"} ${rsiLabel(s.rsi)}`,
                      cls: (s: SymbolSnapshot) =>
                        s.rsi != null && s.rsi > 70
                          ? "text-down"
                          : s.rsi != null && s.rsi < 30
                            ? "text-up"
                            : "",
                    },
                    {
                      label: "52w High",
                      fn: (s: SymbolSnapshot) =>
                        s.high_52w ? `₹${fmt(s.high_52w)}` : "—",
                    },
                    {
                      label: "52w Low",
                      fn: (s: SymbolSnapshot) =>
                        s.low_52w ? `₹${fmt(s.low_52w)}` : "—",
                    },
                    {
                      label: "SMA 20",
                      fn: (s: SymbolSnapshot) =>
                        s.sma_20 ? `₹${fmt(s.sma_20)}` : "—",
                    },
                    {
                      label: "SMA 50",
                      fn: (s: SymbolSnapshot) =>
                        s.sma_50 ? `₹${fmt(s.sma_50)}` : "—",
                    },
                    {
                      label: "MACD",
                      fn: (s: SymbolSnapshot) => s.macd?.toFixed(2) ?? "—",
                      cls: (s: SymbolSnapshot) =>
                        s.macd != null && s.macd_signal != null
                          ? s.macd > s.macd_signal
                            ? "text-up"
                            : "text-down"
                          : "",
                    },
                  ].map((row) => (
                    <tr key={row.label} className="border-b border-border/50">
                      <td className="py-2 pr-4 text-left text-muted-foreground">
                        {row.label}
                      </td>
                      {data.symbols.map((s) => (
                        <td
                          key={s.symbol}
                          className={cn("py-2 px-3 text-right", row.cls?.(s))}
                        >
                          {row.fn(s)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── Empty state hint ── */}
      {symbols.length === 0 && (
        <div className="rounded-2xl border border-dashed border-border py-16 text-center">
          <BarChart3 className="mx-auto mb-4 size-10 text-muted-foreground/40" />
          <p className="text-sm text-muted-foreground">
            Pick two stocks above to start comparing.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            You can add up to 4 stocks and change the time period.
          </p>
        </div>
      )}

      {/* ── Stock picker modal ── */}
      <StockPickerModal
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        onSelect={handleSelect}
        exclude={symbols}
      />
    </div>
  );
}
