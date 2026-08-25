"use client";

import { useState } from "react";
import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Minus,
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
import { SymbolSearch } from "@/components/symbol-search";
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

function SnapshotCard({ s, color }: { s: SymbolSnapshot; color: string }) {
  return (
    <Card className="overflow-hidden">
      <div className="h-1" style={{ background: color }} />
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between">
          <div>
            <span className="font-mono text-sm font-bold" style={{ color }}>
              {s.symbol}
            </span>
            <span className="ml-2 text-xs text-muted-foreground">{s.name}</span>
          </div>
          <span
            className={cn(
              "flex items-center gap-0.5 font-mono text-sm font-semibold",
              s.change_pct >= 0 ? "text-up" : "text-down",
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
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="font-mono text-2xl font-bold">
          ₹{fmt(s.last_price)}
        </div>

        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
          <Row label="Volume" value={fmt(s.volume)} />
          <Row label="Mkt Cap" value={fmtCap(s.market_cap)} />
          <Row label="P/E" value={s.pe_ratio?.toFixed(1) ?? "—"} />
          <Row label="52w High" value={s.high_52w ? `₹${fmt(s.high_52w)}` : "—"} />
          <Row label="52w Low" value={s.low_52w ? `₹${fmt(s.low_52w)}` : "—"} />
          <Row label="RSI" value={s.rsi?.toFixed(1) ?? "—"} />
        </div>

        <div className="border-t border-border pt-2">
          <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Technical
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-[11px]">
            <Row label="SMA 20" value={s.sma_20 ? `₹${fmt(s.sma_20)}` : "—"} />
            <Row label="SMA 50" value={s.sma_50 ? `₹${fmt(s.sma_50)}` : "—"} />
            <Row label="MACD" value={s.macd?.toFixed(2) ?? "—"} />
            <Row
              label="Signal"
              value={s.macd_signal?.toFixed(2) ?? "—"}
            />
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
  const h = 160;
  const w = 600;
  const pad = 10;

  const paths = symbols.map((sym) => {
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
    return pts;
  });

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-3">
        {symbols.map((sym, i) => (
          <div key={sym} className="flex items-center gap-1.5 text-xs">
            <span
              className="size-2.5 rounded-full"
              style={{ background: COLORS[i % COLORS.length] }}
            />
            <span className="font-mono text-muted-foreground">{sym}</span>
          </div>
        ))}
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
        {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
          <line
            key={pct}
            x1={pad}
            y1={pad + pct * (h - 2 * pad)}
            x2={w - pad}
            y2={pad + pct * (h - 2 * pad)}
            stroke="currentColor"
            className="text-border"
            strokeWidth={0.5}
          />
        ))}
        <text x={pad} y={pad - 2} className="fill-muted-foreground" fontSize={8}>
          {max.toFixed(0)}
        </text>
        <text x={pad} y={h - pad + 10} className="fill-muted-foreground" fontSize={8}>
          {min.toFixed(0)}
        </text>
        {paths.map((pts, i) => (
          <polyline
            key={symbols[i]}
            points={pts}
            fill="none"
            stroke={COLORS[i % COLORS.length]}
            strokeWidth={2}
          />
        ))}
      </svg>
    </div>
  );
}

