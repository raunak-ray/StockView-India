import { api } from "./client";
import type { Interval, Period } from "./market";

export interface MlCapabilities {
  sklearn: boolean;
  xgboost: boolean;
  lightgbm: boolean;
  catboost: boolean;
  torch: boolean;
  shap: boolean;
  active_ensemble: string[];
}

export interface HorizonPred {
  direction: "up" | "down";
  prob: number;
}

export interface FeatureImportance {
  feature: string;
  importance: number;
}

export interface MlResult {
  prediction: "UP" | "DOWN";
  direction: "up" | "down";
  confidence: number;
  accuracy: number;
  top_features: FeatureImportance[];
  n_train: number;
  n_test: number;
  horizon: Record<string, HorizonPred>;
  model_accs: Record<string, number>;
  conf_tier: { tier: "HIGH" | "MEDIUM" | "LOW"; tone: string };
  up_prob: number;
  dn_prob: number;
  sentiment: { score: number; label: string };
  lstm_prob: number;
  walk_fwd_acc: number;
  ensemble_size: number;
  active_models: string;
  shap: { ok: boolean; error?: string };
  predicted_price: number | null;
}

export interface MlJobCreated {
  job_id: string;
  symbol: string;
  status: string;
}

export interface MlJob {
  job_id: string;
  symbol: string;
  status: "running" | "done" | "error";
  started_at: number;
  finished_at: number | null;
  result: MlResult | null;
  error: string | null;
}

export interface LstmForecast {
  available: boolean;
  symbol?: string;
  model?: string;
  last_close?: number;
  predicted_close?: number;
  expected_change_pct?: number;
  trained_points?: number;
  test_mse_scaled?: number;
  reason?: string;
}

export async function getMlCapabilities(): Promise<MlCapabilities> {
  return api.get<MlCapabilities>("/ml/capabilities");
}

export async function startMlPredict(
  symbol: string,
  useLstm = false,
): Promise<MlJobCreated> {
  const params = new URLSearchParams({ symbol, use_lstm: String(useLstm) });
  return api.post<MlJobCreated>(`/ml/predict?${params}`);
}

export async function getMlJob(jobId: string): Promise<MlJob> {
  return api.get<MlJob>(`/ml/predict/${jobId}`);
}

export async function getLstmForecast(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<LstmForecast> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<LstmForecast>(`/ml/lstm-forecast?${params}`);
}
