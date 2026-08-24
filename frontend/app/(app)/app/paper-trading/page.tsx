"use client";

import { useState } from "react";
import {
  Banknote,
  BarChart3,
  History,
  Package,
  RefreshCcw,
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
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useWatchlistTickers } from "@/lib/hooks/use-watchlist";
import {
  usePaperSummary,
  usePaperPositions,
  usePaperOrders,
  usePlacePaperOrder,
  useResetPaper,
} from "@/lib/hooks/use-paper";
import { cn } from "@/lib/utils";

function StatCard({
  label,
  value,
  icon,
  tone,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  tone?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 text-center">
      <div className="mb-1 flex items-center justify-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {icon}
        {label}
      </div>
      <div className={cn("font-mono text-lg font-bold tabular-nums", tone)}>
        {value}
      </div>
    </div>
  );
}

function OrderTicket() {
  const [symbol, setSymbol] = useState("");
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [qty, setQty] = useState(1);
  const [price, setPrice] = useState("");
  const watchlistTickers = useWatchlistTickers();
  const placeOrder = usePlacePaperOrder();
  const summary = usePaperSummary();

  const estimatedCost = qty * (parseFloat(price) || 0);

  const handleSubmit = () => {
    const p = parseFloat(price);
    if (!symbol || !p || qty <= 0) return;
    placeOrder.mutate(
      { symbol: symbol.trim().toUpperCase(), side, qty, price: p },
      {
        onSuccess: () => {
          setSymbol("");
          setPrice("");
          setQty(1);
        },
      },
    );
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Banknote className="size-4 text-ai" />
          Place order
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {/* Symbol */}
          <div className="col-span-2 space-y-1.5">
            <Label htmlFor="symbol" className="text-xs">
              Symbol
            </Label>
            <Input
              id="symbol"
              placeholder="RELIANCE.NS"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              className="font-mono text-sm"
            />
            {/* Quick-pick from watchlist */}
            {watchlistTickers.size > 0 && (
              <div className="flex flex-wrap gap-1">
                {Array.from(watchlistTickers)
                  .slice(0, 4)
                  .map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setSymbol(t)}
                      className={cn(
                        "rounded-md border px-1.5 py-0.5 font-mono text-[10px] transition-colors",
                        symbol === t
                          ? "border-ai bg-ai/10 text-ai"
                          : "border-border text-muted-foreground hover:bg-muted",
                      )}
                    >
                      {t.replace(".NS", "")}
                    </button>
                  ))}
              </div>
            )}
          </div>

          {/* Side */}
          <div className="space-y-1.5">
            <Label className="text-xs">Side</Label>
            <div className="flex gap-1">
              {(["BUY", "SELL"] as const).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setSide(s)}
                  className={cn(
                    "flex-1 rounded-md border py-1.5 text-xs font-semibold transition-colors",
                    side === s
                      ? s === "BUY"
                        ? "border-up bg-up/10 text-up"
                        : "border-down bg-down/10 text-down"
                      : "border-border text-muted-foreground hover:bg-muted",
                  )}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          {/* Quantity */}
          <div className="space-y-1.5">
            <Label htmlFor="qty" className="text-xs">
              Qty
            </Label>
            <Input
              id="qty"
              type="number"
              min={1}
              value={qty}
              onChange={(e) => setQty(Math.max(1, parseInt(e.target.value) || 1))}
              className="font-mono text-sm"
            />
          </div>

          {/* Price */}
          <div className="space-y-1.5">
            <Label htmlFor="price" className="text-xs">
              Price (₹)
            </Label>
            <Input
              id="price"
              type="number"
              min={0.01}
              step={0.05}
              placeholder="0.00"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="font-mono text-sm"
            />
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Estimated {side === "BUY" ? "cost" : "proceeds"}:{" "}
            <span className="font-mono font-semibold text-foreground">
              ₹{estimatedCost.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
            </span>
          </span>
          {summary.data && (
            <span>
              Cash:{" "}
              <span className="font-mono font-semibold text-foreground">
                ₹{summary.data.cash.toLocaleString("en-IN")}
              </span>
            </span>
          )}
        </div>

        <Button
          onClick={handleSubmit}
          disabled={!symbol || !parseFloat(price) || qty <= 0 || placeOrder.isPending}
          className={cn(
            "w-full font-semibold",
            side === "BUY"
              ? "bg-up hover:bg-up/90 text-up-foreground"
              : "bg-down hover:bg-down/90 text-down-foreground",
          )}
        >
          {placeOrder.isPending ? "Executing..." : `${side} (Paper)`}
        </Button>
      </CardContent>
    </Card>
  );
}

