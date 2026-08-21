"use client";

import { ArrowDownRight, ArrowUpRight, RefreshCw } from "lucide-react";
import { motion } from "motion/react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useMarketSummary } from "@/lib/hooks/use-market";
import type { IndexQuote } from "@/lib/api/market";
import {
  formatNumber,
  formatPct,
  formatSigned,
  toneTextClass,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function IndexCard({ index, i }: { index: IndexQuote; i: number }) {
  const up = index.change_pct >= 0;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: i * 0.05, ease: "easeOut" }}
    >
      <Card className="transition-colors hover:border-primary/40">
        <CardContent className="space-y-1 p-4">
          <p className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
            {index.name}
          </p>
          <p className="font-mono text-xl font-semibold">
            {formatNumber(index.price)}
          </p>
          <p
            className={cn(
              "flex items-center gap-1 font-mono text-xs",
              toneTextClass[up ? "up" : "down"],
            )}
          >
            {up ? (
              <ArrowUpRight className="size-3.5" />
            ) : (
              <ArrowDownRight className="size-3.5" />
            )}
            {formatPct(index.change_pct)}
            <span className="text-muted-foreground">
              ({formatSigned(index.change)})
            </span>
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function IndexCards() {
  const { data, isLoading, isError, refetch, isRefetching } = useMarketSummary();

  if (isLoading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="space-y-2 p-4">
              <Skeleton className="h-3 w-16" />
              <Skeleton className="h-6 w-24" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (isError || !data?.indices.length) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 py-8 text-center">
          <p className="text-sm text-muted-foreground">
            Live feed unavailable right now.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className={cn("size-4", isRefetching && "animate-spin")} />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {data.indices.map((index, i) => (
        <IndexCard key={index.symbol} index={index} i={i} />
      ))}
    </div>
  );
}
