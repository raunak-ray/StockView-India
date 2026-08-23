"use client";

import { AlertTriangle } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Sparkline } from "@/components/charts/sparkline";
import { useFiiDii } from "@/lib/hooks/use-nse";
import { formatSigned } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function FlowCard({
  title,
  net,
  series,
}: {
  title: string;
  net: number | undefined;
  series: number[];
}) {
  const up = (net ?? 0) >= 0;
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {net === undefined ? (
          <Skeleton className="h-8 w-28" />
        ) : (
          <p
            className={cn(
              "font-mono text-xl font-semibold",
              up ? "text-up" : "text-down",
            )}
          >
            {formatSigned(net)} ₹Cr
          </p>
        )}
        <Sparkline values={series} />
      </CardContent>
    </Card>
  );
}

/** FII / DII cash-market flows — cards, trend sparkline and session table. */
export function FiiDiiTab() {
  const { data, isLoading, isError } = useFiiDii();
  const rows = data?.rows ?? [];
  const latest = rows[0];
  // Rows arrive newest-first; the trend line reads left→right chronologically.
  const fiiSeries = [...rows].reverse().map((r) => r.fii_net);
  const diiSeries = [...rows].reverse().map((r) => r.dii_net);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <Skeleton className="h-36 rounded-xl" />
          <Skeleton className="h-36 rounded-xl" />
        </div>
        <Skeleton className="h-64 rounded-xl" />
      </div>
    );
  }

  if (isError || rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border py-16 text-center">
        <p className="text-sm font-medium">FII/DII feed unavailable right now</p>
        <p className="mt-1 text-sm text-muted-foreground">
          All data sources failed — try again shortly.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data?.source === "static" && (
        <div className="flex items-start gap-2 rounded-lg border border-gold/30 bg-gold/10 px-3 py-2 text-xs text-gold">
          <AlertTriangle className="mt-0.5 size-4 shrink-0" />
          Live sources unreachable — showing last published reference data.
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <FlowCard
          title="FII net (₹ Crore)"
          net={latest?.fii_net}
          series={fiiSeries}
        />
        <FlowCard
          title="DII net (₹ Crore)"
          net={latest?.dii_net}
          series={diiSeries}
        />
      </div>

      {/* Session table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Recent sessions</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="px-4 py-2 text-left">Date</th>
                <th className="px-4 py-2 text-right">FII Buy</th>
                <th className="px-4 py-2 text-right">FII Sell</th>
                <th className="px-4 py-2 text-right">FII Net</th>
                <th className="px-4 py-2 text-right">DII Buy</th>
                <th className="px-4 py-2 text-right">DII Sell</th>
                <th className="px-4 py-2 text-right">DII Net</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr
                  key={r.date}
                  className="border-b border-border/50 transition-colors hover:bg-muted/40"
                >
                  <td className="px-4 py-2 font-mono text-xs">{r.date}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{formatSigned(r.fii_buy)}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{formatSigned(r.fii_sell)}</td>
                  <td className={cn(
                    "px-4 py-2 text-right font-mono text-xs font-semibold",
                    r.fii_net >= 0 ? "text-up" : "text-down",
                  )}>
                    {formatSigned(r.fii_net)}
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{formatSigned(r.dii_buy)}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{formatSigned(r.dii_sell)}</td>
                  <td className={cn(
                    "px-4 py-2 text-right font-mono text-xs font-semibold",
                    r.dii_net >= 0 ? "text-up" : "text-down",
                  )}>
                    {formatSigned(r.dii_net)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
