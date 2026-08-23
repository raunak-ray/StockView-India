"use client";

import { useQuery } from "@tanstack/react-query";

import {
  getAdvancesDeclines,
  getFiiDii,
  getNseQuote,
  getOptionChain,
} from "@/lib/api/nse";
import { getSectorPerformance } from "@/lib/api/market";

/** NSE quote — 60s polling parity (backend TTL 60s, app.py:1274). */
export function useNseQuote(symbol: string | null) {
  return useQuery({
    queryKey: ["nse", "quote", symbol],
    queryFn: () => getNseQuote(symbol as string),
    enabled: Boolean(symbol),
    refetchInterval: 60 * 1000,
    staleTime: 55 * 1000,
  });
}

/** FII/DII — backend caches 300s; refetch on window focus is enough. */
export function useFiiDii() {
  return useQuery({
    queryKey: ["nse", "fii-dii"],
    queryFn: getFiiDii,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  });
}

export function useAdvancesDeclines() {
  return useQuery({
    queryKey: ["nse", "adv-dec"],
    queryFn: getAdvancesDeclines,
    staleTime: 2 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });
}

export function useOptionChain(symbol: string | null) {
  return useQuery({
    queryKey: ["nse", "option-chain", symbol],
    queryFn: () => getOptionChain(symbol as string),
    enabled: Boolean(symbol),
    staleTime: 2 * 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
  });
}

export function useSectorPerformance() {
  return useQuery({
    queryKey: ["market", "sectors"],
    queryFn: getSectorPerformance,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000,
  });
}
