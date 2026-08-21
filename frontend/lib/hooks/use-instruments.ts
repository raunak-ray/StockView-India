"use client";

import { useQuery } from "@tanstack/react-query";

import { searchInstruments, type Instrument } from "@/lib/api/instruments";

export function useInstrumentSearch(query: string, limit = 20) {
  const trimmed = query.trim();
  return useQuery({
    queryKey: ["instruments", "search", trimmed, limit],
    queryFn: () => searchInstruments(trimmed, limit),
    enabled: trimmed.length > 0,
    staleTime: 5 * 60 * 1000, // instrument master is a static asset
  });
}

export type { Instrument };
