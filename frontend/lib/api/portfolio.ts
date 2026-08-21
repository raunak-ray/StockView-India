import { api } from "./client";

export interface WatchlistItem {
  ticker: string;
  sort_order: number;
  created_at: string;
}

export interface WatchlistResponse {
  count: number;
  items: WatchlistItem[];
}

interface MessageResponse {
  message: string;
}

export async function getWatchlist(): Promise<WatchlistResponse> {
  return api.get<WatchlistResponse>("/portfolio/watchlist");
}

export async function addToWatchlist(ticker: string): Promise<MessageResponse> {
  return api.post<MessageResponse>("/portfolio/watchlist", { ticker });
}

export async function removeFromWatchlist(ticker: string): Promise<MessageResponse> {
  const encoded = encodeURIComponent(ticker);
  return api.del<MessageResponse>(`/portfolio/watchlist/${encoded}`);
}
