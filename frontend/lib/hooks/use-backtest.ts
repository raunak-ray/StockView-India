"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import {
  getStrategies,
  runBacktest,
  type BacktestRequest,
} from "@/lib/api/backtest";

const STALE = 60 * 60 * 1000;

export function useStrategies() {
  return useQuery({
    queryKey: ["backtest", "strategies"],
    queryFn: getStrategies,
    staleTime: STALE,
  });
}

export function useRunBacktest() {
  return useMutation({
    mutationFn: (req: BacktestRequest) => runBacktest(req),
  });
}
