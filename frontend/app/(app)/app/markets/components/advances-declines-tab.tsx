"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAdvancesDeclines } from "@/lib/hooks/use-nse";
import { cn } from "@/lib/utils";

function StatTile({
  label,
  value,
  tone,
}: {
  label: string;
  value: number | undefined;
  tone: "up" | "down" | "flat";
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-1 p-6 text-center">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        {value === undefined ? (
          <Skeleton className="mt-1 h-9 w-20" />
        ) : (
          <span
            className={cn(
              "font-mono text-3xl font-semibold",
              tone === "up" && "text-up",
              tone === "down" && "text-down",
            )}
          >
            {value}
          </span>
        )}
      </CardContent>
    </Card>
  );
}

/** Advances vs declines for Nifty 50 with an adv/dec ratio bar. */
export function AdvancesDeclinesTab() {
  const { data, isLoading, isError, refetch } = useAdvancesDeclines();

  if (isError) {
    return (
      <div className="rounded-xl border border-dashed border-border py-16 text-center">
        <p className="text-sm font-medium">Breadth feed unavailable right now</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="mt-2 text-sm text-primary underline-offset-4 hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  const advances = data?.advances ?? 0;
  const declines = data?.declines ?? 0;
  const unchanged = data?.unchanged ?? 0;
  const total = Math.max(advances + declines + unchanged, 1);
  const advPct = (advances / total) * 100;
  const unchPct = (unchanged / total) * 100;

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label="Advancing" value={isLoading ? undefined : advances} tone="up" />
        <StatTile label="Declining" value={isLoading ? undefined : declines} tone="down" />
        <StatTile label="Unchanged" value={isLoading ? undefined : unchanged} tone="flat" />
      </div>

      {/* Ratio bar — teal/red split with unchanged in the middle */}
      <Card>
        <CardContent className="space-y-2 p-5">
          <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-up transition-all duration-300" style={{ width: `${advPct}%` }} />
            <div className="h-full bg-muted-foreground/40" style={{ width: `${unchPct}%` }} />
            <div className="h-full bg-down" style={{ width: `${100 - advPct - unchPct}%` }} />
          </div>
          <div className="flex justify-between font-mono text-xs text-muted-foreground">
            <span className="flex items-center gap-1 text-up">
              <ArrowUpRight className="size-3.5" />
              {advPct.toFixed(0)}% advancing
            </span>
            <span>
              A/D ratio {(advances / Math.max(declines, 1)).toFixed(2)}
            </span>
            <span className="flex items-center gap-1 text-down">
              {declines} declining
              <ArrowDownRight className="size-3.5" />
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
