"use client";

import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { useAdvancesDeclines } from "@/lib/hooks/use-nse";
import { cn } from "@/lib/utils";

function StatTile({
  label,
  value,
  tone,
  icon: Icon,
  tip,
}: {
  label: string;
  value: number | undefined;
  tone: "up" | "down" | "flat";
  icon: typeof ArrowUpRight;
  tip: string;
}) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center gap-1.5 p-6 text-center">
        <span className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          <Icon
            className={cn(
              "size-4",
              tone === "up" && "text-up",
              tone === "down" && "text-down",
              tone === "flat" && "text-muted-foreground",
            )}
          />
          {label}
          <InfoTip label={`What is ${label}?`}>{tip}</InfoTip>
        </span>
        {value === undefined ? (
          <span className="mt-1 font-mono text-3xl text-muted-foreground/40">—</span>
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

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
        <Loader variant="dots" size={28} label="Loading market breadth" />
        <p className="text-sm">Loading market breadth…</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-xl border border-dashed border-border py-16 text-center">
        <p className="text-sm font-medium">Breadth unavailable right now</p>
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
        <StatTile
          label="Advancing"
          value={advances}
          tone="up"
          icon={ArrowUpRight}
          tip="Nifty 50 members whose price is higher than yesterday's close."
        />
        <StatTile
          label="Declining"
          value={declines}
          tone="down"
          icon={ArrowDownRight}
          tip="Nifty 50 members whose price is lower than yesterday's close."
        />
        <StatTile
          label="Unchanged"
          value={unchanged}
          tone="flat"
          icon={Minus}
          tip="Members trading exactly at yesterday's close."
        />
      </div>

      {/* Ratio bar — emerald/red split with unchanged in the middle */}
      <Card>
        <CardContent className="space-y-2 p-5">
          <div className="flex h-3 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-up transition-all duration-300" style={{ width: `${advPct}%` }} />
            <div className="h-full bg-muted-foreground/40" style={{ width: `${unchPct}%` }} />
            <div className="h-full bg-down" style={{ width: `${100 - advPct - unchPct}%` }} />
          </div>
          <div className="flex items-center justify-between font-mono text-xs text-muted-foreground">
            <span className="flex items-center gap-1 text-up">
              <ArrowUpRight className="size-3.5" />
              {advPct.toFixed(0)}% advancing
            </span>
            <span className="flex items-center gap-1">
              <span>A/D ratio {(advances / Math.max(declines, 1)).toFixed(2)}</span>
              <InfoTip label="What is the A/D ratio?">
                Advances divided by declines. Well above 1 = broad strength
                (most stocks rising); well below 1 = broad weakness. This is
                called market breadth.
              </InfoTip>
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
