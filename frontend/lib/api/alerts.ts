import { api } from "./client";

export interface Alert {
  id: string;
  symbol: string;
  price: number;
  condition: string;
  label: string;
  created: string;
  triggered: boolean;
}

export interface AlertListResponse {
  triggered_now: Alert[];
  active: Alert[];
  fired: Alert[];
}

export async function getAlerts(): Promise<AlertListResponse> {
  return api.get<AlertListResponse>("/alerts");
}

export async function createAlert(data: {
  symbol: string;
  price: number;
  condition: string;
  label: string;
}): Promise<Alert> {
  return api.post<Alert>("/alerts", data);
}

export async function deleteAlert(id: string): Promise<void> {
  return api.del<void>(`/alerts/${id}`);
}

export async function clearAlerts(firedOnly = false): Promise<void> {
  const qs = firedOnly ? "?fired_only=true" : "";
  return api.del<void>(`/alerts${qs}`);
}
