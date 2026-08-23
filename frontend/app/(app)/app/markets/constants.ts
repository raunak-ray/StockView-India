/** Option indices supported by NSE chain endpoints (app.py:1396 parity). */
export const OPTION_INDICES = [
  "NIFTY",
  "BANKNIFTY",
  "FINNIFTY",
  "MIDCPNIFTY",
] as const;

export type OptionIndex = (typeof OPTION_INDICES)[number];

export const DEFAULT_OPTION_SYMBOL = "NIFTY";

/** Rows per page in the options chain table. */
export const CHAIN_PAGE_SIZE = 10;

export const SEARCH_DEBOUNCE_MS = 300;
