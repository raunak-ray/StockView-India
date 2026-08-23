"use client";

import { useQuery } from "@tanstack/react-query";

import type { Interval, Period } from "@/lib/api/market";
import { getNews, getSentimentScore } from "@/lib/api/sentiment";

const STALE = 5 * 60 * 1000; // backend news TTL parity: 600s (round to 5m)

export function useSentimentScore(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
) {
  return useQuery({
    queryKey: ["sentiment", "score", symbol, interval, period],
    queryFn: () => getSentimentScore(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}

export function useNews(symbol: string, maxItems = 8) {
  return useQuery({
    queryKey: ["sentiment", "news", symbol, maxItems],
    queryFn: () => getNews(symbol, maxItems),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}
