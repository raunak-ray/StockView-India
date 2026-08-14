"use client";

import { ArrowDownRight, ArrowUpRight, Wallet } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useMe } from "@/lib/hooks/use-auth";

export default function AppPage() {
  const { data: user } = useMe();

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold">
            Welcome back, {user?.username}
          </h1>
          <p className="text-sm text-muted-foreground">
            Market overview — NIFTY 50, movers and your portfolio at a glance.
          </p>
        </div>
        <Button>+ Watchlist</Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "NIFTY 50", value: "24,551.10", delta: "+0.84%", up: true },
          { label: "SENSEX", value: "80,428.70", delta: "+0.91%", up: true },
          { label: "NIFTY BANK", value: "52,311.35", delta: "+1.12%", up: true },
          { label: "NIFTY IT", value: "38,204.62", delta: "-0.28%", up: false },
        ].map((c) => (
          <Card key={c.label}>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-normal text-muted-foreground">
                {c.label}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="font-mono text-xl font-semibold">{c.value}</p>
              <p
                className={`mt-1 flex items-center gap-1 text-sm ${
                  c.up ? "text-emerald-500" : "text-red-500"
                }`}
              >
                {c.up ? (
                  <ArrowUpRight className="size-4" />
                ) : (
                  <ArrowDownRight className="size-4" />
                )}
                {c.delta}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Wallet className="size-4" /> Paper portfolio
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-between">
          <div>
            <p className="font-mono text-2xl font-semibold">₹1,00,000.00</p>
            <p className="text-sm text-muted-foreground">
              Cash balance — paper trading starts here
            </p>
          </div>
          <Badge variant="secondary">0 open positions</Badge>
        </CardContent>
      </Card>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
          <p className="text-sm font-medium">Modules land here next</p>
          <p className="max-w-md text-sm text-muted-foreground">
            Stock terminal, markets, sectors, backtest and paper trading follow
            from the migration plan (plan/02 route map).
          </p>
        </CardContent>
      </Card>
    </div>
  );
}