function PositionsTable() {
  const positions = usePaperPositions();

  if (positions.isLoading) return <Skeleton className="h-24 w-full rounded-lg" />;
  if (!positions.data?.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No open positions.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {positions.data.map((p) => (
        <div
          key={p.symbol}
          className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
        >
          <div>
            <span className="font-mono text-sm font-semibold">{p.symbol}</span>
            <span className="ml-2 text-xs text-muted-foreground">
              {p.qty} shares @ ₹{p.avg_cost.toLocaleString("en-IN")}
            </span>
          </div>
          <div className="text-right">
            <div className="font-mono text-xs">
              LTP ₹{p.ltp.toLocaleString("en-IN")}
            </div>
            <div
              className={cn(
                "font-mono text-xs font-semibold",
                p.unrealised_pnl >= 0 ? "text-up" : "text-down",
              )}
            >
              {p.unrealised_pnl >= 0 ? "+" : ""}
              ₹{p.unrealised_pnl.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
              <span className="ml-1 text-muted-foreground">
                ({p.pnl_pct >= 0 ? "+" : ""}
                {p.pnl_pct.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

function OrdersTable() {
  const orders = usePaperOrders();

  if (orders.isLoading) return <Skeleton className="h-24 w-full rounded-lg" />;
  if (!orders.data?.length) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        No orders yet.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {orders.data.map((o) => (
        <div
          key={o.id}
          className="flex items-center justify-between rounded-lg border border-border px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <span
              className={cn(
                "rounded-full px-2 py-0.5 font-mono text-[10px] font-semibold",
                o.type === "BUY"
                  ? "bg-up/10 text-up"
                  : "bg-down/10 text-down",
              )}
            >
              {o.type}
            </span>
            <div>
              <span className="font-mono text-sm font-semibold">{o.symbol}</span>
              <span className="ml-2 text-xs text-muted-foreground">
                {o.qty} × ₹{o.price.toLocaleString("en-IN")}
              </span>
            </div>
          </div>
          <div className="text-right">
            <div className="font-mono text-xs font-semibold">
              ₹{o.value.toLocaleString("en-IN", { maximumFractionDigits: 2 })}
            </div>
            <div className="font-mono text-[10px] text-muted-foreground">
              {o.id}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function PaperTradingPage() {
  const summary = usePaperSummary();
  const reset = useResetPaper();

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Paper Trading</h1>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => reset.mutate()}
          disabled={reset.isPending}
          className="text-xs text-muted-foreground"
        >
          <RefreshCcw className="mr-1.5 size-3" />
          Reset
        </Button>
      </div>

      {/* ── Summary stat cards ── */}
      {summary.isLoading ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
      ) : summary.data ? (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard
            label="Cash"
            value={`₹${summary.data.cash.toLocaleString("en-IN")}`}
            icon={<Banknote className="size-3" />}
          />
          <StatCard
            label="Positions"
            value={String(summary.data.positions_count)}
            icon={<Package className="size-3" />}
            tone="text-ai"
          />
          <StatCard
            label="Orders"
            value={String(summary.data.orders_count)}
            icon={<History className="size-3" />}
            tone="text-gold"
          />
          <StatCard
            label="Realised P&L"
            value={`${summary.data.pnl >= 0 ? "+" : ""}₹${summary.data.pnl.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`}
            icon={<BarChart3 className="size-3" />}
            tone={summary.data.pnl >= 0 ? "text-up" : "text-down"}
          />
        </div>
      ) : null}

      {/* ── Order ticket ── */}
      <OrderTicket />

      {/* ── Positions / Orders tabs ── */}
      <Tabs defaultValue="positions">
        <TabsList className="w-full">
          <TabsTrigger value="positions" className="flex-1">
            <Package className="mr-1.5 size-3.5" />
            Positions
          </TabsTrigger>
          <TabsTrigger value="orders" className="flex-1">
            <History className="mr-1.5 size-3.5" />
            Orders
          </TabsTrigger>
        </TabsList>
        <TabsContent value="positions">
          <PositionsTable />
        </TabsContent>
        <TabsContent value="orders">
          <OrdersTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
