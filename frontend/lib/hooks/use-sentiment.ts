"use client";

import { useQuery } from "@tanstack/react-query";

import type { Interval, Period } from "@/lib/api/market";
import { getSentimentInsight } from "@/lib/api/sentiment";

const STALE = 5 * 60 * 1000; // backend news TTL parity: 600s (round to 5m)

/**
 * News sentiment for a stock.
 *
 * One call for everything the card shows: the score, the period breakdown, the
 * strongest stories and the recent articles. The response carries
 * `isStoredData`, so the UI can say whether the numbers came from our archive
 * or from a live scrape.
 */
export function useSentimentInsight(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
) {
  return useQuery({
    queryKey: ["sentiment", "insight", symbol, interval, period],
    queryFn: () => getSentimentInsight(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}
