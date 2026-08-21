"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
  type WatchlistItem,
} from "@/lib/api/portfolio";

export const watchlistQueryKey = ["portfolio", "watchlist"] as const;

export function useWatchlist() {
  return useQuery({
    queryKey: watchlistQueryKey,
    queryFn: getWatchlist,
    staleTime: 30 * 1000,
  });
}

export function useWatchlistTickers(): Set<string> {
  const { data } = useWatchlist();
  return new Set((data?.items ?? []).map((i: WatchlistItem) => i.ticker));
}

export function useAddToWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: addToWatchlist,
    onSuccess: (res) => {
      toast.success(res.message);
      qc.invalidateQueries({ queryKey: watchlistQueryKey });
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Could not add to watchlist"),
  });
}

export function useRemoveFromWatchlist() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: removeFromWatchlist,
    onMutate: async (ticker: string) => {
      await qc.cancelQueries({ queryKey: watchlistQueryKey });
      const previous = qc.getQueryData<{ count: number; items: WatchlistItem[] }>(
        watchlistQueryKey,
      );
      qc.setQueryData<{ count: number; items: WatchlistItem[] }>(
        watchlistQueryKey,
        (old) =>
          old
            ? {
                count: old.count - 1,
                items: old.items.filter((i) => i.ticker !== ticker),
              }
            : old,
      );
      return { previous };
    },
    onSuccess: (res) => toast.success(res.message),
    onError: (_e, _ticker, context) => {
      if (context?.previous) qc.setQueryData(watchlistQueryKey, context.previous);
      toast.error("Could not remove from watchlist");
    },
    onSettled: () => qc.invalidateQueries({ queryKey: watchlistQueryKey }),
  });
}
