/**
 * Hand-drawn SVG mini-illustrations for the bento feature grid.
 * All colors come from theme tokens (emerald up / red down / gold hold /
 * blue info / cyan AI) so both modes stay correct. Animations are the
 * subtle CSS loops defined in globals.css.
 */

import type { ReactElement } from "react";

const GRID = "var(--chart-grid)";

export function TerminalGraphic() {
  const candles: Array<[number, number, number, number, number]> = [
    [16, 70, 60, 74, 56],
    [34, 60, 66, 70, 57],
    [52, 66, 50, 68, 45],
    [70, 50, 42, 54, 38],
    [88, 42, 54, 58, 40],
    [106, 54, 60, 64, 50],
    [124, 60, 74, 78, 58],
    [142, 74, 68, 76, 64],
    [160, 68, 80, 84, 66],
    [178, 80, 88, 92, 77],
    [196, 88, 82, 90, 79],
    [214, 82, 94, 98, 80],
    [232, 94, 100, 104, 91],
    [250, 100, 94, 103, 92],
    [268, 94, 106, 110, 92],
    [286, 106, 112, 116, 103],
    [304, 112, 118, 121, 109],
  ];
  return (
    <svg viewBox="0 0 320 130" className="h-full w-full" role="img" aria-hidden>
      {[24, 54, 84, 114].map((y) => (
        <line key={y} x1="0" x2="320" y1={y} y2={y} stroke={GRID} strokeWidth="1" />
      ))}
      {/* SMC demand zone */}
      <rect x="60" y="86" width="44" height="22" rx="3" fill="var(--up)" opacity="0.08" />
      <rect x="60" y="86" width="44" height="22" rx="3" fill="none" stroke="var(--up)" strokeOpacity="0.35" strokeDasharray="3 3" />
      {/* Candles */}
      {candles.map(([x, o, c, hi, lo]) => {
        const up = c >= o;
        const color = up ? "var(--up)" : "var(--down)";
        const top = Math.min(o, c);
        const h = Math.max(1.5, Math.abs(c - o));
        return (
          <g key={x} stroke={color} fill={color}>
            <line x1={x} x2={x} y1={130 - hi} y2={130 - lo} strokeWidth="1.2" />
            <rect
              x={x - 3.5}
              y={130 - top - h}
              width="7"
              height={h}
              rx="1"
              fillOpacity={up ? 0.25 : 0.55}
            />
          </g>
        );
      })}
      {/* SMA 20 */}
      <path
        d="M16,72 C60,66 100,52 140,60 S220,88 304,52"
        fill="none"
        stroke="var(--gold)"
        strokeWidth="1.6"
        opacity="0.9"
      />
      {/* Live price marker */}
      <circle cx="304" cy="44" r="3" fill="var(--up)" className="animate-soft-pulse" />
      <line x1="240" x2="316" y1="44" y2="44" stroke="var(--up)" strokeWidth="1" strokeDasharray="3 4" opacity="0.6" />
    </svg>
  );
}

export function SignalGraphic() {
  return (
    <svg viewBox="0 0 200 96" className="h-full w-full" role="img" aria-hidden>
      {/* Verdict chip */}
      <rect x="8" y="10" width="42" height="16" rx="4" fill="var(--up)" opacity="0.15" />
      <text x="29" y="21.5" textAnchor="middle" fontSize="9" fontWeight="700" fill="var(--up)" fontFamily="var(--font-mono)">
        BUY
      </text>
      {/* Score bar */}
      <rect x="58" y="16" width="118" height="5" rx="2.5" fill="var(--muted)" />
      <rect x="58" y="16" width="82" height="5" rx="2.5" fill="var(--up)" opacity="0.85" />
      <circle cx="140" cy="18.5" r="3" fill="var(--up)" className="animate-soft-pulse" />
      {/* Rule rows */}
      {[
        ["SMA 20 > SMA 50", "var(--up)"],
        ["RSI 61 — momentum", "var(--up)"],
        ["MACD cross below", "var(--down)"],
      ].map(([label, color], i) => (
        <g key={label}>
          <circle cx="14" cy={44 + i * 16} r="3" fill={color} opacity="0.8" />
          <rect x="24" y={40 + i * 16} width={112 - i * 18} height="7" rx="3.5" fill="var(--muted)" />
          <text x="26" y={46 + i * 16} fontSize="6.5" fill="var(--muted-foreground)" fontFamily="var(--font-mono)">
            {label}
          </text>
        </g>
      ))}
    </svg>
  );
}

export function NseGraphic() {
  const bars = [
    [24, 30, "up"], [40, 18, "up"], [56, 34, "up"],
    [88, 22, "down"], [104, 30, "down"], [120, 14, "down"],
    [152, 26, "up"], [168, 20, "up"], [184, 32, "up"],
  ] as const;
  return (
    <svg viewBox="0 0 200 96" className="h-full w-full" role="img" aria-hidden>
      <line x1="0" y1="88" x2="200" y2="88" stroke={GRID} strokeWidth="1" />
      {/* FII / DII grouped bars */}
      {bars.map(([x, h, dir]) => (
        <rect
          key={x}
          x={x}
          y={88 - h}
          width="10"
          height={h}
          rx="2"
          fill={dir === "up" ? "var(--up)" : "var(--down)"}
          opacity={0.7}
        />
      ))}
      {/* Flow line */}
      <path
        d="M24,58 C60,50 90,66 128,52 S176,34 192,30"
        fill="none"
        stroke="var(--info)"
        strokeWidth="1.6"
        className="animate-dash-flow"
      />
      <circle cx="192" cy="30" r="2.5" fill="var(--info)" className="animate-soft-pulse" />
      {/* Labels */}
      <text x="24" y="12" fontSize="7" fill="var(--muted-foreground)" fontFamily="var(--font-mono)">
        FII ₹ +2,140 Cr
      </text>
      <text x="88" y="12" fontSize="7" fill="var(--muted-foreground)" fontFamily="var(--font-mono)">
        DII ₹ −830 Cr
      </text>
    </svg>
  );
}

