"use client";

import { useState } from "react";
import {
  BarChart3,
  Play,
  Trophy,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { InfoTip } from "@/components/info-tip";
import { useStrategies, useRunBacktest } from "@/lib/hooks/use-backtest";
import type { BacktestResult } from "@/lib/api/backtest";
import { cn } from "@/lib/utils";

function MetricCard({
  label,
  value,
  sub,
  icon,
  tone,
}: {
  label: string;
  value: string;
  sub?: string;
  icon?: React.ReactNode;
  tone?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-3 text-center">
      <div className="mb-0.5 flex items-center justify-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className={cn("font-mono text-base font-bold tabular-nums", tone)}>
        {value}
      </div>
      {sub && (
        <div className="font-mono text-[10px] text-muted-foreground">{sub}</div>
      )}
    </div>
  );
}

function EquityCurve({ data }: { data: { date: string; equity: number }[] }) {
  if (!data.length) return null;
  const min = Math.min(...data.map((d) => d.equity));
  const max = Math.max(...data.map((d) => d.equity));
  const range = max - min || 1;
  const h = 120;
  const w = 600;
  const points = data
    .map((d, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((d.equity - min) / range) * h;
      return `${x},${y}`;
    })
    .join(" ");
  const firstEq = data[0].equity;
  const lastEq = data[data.length - 1].equity;
  const isUp = lastEq >= firstEq;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" preserveAspectRatio="none">
      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((pct) => (
        <line
          key={pct}
          x1={0}
          y1={h * pct}
          x2={w}
          y2={h * pct}
          stroke="currentColor"
          className="text-border"
          strokeWidth={0.5}
        />
      ))}
      {/* Area fill */}
      <polygon
        points={`0,${h} ${points} ${w},${h}`}
        fill={isUp ? "rgb(52, 211, 153)" : "rgb(239, 83, 80)"}
        opacity={0.1}
      />
      {/* Line */}
      <polyline
        points={points}
        fill="none"
        stroke={isUp ? "rgb(52, 211, 153)" : "rgb(239, 83, 80)"}
        strokeWidth={1.5}
      />
    </svg>
  );
}

