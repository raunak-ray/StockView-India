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

// ── Fusion types ───────────────────────────────────────────────────────────

export interface LayerSignals {
  rule: string;
  kind: string;
}

export interface FusionLayer {
  score: number;
  label: string;
  weight: number;
}

export interface FusionTechnicalLayer extends FusionLayer {
  signals: LayerSignals[];
  reasons: string[];
}

export interface FusionMlLayer extends FusionLayer {
  available: boolean;
  up_prob: number;
  confidence: number;
  horizon: Record<string, { direction: string; prob: number }>;
  model_accs: Record<string, number>;
  conf_tier: Record<string, string>;
  walk_fwd_acc: number;
  active_models: string;
}

export interface FusionNewsLayer extends FusionLayer {
  available: boolean;
  detail: { headline: string; label: string; score: number }[];
}

export interface FusionLayers {
  technical: FusionTechnicalLayer;
  ml: FusionMlLayer;
  news: FusionNewsLayer;
}

export interface FusionResponse {
  symbol: string;
  fused_score: number;
  final_label: string;
  final_desc: string;
  confidence_tier: string;
  confidence_tone: string;
  missing: string[];
  layers: FusionLayers;
}

export async function getFusion(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<FusionResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<FusionResponse>(`/signals/fusion?${params}`);
}