export function BacktestGraphic() {
  return (
    <svg viewBox="0 0 200 96" className="h-full w-full" role="img" aria-hidden>
      <defs>
        <linearGradient id="bt-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--up)" stopOpacity="0.18" />
          <stop offset="100%" stopColor="var(--up)" stopOpacity="0" />
        </linearGradient>
      </defs>
      <line x1="0" y1="80" x2="200" y2="80" stroke={GRID} strokeWidth="1" strokeDasharray="3 4" />
      <path
        d="M8,78 L28,74 L48,76 L68,64 L88,68 L108,54 L128,58 L148,42 L168,46 L192,26 L192,80 L8,80 Z"
        fill="url(#bt-fill)"
      />
      <path
        d="M8,78 L28,74 L48,76 L68,64 L88,68 L108,54 L128,58 L148,42 L168,46 L192,26"
        fill="none"
        stroke="var(--up)"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
      <circle cx="192" cy="26" r="2.5" fill="var(--up)" className="animate-soft-pulse" />
      <text x="160" y="18" fontSize="7" fill="var(--up)" fontFamily="var(--font-mono)">
        +38.4%
      </text>
    </svg>
  );
}

export function SectorsGraphic() {
  const cells: Array<[number, number, number, number, string, number]> = [
    [4, 4, 92, 44, "up", 0.5],
    [100, 4, 40, 44, "down", 0.45],
    [144, 4, 52, 26, "up", 0.6],
    [144, 34, 52, 14, "gold", 0.4],
    [4, 52, 58, 40, "down", 0.4],
    [66, 52, 46, 40, "up", 0.55],
    [116, 52, 38, 40, "up", 0.35],
    [158, 52, 38, 40, "down", 0.5],
  ];
  const colorOf = (c: string) =>
    c === "up" ? "var(--up)" : c === "down" ? "var(--down)" : "var(--gold)";
  return (
    <svg viewBox="0 0 200 96" className="h-full w-full" role="img" aria-hidden>
      {cells.map(([x, y, w, h, c, o], i) => (
        <g key={i}>
          <rect x={x} y={y} width={w - 2} height={h - 2} rx="3" fill={colorOf(c)} opacity={o * 0.35} />
          <rect
            x={x}
            y={y}
            width={w - 2}
            height={h - 2}
            rx="3"
            fill="none"
            stroke={colorOf(c)}
            strokeOpacity="0.5"
          />
          <circle cx={x + 7} cy={y + 7} r="2" fill={colorOf(c)} className="animate-soft-pulse" style={{ animationDelay: `${i * 0.35}s` }} />
        </g>
      ))}
    </svg>
  );
}

export function LedgerGraphic() {
  return (
    <svg viewBox="0 0 200 96" className="h-full w-full" role="img" aria-hidden>
      {/* Chain links */}
      <line x1="46" y1="44" x2="76" y2="44" stroke="var(--info)" strokeWidth="1.4" strokeDasharray="4 4" className="animate-dash-flow" />
      <line x1="122" y1="44" x2="152" y2="44" stroke="var(--info)" strokeWidth="1.4" strokeDasharray="4 4" className="animate-dash-flow" />
      {[8, 82, 156].map((x, i) => (
        <g key={x} className="animate-soft-pulse" style={{ animationDelay: `${i * 0.8}s` }}>
          <rect x={x} y="20" width="38" height="48" rx="6" fill="var(--card)" stroke={i === 2 ? "var(--up)" : "var(--border)"} strokeWidth="1.2" />
          <rect x={x + 7} y="28" width="24" height="4" rx="2" fill="var(--muted)" />
          <rect x={x + 7} y="37" width="18" height="3" rx="1.5" fill="var(--muted)" opacity="0.7" />
          <rect x={x + 7} y="44" width="22" height="3" rx="1.5" fill="var(--muted)" opacity="0.7" />
          <rect x={x + 7} y="51" width="14" height="3" rx="1.5" fill="var(--muted)" opacity="0.5" />
          {/* Hash footer */}
          <text x={x + 7} y="63" fontSize="5.5" fill={i === 2 ? "var(--up)" : "var(--muted-foreground)"} fontFamily="var(--font-mono)">
            {["000a3f…", "000b91…", "000c07…"][i]}
          </text>
        </g>
      ))}
      {/* Verified tick */}
      <path d="M170,12 l3,3 5,-6" fill="none" stroke="var(--up)" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export const BENTO_GRAPHICS: Record<string, () => ReactElement> = {
  terminal: TerminalGraphic,
  signal: SignalGraphic,
  nse: NseGraphic,
  backtest: BacktestGraphic,
  sectors: SectorsGraphic,
  ledger: LedgerGraphic,
};
