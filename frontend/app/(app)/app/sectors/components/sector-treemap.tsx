"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { SectorPerformance } from "@/lib/api/market";
import { InfoTip } from "@/components/info-tip";
import { cn } from "@/lib/utils";

/**
 * Squarified treemap (Bruls et al.) — lays out sectors as near-square blocks
 * where block area ∝ total market-cap of members and colour encodes the
 * sector's % change (emerald up / red down). Layout runs in real pixels
 * against the measured container so text never stretches.
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

  const scaled = values.map((v) => (v / total) * width * height);
  let remaining = [...scaled];
  let x = x0;
  let y = y0;
  let w = width;
  let h = height;

  while (remaining.length > 0) {
    const side = Math.min(w, h);
    const row: number[] = [remaining[0]];
    remaining = remaining.slice(1);
    while (
      remaining.length > 0 &&
      worst([...row, remaining[0]], side) <= worst(row, side)
    ) {
      row.push(remaining[0]);
      remaining = remaining.slice(1);
    }

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

const TREEMAP_HEIGHT = 360;

/** Emerald/red fill vars for a % change — opacity scales within ±2%. */
function changeFill(pct: number | null) {
  if (pct === null || pct === 0) {
    return { color: "var(--muted-foreground)", opacity: 0.18 };
  }
  const intensity = Math.min(Math.abs(pct) / 2, 1) * 0.45 + 0.15;
  return {
    color: pct > 0 ? "var(--up)" : "var(--down)",
    opacity: intensity,
  };
}

function useElementWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      setWidth(entries[0]?.contentRect.width ?? 0);
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return { ref, width };
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
  const { ref, width } = useElementWidth<HTMLDivElement>();

  const layout = useMemo(() => {
    if (width <= 0) return [];
    const usable = sectors.filter((s) => s.stocks.length > 0);
    const values = usable.map((s) =>
      s.stocks.reduce((sum, st) => sum + st.mcap, 0),
    );
    const coords = squarify(values, 0, 0, width, TREEMAP_HEIGHT);
    return coords.map((rect, i) => ({
      name: usable[i].name,
      changePct: usable[i].change_pct,
      mcap: values[i],
      ...rect,
    }));
  }, [sectors, width]);

  return (
    <div ref={ref} className="relative">
      <svg
        viewBox={`0 0 ${Math.max(width, 1)} ${TREEMAP_HEIGHT}`}
        width="100%"
        height={TREEMAP_HEIGHT}
        className="block w-full rounded-xl border border-border bg-muted/30"
        role="img"
        aria-label="Sector treemap sized by market cap, coloured by change"
      >
        {layout.map((r) => {
          const fill = changeFill(r.changePct);
          const showLabel = r.w > 110 && r.h > 64;
          const showPct = r.w > 110 && r.h > 84;
          return (
            <g key={r.name}>
              <rect
                x={r.x + 1}
                y={r.y + 1}
                width={Math.max(r.w - 2, 0)}
                height={Math.max(r.h - 2, 0)}
                fill={fill.color}
                fillOpacity={fill.opacity}
                stroke={selected === r.name ? "var(--primary)" : "transparent"}
                strokeWidth={selected === r.name ? 2 : 0}
                rx={8}
                className={cn(
                  "cursor-pointer transition-opacity duration-150 hover:opacity-90",
                  selected && selected !== r.name && "opacity-40",
                )}
                onClick={() => onSelect(r.name)}
              >
                <title>{`${r.name} — ${r.changePct !== null ? `${r.changePct > 0 ? "+" : ""}${r.changePct}% today` : "no change data"} (click to see stocks)`}</title>
              </rect>
              {showLabel ? (
                <text
                  x={r.x + 12}
                  y={r.y + 22}
                  fontSize={13}
                  fontWeight={600}
                  className="pointer-events-none fill-foreground"
                >
                  {r.name}
                </text>
              ) : null}
              {showPct ? (
                <text
                  x={r.x + 12}
                  y={r.y + 40}
                  fontSize={12}
                  style={{
                    fontFamily: "var(--font-mono)",
                    fill: (r.changePct ?? 0) >= 0 ? "var(--up-strong)" : "var(--down)",
                  }}
                  className="pointer-events-none"
                >
                  {r.changePct !== null
                    ? `${r.changePct > 0 ? "+" : ""}${r.changePct}%`
                    : ""}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="mt-2.5 flex items-center justify-center gap-2 font-mono text-[10px] text-muted-foreground">
        <span>-2%</span>
        <span className="h-2 w-28 rounded-full bg-gradient-to-r from-down via-gold to-up" />
        <span>+2%</span>
        <span className="ml-2 flex items-center gap-1 normal-case">
          block size
          <InfoTip label="What does block size mean?">
            Bigger blocks are sectors whose companies add up to more market
            value. Colour shows today&apos;s average move — emerald up, red
            down, deeper means bigger. Click a block to list its stocks.
          </InfoTip>
        </span>
      </div>
    </div>
  );
}
