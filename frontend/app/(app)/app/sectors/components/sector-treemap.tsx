"use client";

import { useMemo } from "react";
import type { SectorPerformance } from "@/lib/api/market";
import { cn } from "@/lib/utils";

/**
 * Squarified treemap (Bruls et al.) — lays out sectors as near-square blocks
 * where block area ∝ total market-cap of members and colour encodes the
 * sector's % change (teal up / red down), matching plan/03 §5.8.
 */

/** Worst aspect ratio of a row laid against the shorter side of `w × h`. */
function worst(row: number[], side: number): number {
  const sum = row.reduce((a, b) => a + b, 0);
  const max = Math.max(...row);
  const min = Math.min(...row);
  const s2 = sum * sum;
  const l2 = side * side;
  return Math.max((l2 * max) / s2, s2 / (l2 * min));
}

function squarify(
  values: number[],
  x0: number,
  y0: number,
  width: number,
  height: number,
): Array<{ x: number; y: number; w: number; h: number }> {
  const rects: Array<{ x: number; y: number; w: number; h: number }> = [];
  const total = values.reduce((a, b) => a + b, 0);
  if (total <= 0) return rects;

  // Normalise values into area units matching the canvas.
  const scaled = values.map((v) => (v / total) * width * height);
  let remaining = [...scaled];
  let x = x0;
  let y = y0;
  let w = width;
  let h = height;

  while (remaining.length > 0) {
    const side = Math.min(w, h);
    // Grow a row greedily while it improves the worst aspect ratio.
    const row: number[] = [remaining[0]];
    remaining = remaining.slice(1);
    while (
      remaining.length > 0 &&
      worst([...row, remaining[0]], side) <= worst(row, side)
    ) {
      row.push(remaining[0]);
      remaining = remaining.slice(1);
    }

    // Lay the row along the shorter side and shrink the canvas.
    const rowSum = row.reduce((a, b) => a + b, 0);
    const thickness = rowSum / side;
    let offset = 0;
    for (const item of row) {
      const size = item / thickness;
      if (w >= h) {
        rects.push({ x, y: y + offset, w: thickness, h: size });
      } else {
        rects.push({ x: x + offset, y, w: size, h: thickness });
      }
      offset += size;
    }

    if (w >= h) {
      x += thickness;
      w -= thickness;
    } else {
      y += thickness;
      h -= thickness;
    }
  }
  return rects;
}

/** Signed teal/red fill for a % change — intensity scales within ±2%. */
function changeFill(pct: number | null): string {
  if (pct === null || pct === 0) return "rgba(139,148,158,0.25)";
  const intensity = Math.min(Math.abs(pct) / 2, 1) * 0.45 + 0.12;
  return pct > 0
    ? `rgba(38,166,154,${intensity.toFixed(2)})`
    : `rgba(239,83,80,${intensity.toFixed(2)})`;
}

export function SectorTreemap({
  sectors,
  selected,
  onSelect,
}: {
  sectors: SectorPerformance[];
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  const layout = useMemo(() => {
    const usable = sectors.filter((s) => s.stocks.length > 0);
    const values = usable.map((s) =>
      s.stocks.reduce((sum, st) => sum + st.mcap, 0),
    );
    const coords = squarify(values, 0, 0, 100, 100);
    return coords.map((rect, i) => ({
      name: usable[i].name,
      changePct: usable[i].change_pct,
      ...rect,
    }));
  }, [sectors]);

  return (
    <div className="relative">
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        className="h-80 w-full rounded-xl border border-border bg-muted/40"
        role="img"
        aria-label="Sector treemap sized by market cap, coloured by change"
      >
        {layout.map((r) => (
          <g key={r.name}>
            <rect
              x={r.x + 0.3}
              y={r.y + 0.3}
              width={Math.max(r.w - 0.6, 0)}
              height={Math.max(r.h - 0.6, 0)}
              fill={changeFill(r.changePct)}
              stroke={selected === r.name ? "var(--foreground)" : "transparent"}
              strokeWidth={0.6}
              rx={1}
              className={cn(
                "cursor-pointer transition-opacity hover:opacity-90",
                selected && selected !== r.name && "opacity-50",
              )}
              onClick={() => onSelect(r.name)}
            >
              <title>{`${r.name} ${r.changePct !== null ? `${r.changePct > 0 ? "+" : ""}${r.changePct}%` : ""} — click to inspect`}</title>
            </rect>
            {/* Labels only when the block is big enough to read */}
            {r.w > 14 && r.h > 10 && (
              <>
                <text
                  x={r.x + 2}
                  y={r.y + 7}
                  fontSize={3.4}
                  className="fill-foreground pointer-events-none font-semibold"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {r.name}
                </text>
                <text
                  x={r.x + 2}
                  y={r.y + 11.5}
                  fontSize={3}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fill: (r.changePct ?? 0) >= 0 ? "#26a69a" : "#ef5350",
                  }}
                  className="pointer-events-none"
                >
                  {r.changePct !== null
                    ? `${r.changePct > 0 ? "+" : ""}${r.changePct}%`
                    : ""}
                </text>
              </>
            )}
          </g>
        ))}
      </svg>
      {/* Native colour legend */}
      <div className="mt-2 flex items-center justify-center gap-2 font-mono text-[10px] text-muted-foreground">
        <span>-2%</span>
        <span className="h-2 w-24 rounded-full bg-gradient-to-r from-down via-gold to-up" />
        <span>+2%</span>
        <span className="ml-3">size = total market cap · click a block</span>
      </div>
    </div>
  );
}
