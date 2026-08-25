"use client";

import { useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Edit3,
  Layers,
  LineChart,
  Plus,
  TrendingDown,
  TrendingUp,
  Volume2,
  X,
  Zap,
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
const COLORS_DIM = [
  "rgba(52,211,153,0.12)",
  "rgba(239,83,80,0.12)",
  "rgba(59,130,246,0.12)",
  "rgba(234,179,8,0.12)",
];

function fmt(n: number | null): string {
  if (n == null) return "—";
  return n.toLocaleString("en-IN");
}

function fmtCap(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1e12) return `₹${(n / 1e12).toFixed(1)}T`;
  if (n >= 1e9) return `₹${(n / 1e9).toFixed(1)}B`;
  if (n >= 1e7) return `₹${(n / 1e7).toFixed(1)}Cr`;
  return `₹${n.toLocaleString("en-IN")}`;
}

/* ── Mini sparkline in card header ───────────────────────────────────── */

function Sparkline({
  data,
  symbol,
  color,
  width = 72,
  height = 32,
}: {
  data: { date: string; values: Record<string, number> }[];
  symbol: string;
  color: string;
  width?: number;
  height?: number;
}) {
  const vals = data
    .map((d) => d.values[symbol])
    .filter((v) => v != null) as number[];
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const range = max - min || 1;
  const pad = 2;
  const pts = vals
    .map((v, i) => {
      const x = pad + (i / (vals.length - 1)) * (width - 2 * pad);
      const y = pad + (1 - (v - min) / range) * (height - 2 * pad);
      return `${x},${y}`;
    })
    .join(" ");
  const lastVal = vals[vals.length - 1];
  const lastY =
    pad + (1 - (lastVal - min) / range) * (height - 2 * pad);
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <polyline
        points={pts}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={width - pad} cy={lastY} r={2.5} fill={color} />
    </svg>
  );
}

/* ── Metric row with icon ────────────────────────────────────────────── */

