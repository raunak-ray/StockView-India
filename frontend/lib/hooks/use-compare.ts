"use client";

import { useQuery } from "@tanstack/react-query";
import { getCompare } from "@/lib/api/compare";

const STALE = 5 * 60 * 1000;

export function useCompare(symbols: string[], period: string) {
  return useQuery({
    queryKey: ["compare", symbols.sort().join(","), period],
    queryFn: () => getCompare(symbols, period),
    enabled: symbols.length >= 2,
    staleTime: STALE,
  });
}
