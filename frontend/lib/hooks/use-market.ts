"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getGainersLosers,
  getHistory,
  getInfo,
  getMarketSummary,
  getQuote,
  type Interval,
  type Period,
} from "@/lib/api/market";

/** Live quote polling — parity with the auto-refresh toggle (app.py:1021).
 *  intervalSec is chosen by the caller (see stock page constants). */
export function useQuote(symbol: string, intervalSec: number = 10) {
  return useQuery({
    queryKey: ["market", "quote", symbol],
    queryFn: () => getQuote(symbol),
    enabled: symbol.length > 0,
    refetchInterval: intervalSec * 1000,
    staleTime: Math.min(intervalSec, 10) * 1000 - 1000,
    retry: (failureCount, error) => {
      const status = (error as { status?: number }).status;
      if (status === 404 || status === 401) return false;
      return failureCount < 2;
    },
  });
}

export function useStockInfo(symbol: string) {
  return useQuery({
    queryKey: ["market", "info", symbol],
    queryFn: () => getInfo(symbol),
    enabled: symbol.length > 0,
    staleTime: 10 * 60 * 1000, // backend TTL parity: info cached 600s
  });
}

export function useMarketSummary(intervalSec: number = 60) {
  return useQuery({
    queryKey: ["market", "summary"],
    queryFn: getMarketSummary,
    refetchInterval: intervalSec * 1000, // backend TTL parity: 60s
    staleTime: 55 * 1000,
  });
}

export function useGainersLosers(intervalSec: number = 60) {
  return useQuery({
    queryKey: ["market", "gainers-losers"],
    queryFn: getGainersLosers,
    refetchInterval: intervalSec * 1000, // backend TTL parity: 60s
    staleTime: 55 * 1000,
  });
}

export function useHistory(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["market", "history", symbol, interval, period],
    queryFn: () => getHistory(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: 5 * 60 * 1000, // backend TTL parity: history cached 300s
    retry: (failureCount, error) => {
      const status = (error as { status?: number }).status;
      if (status === 404 || status === 401) return false;
      return failureCount < 2;
    },
  });
}
