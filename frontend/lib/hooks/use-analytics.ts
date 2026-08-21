"use client";

import { useQuery } from "@tanstack/react-query";

import { getIndicators, getSupportResistance } from "@/lib/api/analytics";
import { getSignal } from "@/lib/api/signals";
import type { Interval, Period } from "@/lib/api/market";

const STALE = 5 * 60 * 1000; // backend history TTL parity: 300s

export function useIndicators(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["analytics", "indicators", symbol, interval, period],
    queryFn: () => getIndicators(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}

export function useSupportResistance(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["analytics", "support-resistance", symbol, interval, period],
    queryFn: () => getSupportResistance(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}

export function useSignal(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["signals", symbol, interval, period],
    queryFn: () => getSignal(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}
