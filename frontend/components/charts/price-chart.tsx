"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramSeries,
  LineSeries,
  LineStyle,
  type IChartApi,
  type IPriceLine,
  type ISeriesApi,
  type ISeriesMarkersPluginApi,
  type SeriesMarker,
  type Time,
  type UTCTimestamp,
} from "lightweight-charts";
import { useTheme } from "next-themes";

import type { IndicatorsResponse, SeriesPoint } from "@/lib/api/analytics";
import type { SignalMarker } from "@/lib/api/signals";
import type { Candle } from "@/lib/api/market";

export type ChartStyle = "candles" | "line";

export interface SRLevel {
  price: number;
  kind: "support" | "resistance";
}

export interface PriceChartProps {
  candles: Candle[];
  indicators?: IndicatorsResponse;
  markers?: SignalMarker[];
  srLevels?: SRLevel[];
  height?: number;
  chartStyle?: ChartStyle;
  showVolume?: boolean;
  showSma20?: boolean;
  showSma50?: boolean;
  showBB?: boolean;
  showRsi?: boolean;
  showMacd?: boolean;
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
        bb: "#8957e5",
        support: "#26a69a",
        resistance: "#ef5350",
        volUp: "rgba(38,166,154,0.4)",
        volDown: "rgba(239,83,80,0.4)",
        macdUp: "rgba(38,166,154,0.5)",
        macdDown: "rgba(239,83,80,0.5)",
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
        bb: "#7c3aed",
        support: "#0f766e",
        resistance: "#dc2626",
        volUp: "rgba(15,118,110,0.35)",
        volDown: "rgba(220,38,38,0.35)",
        macdUp: "rgba(15,118,110,0.45)",
        macdDown: "rgba(220,38,38,0.45)",
      };
}

function toTime(iso: string): UTCTimestamp {
  return Math.floor(new Date(iso).getTime() / 1000) as UTCTimestamp;
}

function toLineData(points: SeriesPoint[] | undefined) {
  return (points ?? []).map((p) => ({ time: toTime(p.time), value: p.value }));
}

