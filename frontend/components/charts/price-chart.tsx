"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  LineSeries,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useTheme } from "next-themes";

import type { Candle } from "@/lib/api/market";

export type ChartStyle = "candles" | "line";

export interface PriceChartProps {
  candles: Candle[];
  height?: number;
  chartStyle?: ChartStyle;
  showVolume?: boolean;
  showSma20?: boolean;
  showSma50?: boolean;
}

/** Palette mirrors app/globals.css tokens for both themes. */
function palette(dark: boolean) {
  return dark
    ? {
        background: "#0d1117",
        text: "#8b949e",
        grid: "#1e2535",
        border: "#30363d",
        up: "#26a69a",
        upBorder: "#1a7a72",
        down: "#ef5350",
        downBorder: "#c62828",
        line: "#26a69a",
        sma20: "#d29922",
        sma50: "#1a7fd4",
        volUp: "rgba(38,166,154,0.4)",
        volDown: "rgba(239,83,80,0.4)",
      }
    : {
        background: "#ffffff",
        text: "#57606a",
        grid: "#e2e6ee",
        border: "#d0d7de",
        up: "#0f766e",
        upBorder: "#0b5d57",
        down: "#dc2626",
        downBorder: "#991b1b",
        line: "#0f766e",
        sma20: "#b45309",
        sma50: "#2563eb",
        volUp: "rgba(15,118,110,0.35)",
        volDown: "rgba(220,38,38,0.35)",
      };
}

function toChartTime(iso: string): UTCTimestamp {
  return Math.floor(new Date(iso).getTime() / 1000) as UTCTimestamp;
}

/** Simple moving average over `window` bars; null until the window fills. */
function sma(candles: Candle[], window: number) {
  const out: { time: UTCTimestamp; value: number }[] = [];
  let sum = 0;
  for (let i = 0; i < candles.length; i++) {
    sum += candles[i].close;
    if (i >= window) sum -= candles[i - window].close;
    if (i >= window - 1) {
      out.push({ time: toChartTime(candles[i].time), value: sum / window });
    }
  }
  return out;
}

export function PriceChart({
  candles,
  height = 420,
  chartStyle = "candles",
  showVolume = true,
  showSma20 = false,
  showSma50 = false,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const mainRef = useRef<ISeriesApi<"Candlestick"> | ISeriesApi<"Line"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const sma20Ref = useRef<ISeriesApi<"Line"> | null>(null);
  const sma50Ref = useRef<ISeriesApi<"Line"> | null>(null);

  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme !== "light";
  const colors = useMemo(() => palette(isDark), [isDark]);

  // Create the chart once per theme; lightweight-charts owns its DOM.
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const chart = createChart(el, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: colors.background },
        textColor: colors.text,
        fontFamily:
          "var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace",
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: colors.grid },
        horzLines: { color: colors.grid },
      },
      rightPriceScale: { borderColor: colors.border },
      timeScale: { borderColor: colors.border, rightOffset: 6 },
      crosshair: { mode: 1 }, // magnet
      autoSize: false,
    });
    chartRef.current = chart;

    mainRef.current = chart.addSeries(
      chartStyle === "candles" ? CandlestickSeries : LineSeries,
      chartStyle === "candles"
        ? {
            upColor: colors.up,
            downColor: colors.down,
            borderUpColor: colors.upBorder,
            borderDownColor: colors.downBorder,
            wickUpColor: colors.upBorder,
            wickDownColor: colors.downBorder,
          }
        : { color: colors.line, lineWidth: 2 },
    ) as ISeriesApi<"Candlestick"> | ISeriesApi<"Line">;

    volumeRef.current = chart.addSeries(
      HistogramSeries,
      { priceFormat: { type: "volume" }, priceScaleId: "vol" },
      1,
    );
    chart.panes()[1]?.setHeight(Math.round(height * 0.22));

    sma20Ref.current = chart.addSeries(LineSeries, {
      color: colors.sma20,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });
    sma50Ref.current = chart.addSeries(LineSeries, {
      color: colors.sma50,
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: false,
    });

    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width;
      if (width) chart.applyOptions({ width });
    });
    observer.observe(el);

    return () => {
      observer.disconnect();
      chart.remove();
      chartRef.current = null;
      mainRef.current = null;
      volumeRef.current = null;
      sma20Ref.current = null;
      sma50Ref.current = null;
    };
    // Rebuild on theme or style change (series types cannot be swapped in place).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDark, chartStyle, height]);

  // Feed data without recreating the chart.
  useEffect(() => {
    const chart = chartRef.current;
    const main = mainRef.current;
    if (!chart || !main || candles.length === 0) return;

    if (chartStyle === "candles") {
      (main as ISeriesApi<"Candlestick">).setData(
        candles.map((c) => ({
          time: toChartTime(c.time),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        })),
      );
    } else {
      (main as ISeriesApi<"Line">).setData(
        candles.map((c) => ({ time: toChartTime(c.time), value: c.close })),
      );
    }

    volumeRef.current?.setData(
      showVolume
        ? candles.map((c) => ({
            time: toChartTime(c.time),
            value: c.volume ?? 0,
            color: c.close >= c.open ? colors.volUp : colors.volDown,
          }))
        : [],
    );
    volumeRef.current?.applyOptions({ visible: showVolume });

    sma20Ref.current?.setData(showSma20 ? sma(candles, 20) : []);
    sma50Ref.current?.setData(showSma50 ? sma(candles, 50) : []);

    chart.timeScale().fitContent();
  }, [candles, chartStyle, showVolume, showSma20, showSma50, colors]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
