"use client";

import { Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  useAddToWatchlist,
  useRemoveFromWatchlist,
  useWatchlistTickers,
} from "@/lib/hooks/use-watchlist";
import { cn } from "@/lib/utils";

/** Watchlist star: filled gold when starred, outline otherwise. */
export function WatchlistStar({ ticker }: { ticker: string }) {
  const tickers = useWatchlistTickers();
  const add = useAddToWatchlist();
  const remove = useRemoveFromWatchlist();

  const starred = tickers.has(ticker);
  const busy = add.isPending || remove.isPending;

  return (
    <Button
      variant="outline"
      size="icon"
      disabled={busy}
      aria-label={starred ? `Remove ${ticker} from watchlist` : `Add ${ticker} to watchlist`}
      aria-pressed={starred}
      title={starred ? "Remove from watchlist" : "Add to watchlist"}
      onClick={() => (starred ? remove.mutateAsync(ticker) : add.mutateAsync(ticker))}
    >
      <Star
        className={cn(
          "size-4 transition-colors",
          starred ? "fill-gold text-gold" : "text-muted-foreground",
        )}
      />
    </Button>
  );
}