export default function ComparePage() {
  const [symbols, setSymbols] = useState<string[]>(["RELIANCE.NS", "TCS.NS"]);
  const [period, setPeriod] = useState("1y");
  const [pending, setPending] = useState("");

  const { data, isLoading, isError } = useCompare(symbols, period);

  const addSymbol = () => {
    const s = pending.trim().toUpperCase();
    if (s && !symbols.includes(s) && symbols.length < 4) {
      setSymbols([...symbols, s]);
      setPending("");
    }
  };

  const removeSymbol = (sym: string) => {
    if (symbols.length > 2) {
      setSymbols(symbols.filter((s) => s !== sym));
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <h1 className="text-2xl font-semibold">Compare</h1>

      {/* ── Config ── */}
      <Card>
        <CardContent className="flex flex-wrap items-end gap-4 pt-6">
          <div className="flex-1 space-y-1.5">
            <Label className="text-xs">Symbols ({symbols.length}/4)</Label>
            <div className="flex flex-wrap gap-2">
              {symbols.map((s, i) => (
                <span
                  key={s}
                  className="flex items-center gap-1 rounded-full border px-2.5 py-1 font-mono text-xs font-semibold"
                  style={{ borderColor: COLORS[i], color: COLORS[i] }}
                >
                  {s}
                  {symbols.length > 2 && (
                    <button onClick={() => removeSymbol(s)}>
                      <X className="size-3" />
                    </button>
                  )}
                </span>
              ))}
            </div>
          </div>

          {symbols.length < 4 && (
            <div className="flex items-end gap-2">
              <div className="w-56">
                <SymbolSearch value={pending} onChange={setPending} placeholder="Add symbol…" />
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={addSymbol}
                disabled={!pending.trim()}
              >
                <Plus className="size-4" />
              </Button>
            </div>
          )}

          <div className="w-32">
            <Label className="text-xs">Period</Label>
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="font-mono text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1mo">1M</SelectItem>
                <SelectItem value="3mo">3M</SelectItem>
                <SelectItem value="6mo">6M</SelectItem>
                <SelectItem value="1y">1Y</SelectItem>
                <SelectItem value="3y">3Y</SelectItem>
                <SelectItem value="5y">5Y</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* ── Loading ── */}
      {isLoading && (
        <div className="grid gap-4 sm:grid-cols-2">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      )}

      {/* ── Error ── */}
      {isError && (
        <div className="rounded-xl border border-down/20 bg-down/5 p-4 text-sm text-down">
          Failed to fetch comparison data. Check that the symbols are valid.
        </div>
      )}

      {/* ── Results ── */}
      {data && (
        <div className="space-y-6">
          {/* Snapshot cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.symbols.map((s, i) => (
              <SnapshotCard key={s.symbol} s={s} color={COLORS[i]} />
            ))}
          </div>

          {/* Normalised chart */}
          {data.normalized.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-sm">
                  <BarChart3 className="size-4 text-muted-foreground" />
                  Normalised performance (base 100)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <NormalizedChart
                  data={data.normalized}
                  symbols={data.symbols.map((s) => s.symbol)}
                />
              </CardContent>
            </Card>
          )}

          {/* Comparison table */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Side-by-side</CardTitle>
            </CardHeader>
            <CardContent className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-border">
                    <th className="py-2 pr-4 text-left font-semibold text-muted-foreground">
                      Metric
                    </th>
                    {data.symbols.map((s, i) => (
                      <th
                        key={s.symbol}
                        className="py-2 px-3 text-right font-mono font-semibold"
                        style={{ color: COLORS[i] }}
                      >
                        {s.symbol}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="font-mono">
                  {[
                    { label: "Price", fn: (s: SymbolSnapshot) => `₹${fmt(s.last_price)}` },
                    { label: "Change %", fn: (s: SymbolSnapshot) => `${s.change_pct >= 0 ? "+" : ""}${s.change_pct.toFixed(2)}%`, cls: (s: SymbolSnapshot) => s.change_pct >= 0 ? "text-up" : "text-down" },
                    { label: "Volume", fn: (s: SymbolSnapshot) => fmt(s.volume) },
                    { label: "Mkt Cap", fn: (s: SymbolSnapshot) => fmtCap(s.market_cap) },
                    { label: "P/E", fn: (s: SymbolSnapshot) => s.pe_ratio?.toFixed(1) ?? "—" },
                    { label: "52w High", fn: (s: SymbolSnapshot) => s.high_52w ? `₹${fmt(s.high_52w)}` : "—" },
                    { label: "52w Low", fn: (s: SymbolSnapshot) => s.low_52w ? `₹${fmt(s.low_52w)}` : "—" },
                    { label: "RSI", fn: (s: SymbolSnapshot) => s.rsi?.toFixed(1) ?? "—" },
                    { label: "SMA 20", fn: (s: SymbolSnapshot) => s.sma_20 ? `₹${fmt(s.sma_20)}` : "—" },
                    { label: "SMA 50", fn: (s: SymbolSnapshot) => s.sma_50 ? `₹${fmt(s.sma_50)}` : "—" },
                    { label: "MACD", fn: (s: SymbolSnapshot) => s.macd?.toFixed(2) ?? "—" },
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
    </div>
  );
}
