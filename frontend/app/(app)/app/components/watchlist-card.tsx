"use client";

import Link from "next/link";
import { ArrowDownRight, ArrowUpRight, Star, X } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuote } from "@/lib/hooks/use-market";
import {
  useRemoveFromWatchlist,
  useWatchlist,
} from "@/lib/hooks/use-watchlist";
import type { WatchlistItem } from "@/lib/api/portfolio";
import {
  formatINR,
  formatPct,
  toneBadgeClass,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function WatchlistRow({ item }: { item: WatchlistItem }) {
  const quote = useQuote(item.ticker, 60);
  const remove = useRemoveFromWatchlist();
  const changePct = quote.data?.change_pct ?? null;
  const up = (changePct ?? 0) >= 0;

  return (
    <div className="group flex items-center justify-between rounded-lg px-2 py-1.5 transition-colors hover:bg-muted">
      <Link
        href={`/app/stocks/${encodeURIComponent(item.ticker)}`}
        className="flex min-w-0 flex-1 items-center gap-3"
      >
        <Star className="size-3.5 shrink-0 fill-gold text-gold" />
        <span className="truncate font-mono text-sm font-medium">
          {item.ticker}
        </span>
      </Link>
      <div className="flex shrink-0 items-center gap-3">
        <span className="font-mono text-xs text-muted-foreground">
          {quote.isLoading ? "…" : formatINR(quote.data?.price)}
        </span>
        {changePct !== null && (
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
            {formatPct(changePct)}
          </span>
        )}
        <Button
          variant="ghost"
          size="icon"
          className="size-7 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
          disabled={remove.isPending}
          aria-label={`Remove ${item.ticker} from watchlist`}
          onClick={() => remove.mutateAsync(item.ticker)}
        >
          <X className="size-4 text-muted-foreground" />
        </Button>
      </div>
    </div>
  );
}

export function WatchlistCard() {
  const { data, isLoading, isError, refetch } = useWatchlist();

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm">
          <span className="flex items-center gap-2">
            <Star className="size-4 text-gold" /> My watchlist
          </span>
          {data && data.count > 0 && (
            <span className="font-mono text-xs font-normal text-muted-foreground">
              {data.count} {data.count === 1 ? "instrument" : "instruments"}
            </span>
          )}
        </CardTitle>
        <CardDescription>
          Starred instruments refresh live every minute.
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-1.5 py-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full rounded-lg" />
            ))}
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-border py-8 text-center">
            <p className="text-sm text-muted-foreground">
              Could not load your watchlist.
            </p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              Retry
            </Button>
          </div>
        ) : data && data.count > 0 ? (
          <div className="-mx-2 space-y-0.5">
            {data.items.map((item) => (
              <WatchlistRow key={item.ticker} item={item} />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1.5 rounded-lg border border-dashed border-border py-10 text-center">
            <p className="text-sm font-medium">Your watchlist is empty</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Open any stock from the search bar (⌘K) and hit the star to add it here.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
