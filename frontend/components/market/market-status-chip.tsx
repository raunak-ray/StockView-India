"use client";

import { useSyncExternalStore } from "react";

import { isMarketOpen } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function subscribe(onChange: () => void) {
  const t = setInterval(onChange, 30_000);
  return () => clearInterval(t);
}

// Server snapshot avoids hydration mismatches; React re-reads after mount.
const getSnapshot = () => isMarketOpen();
const getServerSnapshot = () => false;

/**
 * `● LIVE` when NSE is trading (Mon–Fri 09:15–15:30 IST), `○ CLOSED` otherwise.
 * Plan/03 §4 chip spec — the only pulsing element in the UI.
 */
export function MarketStatusChip({ className }: { className?: string }) {
  const open = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-[11px] font-semibold tracking-wide",
        open
          ? "border-up/30 bg-up/10 text-up"
          : "border-border bg-muted text-muted-foreground",
        className,
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          open ? "animate-pulse bg-up" : "bg-muted-foreground",
        )}
      />
      {open ? "LIVE" : "CLOSED"}
    </span>
  );
}
