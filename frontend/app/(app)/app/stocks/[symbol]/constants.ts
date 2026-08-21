/** Live-quote auto-refresh options — parity with the Streamlit
 *  select_slider (app.py:1022): [5, 10, 15, 30, 60] seconds. */
export const REFRESH_INTERVALS = [5, 10, 15, 30, 60] as const;

export type RefreshInterval = (typeof REFRESH_INTERVALS)[number];

export const DEFAULT_REFRESH_INTERVAL: RefreshInterval = 10;
