import { api } from "./client";

export interface Instrument {
  name: string;
  ticker: string;
}

export interface InstrumentListResponse {
  count: number;
  instruments: Instrument[];
}

export interface InstrumentSearchResponse {
  query: string;
  count: number;
  results: Instrument[];
}

export async function searchInstruments(
  q: string,
  limit = 20,
): Promise<InstrumentSearchResponse> {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return api.get<InstrumentSearchResponse>(`/instruments/search?${params}`);
}
