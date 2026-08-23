"use client";

import { motion, useReducedMotion } from "motion/react";

import { FEATURES } from "../constants";
import { BENTO_GRAPHICS } from "./bento-graphics";

/** Bento span per feature — the terminal is the hero tile (4×2). */
const SPANS: Record<string, string> = {
  terminal: "md:col-span-4 md:row-span-2",
  signal: "md:col-span-2",
  nse: "md:col-span-2",
  backtest: "md:col-span-2",
  sectors: "md:col-span-2",
  ledger: "md:col-span-2",
};

export function BentoFeatures() {
  const reduce = useReducedMotion();

  return (
    <section id="features" className="mx-auto w-full max-w-6xl px-4 py-20">
      <div className="mx-auto max-w-2xl text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-primary">
          Features
        </p>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight sm:text-3xl">
          Everything a trader needs
        </h2>
        <p className="mt-3 text-sm text-muted-foreground sm:text-base">
          One terminal for research, signals and practice — built for NSE and
          BSE, free and open source.
        </p>
      </div>

      <div className="mt-10 grid auto-rows-fr gap-4 md:grid-cols-6">
        {FEATURES.map((f, i) => {
          const Graphic = BENTO_GRAPHICS[f.graphic];
          const big = f.graphic === "terminal";
          return (
            <motion.article
              key={f.title}
              initial={reduce ? undefined : { opacity: 0, y: 14 }}
              whileInView={reduce ? undefined : { opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.25 }}
              transition={{ duration: 0.45, delay: i * 0.06, ease: "easeOut" }}
              className={`group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card/60 p-5 transition-[border-color,box-shadow,transform] duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md hover:shadow-primary/5 ${SPANS[f.graphic] ?? "md:col-span-2"}`}
            >
              <div className="flex items-center gap-2.5">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-background/60">
                  <f.icon className="size-4 text-primary" />
                </span>
                <h3 className="font-medium">{f.title}</h3>
              </div>
              <p className="mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                {f.desc}
              </p>
              {Graphic ? (
                <div
                  className={`mt-auto pt-4 transition-transform duration-300 group-hover:scale-[1.015] ${big ? "min-h-56 flex-1" : "h-24"}`}
                >
                  <Graphic />
                </div>
              ) : null}
            </motion.article>
          );
        })}
      </div>
    </section>
  );
}
