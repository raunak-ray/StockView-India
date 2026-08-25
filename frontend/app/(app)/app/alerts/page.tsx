"use client";

import { useState } from "react";
import { Bell, BellOff, Plus, Trash2, X } from "lucide-react";

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
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useAlerts, useCreateAlert, useDeleteAlert, useClearAlerts } from "@/lib/hooks/use-alerts";
import { cn } from "@/lib/utils";

export default function AlertsPage() {
  const { data, isLoading } = useAlerts();
  const createAlert = useCreateAlert();
  const deleteAlert = useDeleteAlert();
  const clearAlerts = useClearAlerts();

  const [symbol, setSymbol] = useState("RELIANCE.NS");
  const [price, setPrice] = useState("");
  const [condition, setCondition] = useState("above");

  const active = data?.active ?? [];
  const fired = data?.fired ?? [];

  const handleCreate = () => {
    if (!symbol.trim() || !price) return;
    createAlert.mutate(
      {
        symbol: symbol.trim().toUpperCase(),
        price: Number(price),
        condition,
        label: condition === "above" ? "📈 Crosses Above" : "📉 Crosses Below",
      },
      { onSuccess: () => setPrice("") },
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <h1 className="text-2xl font-semibold">Price Alerts</h1>

      {/* ── Create form ── */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bell className="size-4 text-gold" />
            Set alert
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div className="col-span-2 space-y-1.5">
              <Label htmlFor="al-symbol" className="text-xs">Symbol</Label>
              <Input
                id="al-symbol"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value.toUpperCase())}
                className="font-mono text-sm"
                placeholder="RELIANCE.NS"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="al-price" className="text-xs">Price (₹)</Label>
              <Input
                id="al-price"
                type="number"
                min={0.01}
                step={0.5}
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                className="font-mono text-sm"
                placeholder="2800.00"
              />
            </div>

            <div className="space-y-1.5">
              <Label className="text-xs">Condition</Label>
              <Select value={condition} onValueChange={setCondition}>
                <SelectTrigger className="w-full font-mono text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="above">📈 Crosses Above</SelectItem>
                  <SelectItem value="below">📉 Crosses Below</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            onClick={handleCreate}
            disabled={createAlert.isPending || !symbol.trim() || !price}
            className="w-full bg-gold text-gold-foreground hover:bg-gold/90 sm:w-auto"
          >
            <Plus className="mr-1 size-4" />
            Add Alert
          </Button>
        </CardContent>
      </Card>

      {/* ── Loading ── */}
      {isLoading && (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-lg" />
          ))}
        </div>
      )}

      {/* ── Active alerts ── */}
      {!isLoading && active.length === 0 && fired.length === 0 && (
        <div className="py-12 text-center text-sm text-muted-foreground">
          No alerts set. Add one above.
        </div>
      )}

      {!isLoading && active.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Watching ({active.length})
            </h2>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-muted-foreground"
              onClick={() => clearAlerts.mutate(false)}
              disabled={clearAlerts.isPending}
            >
              <Trash2 className="mr-1 size-3" />
              Clear all
            </Button>
          </div>

          {active.map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
            >
              <div className="flex items-center gap-4">
                <span className="font-mono text-sm font-bold">{a.symbol}</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                    a.condition === "above"
                      ? "bg-up/10 text-up"
                      : "bg-down/10 text-down",
                  )}
                >
                  {a.condition === "above" ? "ABOVE" : "BELOW"}
                </span>
                <span className="font-mono text-base font-bold text-gold">
                  ₹{a.price.toLocaleString("en-IN")}
                </span>
                <span className="text-[10px] text-muted-foreground">
                  Set {a.created}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="size-8 p-0 text-muted-foreground hover:text-down"
                onClick={() => deleteAlert.mutate(a.id)}
                disabled={deleteAlert.isPending}
              >
                <X className="size-4" />
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* ── Fired alerts ── */}
      {!isLoading && fired.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-down">
              Triggered ({fired.length})
            </h2>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-muted-foreground"
              onClick={() => clearAlerts.mutate(true)}
              disabled={clearAlerts.isPending}
            >
              <Trash2 className="mr-1 size-3" />
              Clear triggered
            </Button>
          </div>

          {fired.map((a) => (
            <div
              key={a.id}
              className="flex items-center justify-between rounded-lg border border-down/20 bg-down/5 px-4 py-3"
            >
              <div className="flex items-center gap-4">
                <BellOff className="size-4 text-down" />
                <span className="font-mono text-sm font-bold">{a.symbol}</span>
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                    a.condition === "above"
                      ? "bg-up/10 text-up"
                      : "bg-down/10 text-down",
                  )}
                >
                  {a.condition === "above" ? "ABOVE" : "BELOW"}
                </span>
                <span className="font-mono text-base font-bold text-down">
                  ₹{a.price.toLocaleString("en-IN")}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="size-8 p-0 text-muted-foreground hover:text-down"
                onClick={() => deleteAlert.mutate(a.id)}
                disabled={deleteAlert.isPending}
              >
                <X className="size-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
