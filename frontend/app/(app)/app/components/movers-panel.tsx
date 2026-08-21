"use client";

import Link from "next/link";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useGainersLosers } from "@/lib/hooks/use-market";
import type { Mover } from "@/lib/api/market";
import {
  formatINR,
  formatPct,
  toneBadgeClass,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function MoverRow({ mover }: { mover: Mover }) {
  const up = mover.change_pct >= 0;
  return (
    <Link
      href={`/app/stocks/${encodeURIComponent(mover.symbol + ".NS")}`}
      className="flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-muted"
    >
      <span className="font-mono text-sm font-medium">{mover.symbol}</span>
      <span className="flex items-center gap-3">
        <span className="font-mono text-xs text-muted-foreground">
          {formatINR(mover.price)}
        </span>
        <span
          className={cn(
            "inline-flex min-w-16 items-center justify-end gap-0.5 rounded-full border px-2 py-0.5 font-mono text-[11px] font-semibold",
            toneBadgeClass[up ? "up" : "down"],
          )}
        >
          {up ? (
            <ArrowUpRight className="size-3" />
          ) : (
            <ArrowDownRight className="size-3" />
          )}
          {formatPct(mover.change_pct)}
        </span>
      </span>
    </Link>
  );
}

function MoverSkeleton() {
  return (
    <div className="space-y-2 p-2">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center justify-between">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-24" />
        </div>
      ))}
    </div>
  );
}

export function MoversPanel() {
  const { data, isLoading, isError } = useGainersLosers();

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Market movers — NSE large caps</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-6 sm:grid-cols-2">
        <section aria-label="Top gainers">
          <p className="mb-2 flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-up">
            <ArrowUpRight className="size-3.5" /> Top gainers
          </p>
          {isLoading ? (
            <MoverSkeleton />
          ) : data?.gainers.length ? (
            <div className="space-y-0.5">
              {data.gainers.map((m) => (
                <MoverRow key={m.symbol} mover={m} />
              ))}
            </div>
          ) : (
            <p className="px-2 py-4 text-sm text-muted-foreground">
              {isError ? "Feed unavailable right now." : "No movers today."}
            </p>
          )}
        </section>
        <section aria-label="Top losers">
          <p className="mb-2 flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-down">
            <ArrowDownRight className="size-3.5" /> Top losers
          </p>
          {isLoading ? (
            <MoverSkeleton />
          ) : data?.losers.length ? (
            <div className="space-y-0.5">
              {data.losers.map((m) => (
                <MoverRow key={m.symbol} mover={m} />
              ))}
            </div>
          ) : (
            <p className="px-2 py-4 text-sm text-muted-foreground">
              {isError ? "Feed unavailable right now." : "No movers today."}
            </p>
          )}
        </section>
      </CardContent>
    </Card>
  );
}
