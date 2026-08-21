"use client";

import { IndexCards } from "./components/index-cards";
import { MoversPanel } from "./components/movers-panel";
import { WatchlistCard } from "./components/watchlist-card";
import { MarketStatusChip } from "@/components/market/market-status-chip";
import { useMe } from "@/lib/hooks/use-auth";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

export default function AppPage() {
  const { data: user } = useMe();

  const dateLine = new Date().toLocaleDateString("en-IN", {
    weekday: "short",
    day: "numeric",
    month: "short",
    year: "numeric",
  });

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">
            {greeting()}, {user?.username}
          </h1>
          <p className="mt-0.5 flex items-center gap-2 text-sm text-muted-foreground">
            {dateLine}
            <MarketStatusChip />
          </p>
        </div>
      </div>

      <section aria-label="Market snapshot" className="space-y-3">
        <h2 className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          Market snapshot
        </h2>
        <IndexCards />
      </section>

      <MoversPanel />

      <WatchlistCard />
    </div>
  );
}
