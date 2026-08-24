"use client";

import { useQuery } from "@tanstack/react-query";

import { getIndicators, getSupportResistance } from "@/lib/api/analytics";
import { getSmc, type SmcResponse } from "@/lib/api/smc";
import { getSignal, getFusion, type FusionResponse } from "@/lib/api/signals";
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

export function useSmc(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["smc", symbol, interval, period],
    queryFn: (): Promise<SmcResponse> => getSmc(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}

export function useFusion(symbol: string, interval: Interval, period: Period) {
  return useQuery({
    queryKey: ["fusion", symbol, interval, period],
    queryFn: (): Promise<FusionResponse> => getFusion(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: STALE,
  });
}
