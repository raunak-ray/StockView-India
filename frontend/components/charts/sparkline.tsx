"use client";

/** Minimal inline sparkline (SVG polyline) for signed value series. */
export function Sparkline({
  values,
  width = 220,
  height = 48,
}: {
  values: number[];
  width?: number;
  height?: number;
}) {
  if (values.length < 2) return null;

  const min = Math.min(...values, 0);
  const max = Math.max(...values, 0);
  const range = max - min || 1;
  const stepX = width / (values.length - 1);
  const yOf = (v: number) => height - ((v - min) / range) * (height - 4) - 2;
  const points = values.map((v, i) => `${i * stepX},${yOf(v)}`).join(" ");
  const zeroY = yOf(0);

  return (
    <svg
      aria-hidden
      viewBox={`0 0 ${width} ${height}`}
      className="h-12 w-full"
      preserveAspectRatio="none"
    >
      {/* zero baseline */}
      <line
        x1={0}
        x2={width}
        y1={zeroY}
        y2={zeroY}
        className="stroke-border"
        strokeWidth={1}
        strokeDasharray="3 3"
      />
      <polyline
        points={points}
        fill="none"
        className="stroke-primary"
        strokeWidth={1.5}
      />
    </svg>
  );
}
