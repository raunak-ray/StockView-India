"use client";

import { useQuery } from "@tanstack/react-query";

import type { Interval, Period } from "@/lib/api/market";
import { getLstmForecast, getMlCapabilities, getMlJob, startMlPredict } from "@/lib/api/ml";

const CAPABILITIES_STALE = 60 * 60 * 1000; // flags change only on reinstall
const RESULT_STALE = 10 * 60 * 1000; // backend caches predictions ~15 min

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

/**
 * Start a prediction job, then poll until it finishes. The whole
 * orchestration lives in one queryFn so React Query caches the final
 * result and "loading" means "training in progress".
 */
async function predictWithJob(symbol: string) {
  const job = await startMlPredict(symbol);
  for (let i = 0; i < 60; i++) {
    const status = await getMlJob(job.job_id);
    if (status.status === "done" && status.result) return status.result;
    if (status.status === "error") {
      throw new Error(status.error ?? "Prediction failed");
    }
    await sleep(2000);
  }
  throw new Error("Prediction timed out — try again");
}

export function useMlPredict(symbol: string, enabled = true) {
  return useQuery({
    queryKey: ["ml", "predict", symbol],
    queryFn: () => predictWithJob(symbol),
    enabled: enabled && symbol.length > 0,
    staleTime: RESULT_STALE,
    retry: 1,
  });
}

export function useMlCapabilities() {
  return useQuery({
    queryKey: ["ml", "capabilities"],
    queryFn: getMlCapabilities,
    staleTime: CAPABILITIES_STALE,
  });
}

export function useLstmForecast(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
) {
  return useQuery({
    queryKey: ["ml", "lstm-forecast", symbol, interval, period],
    queryFn: () => getLstmForecast(symbol, interval, period),
    enabled: symbol.length > 0,
    staleTime: RESULT_STALE,
  });
}