function MonthlyHeatmap({ data }: { data: { month: string; return_pct: number }[] }) {
  if (!data.length) return null;
  return (
    <div className="grid grid-cols-6 gap-1 sm:grid-cols-12">
      {data.map((d) => {
        const pct = d.return_pct;
        const intensity = Math.min(Math.abs(pct) / 8, 1);
        const bg = pct >= 0
          ? `rgba(52, 211, 153, ${0.15 + intensity * 0.6})`
          : `rgba(239, 83, 80, ${0.15 + intensity * 0.6})`;
        return (
          <div
            key={d.month}
            className="flex flex-col items-center rounded p-1 text-[9px] font-mono"
            style={{ background: bg }}
            title={`${d.month}: ${pct >= 0 ? "+" : ""}${pct.toFixed(2)}%`}
          >
            <span className="text-muted-foreground">{d.month.slice(5)}</span>
            <span className={pct >= 0 ? "text-up" : "text-down"}>
              {pct >= 0 ? "+" : ""}
              {pct.toFixed(1)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

export default function BacktestPage() {
  const strategies = useStrategies();
  const runBt = useRunBacktest();

  const [symbol, setSymbol] = useState("RELIANCE.NS");
  const [strategy, setStrategy] = useState("SMA Crossover");
  const [years, setYears] = useState(5);
  const [capital, setCapital] = useState(100000);
  const [sl, setSl] = useState(5);
  const [tp, setTp] = useState(0);
  const [comm, setComm] = useState(0.1);

  const result: BacktestResult | null = runBt.data ?? null;

  const handleRun = () => {
    runBt.mutate({
      symbol: symbol.trim().toUpperCase(),
      strategy,
      years,
      initial_capital: capital,
      commission_pct: comm,
      sl_pct: sl,
      tp_pct: tp,
      position_size_pct: 100,
    });
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <h1 className="text-2xl font-semibold">Backtesting</h1>

      {/* ── Config form ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Play className="size-4 text-ai" />
            Configure backtest
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="col-span-2 space-y-1.5">
              <Label htmlFor="bt-symbol" className="text-xs">Symbol</Label>
              <Input
                id="bt-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="font-mono text-sm"
                placeholder="RELIANCE.NS"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Strategy</Label>
              <Select value={strategy} onValueChange={setStrategy}>
                <Trigger className="w-full font-mono text-sm">
                  <SelectValue />
                </Trigger>
                <SelectContent>
                  {strategies.data?.strategies.map((s) => (
                    <SelectItem key={s.name} value={s.name}>
                      {s.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {strategies.data && (
                <p className="text-[11px] text-muted-foreground">
                  {strategies.data.strategies.find((s) => s.name === strategy)?.description}
                </p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Period</Label>
              <Select value={String(years)} onValueChange={(v) => setYears(Number(v))}>
                <Trigger className="w-full font-mono text-sm">
                  <SelectValue />
                </Trigger>
                <SelectContent>
                  {[1, 2, 3, 5, 7, 10].map((y) => (
                    <SelectItem key={y} value={String(y)}>
                      {y}y
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="space-y-1.5">
              <Label htmlFor="bt-cap" className="text-xs">Capital (₹)</Label>
              <Input
                id="bt-cap"
                type="number"
                min={10000}
                step={10000}
                value={capital}
                onChange={(e) => setCapital(Number(e.target.value))}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="bt-sl" className="text-xs">
                Stop-loss %
                <InfoTip side="top">0 = no stop loss</InfoTip>
              </Label>
              <Input
                id="bt-sl"
                type="number"
                min={0}
                max={20}
                value={sl}
                onChange={(e) => setSl(Number(e.target.value))}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="bt-tp" className="text-xs">
                Take-profit %
                <InfoTip side="top">0 = no take-profit (exit on signal only)</InfoTip>
              </Label>
              <Input
                id="bt-tp"
                type="number"
                min={0}
                max={50}
                value={tp}
                onChange={(e) => setTp(Number(e.target.value))}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="bt-comm" className="text-xs">
                Commission %
                <InfoTip side="top">Per-trade commission (each leg)</InfoTip>
              </Label>
              <Input
                id="bt-comm"
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={comm}
                onChange={(e) => setComm(Number(e.target.value))}
                className="font-mono text-sm"
              />
            </div>
          </div>

          <Button
            onClick={handleRun}
            disabled={runBt.isPending || !symbol.trim()}
            className="w-full bg-ai text-ai-foreground hover:bg-ai/90 sm:w-auto"
          >
            {runBt.isPending ? "Running..." : "Run Backtest"}
          </Button>
        </CardContent>
      </Card>

      {/* ── Error ── */}
      {runBt.isError && (
        <div className="rounded-lg border border-down/20 bg-down/5 p-4 text-sm text-down">
          {runBt.error instanceof Error ? runBt.error.message : "Backtest failed"}
        </div>
      )}

      {/* ── Loading ── */}
      {runBt.isPending && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))}
          </div>
          <Skeleton className="h-32 w-full rounded-lg" />
        </div>
      )}

      {/* ── Results ── */}
      {result && (
        <div className="space-y-6">
          {/* Strategy + symbol header */}
          <div className="flex items-center justify-between text-sm">
            <span className="font-mono text-muted-foreground">
              {result.strategy} · {result.symbol} · {result.years}y
            </span>
            <span className="font-mono text-muted-foreground">
              ₹{result.initial_capital.toLocaleString("en-IN")} → ₹
              {result.final_equity.toLocaleString("en-IN")}
            </span>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <MetricCard
              label="CAGR"
              value={`${result.cagr >= 0 ? "+" : ""}${result.cagr.toFixed(2)}%`}
              sub="Annualised return"
              icon={<TrendingUp className="size-3" />}
              tone={result.cagr >= 0 ? "text-up" : "text-down"}
            />
            <MetricCard
              label="Sharpe"
              value={result.sharpe.toFixed(2)}
              sub={result.sharpe > 2 ? "Excellent" : result.sharpe > 1 ? "Good" : result.sharpe > 0 ? "Marginal" : "Poor"}
              icon={<BarChart3 className="size-3" />}
              tone={result.sharpe > 1 ? "text-up" : result.sharpe > 0 ? "text-gold" : "text-down"}
            />
            <MetricCard
              label="Max Drawdown"
              value={`${result.max_dd.toFixed(2)}%`}
              sub={`${result.dd_dur_days} days`}
              icon={<TrendingDown className="size-3" />}
              tone="text-down"
            />
            <MetricCard
              label="Total Return"
              value={`${result.total_ret_pct >= 0 ? "+" : ""}${result.total_ret_pct.toFixed(2)}%`}
              sub={`Win rate ${result.win_rate.toFixed(1)}%`}
              icon={<Trophy className="size-3" />}
              tone={result.total_ret_pct >= 0 ? "text-up" : "text-down"}
            />
          </div>

          {/* Equity curve */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-xs text-muted-foreground">Equity Curve</CardTitle>
            </CardHeader>
            <CardContent>
              <EquityCurve data={result.equity_curve} />
            </CardContent>
          </Card>

          {/* Secondary metrics */}
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
            <MetricCard label="Sortino" value={result.sortino.toFixed(2)} tone={result.sortino > 1 ? "text-up" : "text-gold"} />
            <MetricCard label="Calmar" value={result.calmar.toFixed(2)} tone={result.calmar > 1 ? "text-up" : "text-gold"} />
            <MetricCard label="Profit Factor" value={result.profit_factor?.toFixed(2) ?? "∞"} tone={result.profit_factor && result.profit_factor > 1.5 ? "text-up" : "text-gold"} />
            <MetricCard label="Alpha" value={`${result.alpha >= 0 ? "+" : ""}${result.alpha.toFixed(2)}%`} tone={result.alpha >= 0 ? "text-up" : "text-down"} />
            <MetricCard label="Win Rate" value={`${result.win_rate.toFixed(1)}%`} sub={`${result.wins}W · ${result.losses}L`} tone={result.win_rate >= 50 ? "text-up" : "text-down"} />
            <MetricCard label="Avg Hold" value={`${result.avg_hold.toFixed(0)}d`} sub={`Expect ₹${result.expectancy.toFixed(0)}`} />
          </div>

          {/* Tabs: monthly + trades */}
          <Tabs defaultValue="trades">
            <TabsList className="w-full">
              <TabsTrigger value="trades" className="flex-1">
                Trade Log ({result.trades.length})
              </TabsTrigger>
              <TabsTrigger value="monthly" className="flex-1">
                Monthly Returns
              </TabsTrigger>
            </TabsList>

            <TabsContent value="trades">
              <div className="space-y-1.5">
                {result.trades.length === 0 ? (
                  <p className="py-8 text-center text-sm text-muted-foreground">
                    No trades executed.
                  </p>
                ) : (
                  result.trades.map((t, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
                    >
                      <div className="flex items-center gap-2">
                        <span
                          className={cn(
                            "rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold",
                            t.win ? "bg-up/10 text-up" : "bg-down/10 text-down",
                          )}
                        >
                          {t.exit_reason}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {t.entry_date} → {t.exit_date}
                        </span>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-xs">
                          ₹{t.entry_px.toLocaleString("en-IN")} → ₹{t.exit_px.toLocaleString("en-IN")}
                        </div>
                        <div
                          className={cn(
                            "font-mono text-xs font-semibold",
                            t.pnl >= 0 ? "text-up" : "text-down",
                          )}
                        >
                          {t.pnl >= 0 ? "+" : ""}₹{t.pnl.toLocaleString("en-IN")} ({t.pnl_pct >= 0 ? "+" : ""}
                          {t.pnl_pct.toFixed(2)}%)
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </TabsContent>

            <TabsContent value="monthly">
              <MonthlyHeatmap data={result.monthly_returns} />
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}

function Trigger({ className, children }: { className?: string; children: React.ReactNode }) {
  return (
    <button
      className={cn(
        "flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
    >
      {children}
    </button>
  );
}
