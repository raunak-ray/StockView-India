import { api } from "./client";
import type { Interval, Period } from "./market";

export interface Rule {
  rule: string;
  kind: "buy" | "sell" | "neut";
}

export interface SignalMarker {
  time: string;
  position: "aboveBar" | "belowBar";
  kind: "buy" | "sell";
  price: number;
}

export interface SignalResponse {
  symbol: string;
  verdict: string;
  score: number;
  /** 0.5 – 1.0 (server blends agreement ratio + score magnitude). */
  confidence: number;
  rules: Rule[];
  reasons: string[];
  markers: SignalMarker[];
}

export async function getSignal(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<SignalResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<SignalResponse>(`/signals?${params}`);
}
