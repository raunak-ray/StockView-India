/**
 * Hero product preview — a glassy mini terminal mock, pure SVG (server-safe).
 * Subtle life: SMA line "draws" itself (dash-flow), ML/RSI chips float.
 */

const CANDLES: ReadonlyArray<
  readonly [x: number, o: number, c: number, hi: number, lo: number]
> = [
  [20, 96, 88, 102, 84],
  [40, 88, 94, 97, 85],
  [60, 94, 78, 96, 74],
  [80, 78, 72, 80, 66],
  [100, 72, 84, 86, 70],
  [120, 84, 90, 93, 82],
  [140, 90, 104, 107, 88],
  [160, 104, 99, 106, 95],
  [180, 99, 108, 111, 97],
  [200, 108, 116, 119, 105],
  [220, 116, 110, 118, 107],
  [240, 110, 121, 124, 108],
  [260, 121, 128, 132, 118],
  [280, 128, 122, 130, 119],
  [300, 122, 134, 137, 120],
  [320, 134, 142, 146, 131],
];

const SMA_PATH =
  "M20,95 L40,91 L60,86 L80,81 L100,80 L120,83 L140,90 L160,94 L180,98 L200,104 L220,109 L240,113 L260,119 L280,124 L300,128 L320,133";

export function HeroPreview() {
  return (
    <div className="relative mx-auto mt-16 w-full max-w-3xl">
      {/* Floating stat chips */}
      <div
        className="animate-float-y absolute -left-4 top-10 z-10 hidden rounded-lg border border-ai/30 bg-card/80 px-3 py-1.5 text-xs font-medium text-ai shadow-lg backdrop-blur sm:block"
        style={{ animationDelay: "-2s" }}
      >
        ML · 72% UP next 5d
      </div>
      <div
        className="animate-float-y absolute -right-3 bottom-14 z-10 hidden rounded-lg border border-border bg-card/80 px-3 py-1.5 font-mono text-xs text-muted-foreground shadow-lg backdrop-blur sm:block"
        style={{ animationDelay: "-4.5s" }}
      >
        RSI 61.4 · MACD +
      </div>

      {/* Terminal card */}
      <div className="overflow-hidden rounded-2xl border border-border/80 bg-card/70 shadow-2xl shadow-primary/5 backdrop-blur-md">
        {/* Window chrome */}
        <div className="flex items-center gap-2 border-b border-border/70 px-4 py-2.5">
          <span className="size-2.5 rounded-full bg-down/70" />
          <span className="size-2.5 rounded-full bg-gold/70" />
          <span className="size-2.5 rounded-full bg-up/70" />
          <span className="ml-3 font-mono text-xs text-muted-foreground">
            RELIANCE · NSE · 1D
          </span>
          <span className="ml-auto flex items-center gap-1.5 rounded-full border border-up/30 bg-up/10 px-2 py-0.5 font-mono text-xs font-semibold text-up">
            <span className="animate-soft-pulse size-1.5 rounded-full bg-up" />
            ₹2,981.40 ▲ 1.34%
          </span>
        </div>

        {/* Chart */}
        <div className="relative">
          <svg
            viewBox="0 0 360 200"
            className="block w-full"
            role="img"
            aria-label="Example candlestick chart with moving average and order block zone"
          >
            <defs>
              <linearGradient id="ob-zone" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--info)" stopOpacity="0.16" />
                <stop offset="100%" stopColor="var(--info)" stopOpacity="0.04" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            {[50, 90, 130, 170].map((y) => (
              <line
                key={y}
                x1="8"
                x2="352"
                y1={y}
                y2={y}
                stroke="var(--chart-grid)"
                strokeWidth="1"
              />
            ))}

            {/* SMC order-block zone */}
            <rect x="72" y="64" width="52" height="26" rx="3" fill="url(#ob-zone)" stroke="var(--info)" strokeOpacity="0.35" strokeWidth="1" strokeDasharray="3 3" />
            <text x="76" y="60" fontSize="7" fill="var(--info)" opacity="0.9" fontFamily="var(--font-mono)">
              ORDER BLOCK
            </text>

            {/* Candles */}
            {CANDLES.map(([x, o, c, hi, lo]) => {
              const up = c >= o;
              const color = up ? "var(--up)" : "var(--down)";
              const top = Math.min(o, c);
              const height = Math.max(2, Math.abs(c - o));
              return (
                <g key={x} stroke={color} fill={color}>
                  <line x1={x} x2={x} y1={200 - hi} y2={200 - lo} strokeWidth="1.5" />
                  <rect
                    x={x - 4}
                    y={200 - top - height}
                    width="8"
                    height={height}
                    rx="1"
                    fill={up ? "transparent" : color}
                    fillOpacity={up ? 0 : 0.25}
                  />
                </g>
              );
            })}

            {/* SMA path */}
            <path
              d={SMA_PATH}
              fill="none"
              stroke="var(--gold)"
              strokeWidth="1.8"
              strokeLinecap="round"
              opacity="0.9"
            />

            {/* Volume bars */}
            {CANDLES.map(([x, o, c], i) => (
              <rect
                key={`v-${x}`}
                x={x - 3}
                y={196 - [14, 10, 18, 20, 12, 8, 16, 9, 11, 15, 7, 13, 17, 8, 12, 10][i]}
                width="6"
                rx="1"
                fill={c >= o ? "var(--up)" : "var(--down)"}
                opacity="0.25"
                height={[14, 10, 18, 20, 12, 8, 16, 9, 11, 15, 7, 13, 17, 8, 12, 10][i]}
              />
            ))}

            {/* Last-price dashed line */}
            <line
              x1="8"
              x2="352"
              y1={200 - 142}
              y2={200 - 142}
              stroke="var(--up)"
              strokeWidth="1"
              strokeDasharray="4 4"
              opacity="0.5"
            />
          </svg>
        </div>

        {/* Verdict strip */}
        <div className="flex items-center gap-3 border-t border-border/70 px-4 py-3">
          <span className="rounded-md bg-up/15 px-2 py-1 text-xs font-semibold text-up">
            BUY
          </span>
          <div className="flex h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
            <div className="h-full w-[68%] rounded-full bg-gradient-to-r from-up/70 to-up" />
          </div>
          <span className="font-mono text-xs text-muted-foreground">
            score +8.2 / ±15 · confidence 74%
          </span>
        </div>
      </div>

      {/* Under-glow */}
      <div
        aria-hidden
        className="absolute -inset-x-8 -bottom-10 -z-10 h-40 bg-gradient-to-tr from-primary/25 via-info/15 to-transparent blur-3xl"
      />
    </div>
  );
}