export function PriceChart({
  candles,
  indicators,
  markers = [],
  srLevels = [],
  height = 420,
  chartStyle = "candles",
  showVolume = true,
  showSma20 = true,
  showSma50 = true,
  showBB = false,
  showRsi = false,
  showMacd = false,
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const mainRef = useRef<ISeriesApi<"Candlestick"> | ISeriesApi<"Line"> | null>(null);
  const volumeRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const rsiRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdHistRef = useRef<ISeriesApi<"Histogram"> | null>(null);
  const macdLineRef = useRef<ISeriesApi<"Line"> | null>(null);
  const macdSignalRef = useRef<ISeriesApi<"Line"> | null>(null);
  const overlayRefs = useRef<Record<string, ISeriesApi<"Line">>>({});
  const priceLinesRef = useRef<IPriceLine[]>([]);
  const markersRef = useRef<ISeriesMarkersPluginApi<Time> | null>(null);

  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme !== "light";
  const colors = useMemo(() => palette(isDark), [isDark]);

  // Chart is rebuilt when theme/style or pane layout changes; series types
  // cannot be swapped in place and empty panes would still render axes.
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
      { priceFormat: { type: "volume" }, priceScaleId: "" },
      1,
    );
    rsiRef.current =
      chart.addSeries(
        LineSeries,
        { color: colors.sma20, lineWidth: 1, priceScaleId: "rsi" },
        2,
      ) ?? null;
    if (showVolume) chart.panes()[1]?.setHeight(Math.round(height * 0.2));
    if (showRsi) chart.panes()[2]?.setHeight(Math.round(height * 0.16));

    if (showMacd) {
      macdHistRef.current = chart.addSeries(
        HistogramSeries,
        { priceFormat: { type: "price" }, priceScaleId: "macd" },
        3,
      );
      macdLineRef.current = chart.addSeries(
        LineSeries,
        { color: colors.sma50, lineWidth: 1, priceScaleId: "macd" },
        3,
      );
      macdSignalRef.current = chart.addSeries(
        LineSeries,
        { color: colors.sma20, lineWidth: 1, priceScaleId: "macd" },
        3,
      );
      chart.panes()[3]?.setHeight(Math.round(height * 0.18));
    }

    // Overlays on the main pane (created once, fed by the data effect).
    for (const [key, color] of [
      ["bb_high", colors.bb],
      ["bb_low", colors.bb],
    ] as const) {
      overlayRefs.current[key] = chart.addSeries(LineSeries, {
        color,
        lineWidth: 1,
        lineStyle: LineStyle.Dotted,
        priceLineVisible: false,
        lastValueVisible: false,
      });
    }

    markersRef.current = createSeriesMarkers(mainRef.current, []);

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
      rsiRef.current = null;
      macdHistRef.current = null;
      macdLineRef.current = null;
      macdSignalRef.current = null;
      overlayRefs.current = {};
      priceLinesRef.current = [];
      markersRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isDark, chartStyle, height, showVolume, showRsi, showMacd]);

  // Feed data without recreating the chart.
  useEffect(() => {
    const chart = chartRef.current;
    const main = mainRef.current;
    if (!chart || !main || candles.length === 0) return;

    if (chartStyle === "candles") {
      (main as ISeriesApi<"Candlestick">).setData(
        candles.map((c) => ({
          time: toTime(c.time),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        })),
      );
    } else {
      (main as ISeriesApi<"Line">).setData(
        candles.map((c) => ({ time: toTime(c.time), value: c.close })),
      );
    }

    volumeRef.current?.setData(
      showVolume
        ? candles.map((c) => ({
            time: toTime(c.time),
            value: c.volume ?? 0,
            color: c.close >= c.open ? colors.volUp : colors.volDown,
          }))
        : [],
    );

    // Indicator overlays (API-computed — parity with app.py ta usage).
    const overlayData: Record<string, ReturnType<typeof toLineData>> = {
      sma20: toLineData(indicators?.sma20),
      sma50: toLineData(indicators?.sma50),
      ema20: toLineData(indicators?.ema20),
      bb_high: toLineData(indicators?.bb_high),
      bb_low: toLineData(indicators?.bb_low),
    };

    // SMA/EMA reuse one generic overlay slot each (create lazily).
    const ensureOverlay = (key: string, color: string, dashed = false) => {
      if (!overlayRefs.current[key]) {
        overlayRefs.current[key] = chart.addSeries(LineSeries, {
          color,
          lineWidth: 1,
          lineStyle: dashed ? LineStyle.Dotted : undefined,
          priceLineVisible: false,
          lastValueVisible: false,
        });
      }
      return overlayRefs.current[key];
    };

    ensureOverlay("sma20", colors.sma20).setData(showSma20 ? overlayData.sma20 : []);
    ensureOverlay("sma50", colors.sma50).setData(showSma50 ? overlayData.sma50 : []);
    overlayRefs.current["bb_high"].setData(showBB ? overlayData.bb_high : []);
    overlayRefs.current["bb_low"].setData(showBB ? overlayData.bb_low : []);

    rsiRef.current?.setData(showRsi ? toLineData(indicators?.rsi) : []);
    macdHistRef.current?.setData(
      showMacd
        ? (indicators?.macd_hist ?? []).map((p, i) => ({
            time: toTime(p.time),
            value: p.value,
            color:
              p.value >= (indicators?.macd_signal?.[i]?.value ?? p.value)
                ? colors.macdUp
                : colors.macdDown,
          }))
        : [],
    );
    macdLineRef.current?.setData(showMacd ? toLineData(indicators?.macd) : []);
    macdSignalRef.current?.setData(showMacd ? toLineData(indicators?.macd_signal) : []);

    // S/R horizontal price lines (re-created on change).
    for (const line of priceLinesRef.current) main.removePriceLine(line);
    priceLinesRef.current = [];
    if (srLevels.length > 0) {
      for (const level of srLevels.slice(0, 6)) {
        priceLinesRef.current.push(
          main.createPriceLine({
            price: level.price,
            color: level.kind === "support" ? colors.support : colors.resistance,
            lineWidth: 1,
            lineStyle: LineStyle.Dashed,
            axisLabelVisible: true,
            title: level.kind === "support" ? "S" : "R",
          }),
        );
      }
    }

    // Buy/sell markers.
    markersRef.current?.setMarkers(
      markers
        .slice(-100)
        .map<SeriesMarker<Time>>((m) =>
          m.kind === "buy"
            ? {
                time: toTime(m.time),
                position: "belowBar",
                color: colors.up,
                shape: "arrowUp",
                text: "B",
              }
            : {
                time: toTime(m.time),
                position: "aboveBar",
                color: colors.down,
                shape: "arrowDown",
                text: "S",
              },
        ),
    );

    chart.timeScale().fitContent();
  }, [
    candles, indicators, markers, srLevels, chartStyle, showVolume,
    showSma20, showSma50, showBB, showRsi, showMacd, colors,
  ]);

  return <div ref={containerRef} className="w-full" style={{ height }} />;
}