function MetricPill({
  icon,
  label,
  value,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  tone?: "up" | "down" | "neutral";
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg bg-background/50 px-2.5 py-1.5">
      <span className="text-muted-foreground">{icon}</span>
      <span className="min-w-0 flex-1 truncate text-[11px] text-muted-foreground">
        {label}
      </span>
      <span
        className={cn(
          "font-mono text-xs font-semibold",
          tone === "up" && "text-up",
          tone === "down" && "text-down",
          (!tone || tone === "neutral") && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

/* ── Empty slot ──────────────────────────────────────────────────────── */

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
        "group relative flex min-h-[340px] flex-col items-center justify-center gap-5 overflow-hidden rounded-2xl border-2 border-dashed border-border transition-all duration-300",
        "hover:border-emerald-500/60 hover:shadow-lg hover:shadow-emerald-500/5",
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/5 via-transparent to-cyan-500/5 opacity-0 transition-opacity group-hover:opacity-100" />
      <div className="relative flex flex-col items-center gap-4">
        <div className="rounded-2xl bg-muted/80 p-5 transition-all group-hover:scale-110 group-hover:bg-emerald-500/10">
          <Plus className="size-7 text-muted-foreground transition-colors group-hover:text-emerald-500" />
        </div>
        <div className="text-center">
          <p className="text-sm font-medium text-muted-foreground group-hover:text-foreground">
            Select a stock
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground/60">
            Slot {index + 1}
          </p>
        </div>
      </div>
    </button>
  );
}

/* ── Snapshot card ───────────────────────────────────────────────────── */

function SnapshotCard({
  s,
  color,
  colorDim,
  normalizedData,
  onEdit,
  onRemove,
}: {
  s: SymbolSnapshot;
  color: string;
  colorDim: string;
  normalizedData: { date: string; values: Record<string, number> }[];
  onEdit: () => void;
  onRemove: () => void;
}) {
  const up = s.change_pct >= 0;
  const rsiTone =
    s.rsi != null && s.rsi > 70
      ? ("down" as const)
      : s.rsi != null && s.rsi < 30
        ? ("up" as const)
        : ("neutral" as const);
  const macdTone =
    s.macd != null && s.macd_signal != null
      ? s.macd > s.macd_signal
        ? ("up" as const)
        : ("down" as const)
      : ("neutral" as const);

  const range52 =
    s.high_52w && s.low_52w ? s.high_52w - s.low_52w : null;
  const pos52 =
    range52 && range52 > 0
      ? Math.min(100, Math.max(5, ((s.last_price - s.low_52w!) / range52) * 100))
      : 50;

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border bg-card transition-all duration-300 hover:shadow-lg">
      {/* Header with gradient */}
      <div
        className="relative overflow-hidden px-5 pt-5 pb-4"
        style={{ background: `linear-gradient(135deg, ${colorDim}, transparent)` }}
      >
        {/* Edit / Remove — icons only, visible on hover */}
        <div className="absolute right-3 top-3 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
          <button
            onClick={onEdit}
            className="rounded-full bg-background/80 p-1.5 text-muted-foreground backdrop-blur transition-colors hover:bg-background hover:text-foreground"
            title="Change stock"
          >
            <Edit3 className="size-3.5" />
          </button>
          <button
            onClick={onRemove}
            className="rounded-full bg-background/80 p-1.5 text-muted-foreground backdrop-blur transition-colors hover:bg-down/10 hover:text-down"
            title="Remove"
          >
            <X className="size-3.5" />
          </button>
        </div>

        {/* Ticker + sparkline */}
        <div className="flex items-start justify-between">
          <div>
            <span className="font-mono text-lg font-bold" style={{ color }}>
              {s.symbol.replace(".NS", "")}
            </span>
            <p className="mt-0.5 truncate text-xs text-muted-foreground">
              {s.name}
            </p>
          </div>
          <Sparkline
            data={normalizedData}
            symbol={s.symbol}
            color={color}
          />
        </div>

        {/* Price + change */}
        <div className="mt-3 flex items-baseline gap-3">
          <span className="font-mono text-3xl font-bold tracking-tight">
            ₹{fmt(s.last_price)}
          </span>
          <span
            className={cn(
              "flex items-center gap-0.5 rounded-full px-2 py-0.5 font-mono text-xs font-bold",
              up ? "bg-up/15 text-up" : "bg-down/15 text-down",
            )}
          >
            {up ? (
              <ArrowUpRight className="size-3" />
            ) : (
              <ArrowDownRight className="size-3" />
            )}
            {up ? "+" : ""}
            {s.change_pct.toFixed(2)}%
          </span>
        </div>
      </div>

      {/* Body */}
      <div className="space-y-3 px-5 py-4">
        {/* Key metrics grid */}
        <div className="grid grid-cols-2 gap-1.5">
          <MetricPill
            icon={<Volume2 className="size-3" />}
            label="Vol"
            value={fmt(s.volume)}
          />
          <MetricPill
            icon={<Layers className="size-3" />}
            label="Mkt Cap"
            value={fmtCap(s.market_cap)}
          />
          <MetricPill
            icon={<BarChart3 className="size-3" />}
            label="P/E"
            value={s.pe_ratio?.toFixed(1) ?? "—"}
          />
          <MetricPill
            icon={<Zap className="size-3" />}
            label="RSI"
            value={`${s.rsi?.toFixed(0) ?? "—"}${s.rsi != null ? (s.rsi > 70 ? " OB" : s.rsi < 30 ? " OS" : "") : ""}`}
            tone={rsiTone}
          />
        </div>

        {/* 52-week range bar */}
        {s.high_52w && s.low_52w && (
          <div className="rounded-lg bg-background/50 px-2.5 py-2">
            <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              52-week range
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] text-down">
                ₹{fmt(s.low_52w)}
              </span>
              <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                <div
                  className="absolute h-full rounded-full"
                  style={{
                    background: `linear-gradient(90deg, ${color}66, ${color})`,
                    width: `${pos52}%`,
                  }}
                />
                <div
                  className="absolute top-1/2 size-2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-background"
                  style={{ left: `${pos52}%`, background: color }}
                />
              </div>
              <span className="font-mono text-[11px] text-up">
                ₹{fmt(s.high_52w)}
              </span>
            </div>
          </div>
        )}

        {/* Trend indicators */}
        <div>
          <div className="mb-1.5 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            <TrendingUp className="size-3" />
            Trend
            <InfoTip side="right">
              SMA 20/50: average price over 20 and 50 days. MACD: momentum
              indicator — above signal line is bullish.
            </InfoTip>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            <MetricPill
              icon={<LineChart className="size-3" />}
              label="SMA 20"
              value={s.sma_20 ? `₹${fmt(s.sma_20)}` : "—"}
            />
            <MetricPill
              icon={<LineChart className="size-3" />}
              label="SMA 50"
              value={s.sma_50 ? `₹${fmt(s.sma_50)}` : "—"}
            />
            <MetricPill
              icon={<TrendingUp className="size-3" />}
              label="MACD"
              value={s.macd?.toFixed(2) ?? "—"}
              tone={macdTone}
            />
            <MetricPill
              icon={<TrendingDown className="size-3" />}
              label="Signal"
              value={s.macd_signal?.toFixed(2) ?? "—"}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Normalised chart ────────────────────────────────────────────────── */

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
  const h = 200;
  const w = 600;
  const pad = 44;

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-1">
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="size-4 text-muted-foreground" />
          Normalised performance
          <InfoTip side="right">
            Each stock starts at 100 on the earliest date shown. A value of 120
            means the stock gained 20%. This lets you compare stocks with very
            different prices on the same scale.
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

        {/* SVG chart */}
        <svg
          viewBox={`0 0 ${w} ${h}`}
          className="w-full"
          preserveAspectRatio="none"
        >
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

/* ── Side-by-side table ──────────────────────────────────────────────── */

function ComparisonTable({
  data,
}: {
  data: SymbolSnapshot[];
}) {
  const rows: {
    label: string;
    icon: React.ReactNode;
    fn: (s: SymbolSnapshot) => string;
    cls?: (s: SymbolSnapshot) => string;
  }[] = [
    {
      label: "Price",
      icon: <BarChart3 className="size-3" />,
      fn: (s) => `₹${fmt(s.last_price)}`,
    },
    {
      label: "Change",
      icon: <ArrowUpRight className="size-3" />,
      fn: (s) =>
        `${s.change_pct >= 0 ? "+" : ""}${s.change_pct.toFixed(2)}%`,
      cls: (s) => (s.change_pct >= 0 ? "text-up" : "text-down"),
    },
    {
      label: "Volume",
      icon: <Volume2 className="size-3" />,
      fn: (s) => fmt(s.volume),
    },
    {
      label: "Market Cap",
      icon: <Layers className="size-3" />,
      fn: (s) => fmtCap(s.market_cap),
    },
    {
      label: "P/E Ratio",
      icon: <BarChart3 className="size-3" />,
      fn: (s) => s.pe_ratio?.toFixed(1) ?? "—",
    },
    {
      label: "RSI",
      icon: <Zap className="size-3" />,
      fn: (s) => `${s.rsi?.toFixed(0) ?? "—"}`,
      cls: (s) =>
        s.rsi != null && s.rsi > 70
          ? "text-down"
          : s.rsi != null && s.rsi < 30
            ? "text-up"
            : "",
    },
    {
      label: "52w High",
      icon: <TrendingUp className="size-3" />,
      fn: (s) => (s.high_52w ? `₹${fmt(s.high_52w)}` : "—"),
    },
    {
      label: "52w Low",
      icon: <TrendingDown className="size-3" />,
      fn: (s) => (s.low_52w ? `₹${fmt(s.low_52w)}` : "—"),
    },
    {
      label: "SMA 20",
      icon: <LineChart className="size-3" />,
      fn: (s) => (s.sma_20 ? `₹${fmt(s.sma_20)}` : "—"),
    },
    {
      label: "SMA 50",
      icon: <LineChart className="size-3" />,
      fn: (s) => (s.sma_50 ? `₹${fmt(s.sma_50)}` : "—"),
    },
    {
      label: "MACD",
      icon: <TrendingUp className="size-3" />,
      fn: (s) => s.macd?.toFixed(2) ?? "—",
      cls: (s) =>
        s.macd != null && s.macd_signal != null
          ? s.macd > s.macd_signal
            ? "text-up"
            : "text-down"
          : "",
    },
  ];

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          Side-by-side comparison
          <InfoTip side="right">
            All key metrics in one table for quick comparison.
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
              {data.map((s, i) => (
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
            {rows.map((row) => (
              <tr key={row.label} className="border-b border-border/50">
                <td className="flex items-center gap-1.5 py-2 pr-4 text-left text-muted-foreground">
                  {row.icon}
                  {row.label}
                </td>
                {data.map((s) => (
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

  const editSymbol = (sym: string) => {
    const idx = symbols.indexOf(sym);
    if (idx >= 0) openPicker(idx);
  };

  const normalizedData = data?.normalized ?? [];
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

      {/* Slot cards */}
      <div className="grid gap-4 sm:grid-cols-2">
        {symbols.map((sym, i) => {
          const snap = filled.find((s) => s.symbol === sym);
          return snap ? (
            <SnapshotCard
              key={sym}
              s={snap}
              color={COLORS[i]}
              colorDim={COLORS_DIM[i]}
              normalizedData={normalizedData}
              onEdit={() => editSymbol(sym)}
              onRemove={() => removeSymbol(sym)}
            />
          ) : (
            <div
              key={sym}
              className="flex min-h-[340px] items-center justify-center rounded-2xl border border-border"
            >
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span className="size-4 animate-spin rounded-full border-2 border-muted border-t-foreground" />
                Loading…
              </div>
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
              "flex min-h-[340px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-border p-6 transition-all duration-300",
              "hover:border-emerald-500/50 hover:bg-emerald-500/5 hover:shadow-md",
            )}
          >
            <Plus className="size-5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              Add another stock
            </span>
          </button>
        )}
      </div>

      {/* Loading */}
      {isLoading && symbols.length >= 2 && (
        <div className="space-y-4">
          <Skeleton className="h-48 w-full rounded-2xl" />
          <Skeleton className="h-64 w-full rounded-2xl" />
        </div>
      )}

      {/* Error */}
      {isError && symbols.length >= 2 && (
        <div className="rounded-2xl border border-down/20 bg-down/5 p-4 text-sm text-down">
          Failed to fetch comparison data. Check that the symbols are valid.
        </div>
      )}

      {/* Chart + table */}
      {data && data.normalized.length > 0 && (
        <div className="space-y-6">
          <NormalizedChart
            data={data.normalized}
            symbols={data.symbols.map((s) => s.symbol)}
          />
          <ComparisonTable data={data.symbols} />
        </div>
      )}

      {/* Empty state hint */}
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

      {/* Stock picker modal */}
      <StockPickerModal
        open={pickerOpen}
        onOpenChange={setPickerOpen}
        onSelect={handleSelect}
        exclude={symbols}
      />
    </div>
  );
}
