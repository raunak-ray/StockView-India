import { api } from "./client";

export interface BlockchainAutoSaveResponse {
  saved: boolean;
  message: string;
  transaction_hash: string | null;
  block_number: number | null;
  status: number | null;
  contract_address: string;
  sender: string | null;
}

export async function autoSavePrediction(
  symbol: string,
): Promise<BlockchainAutoSaveResponse> {
  return api.post<BlockchainAutoSaveResponse>(
    "/blockchain/predictions/auto",
    { symbol },
  );
}