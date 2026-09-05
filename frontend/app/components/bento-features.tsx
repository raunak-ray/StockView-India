"use client";

import { motion, useReducedMotion, type Variants } from "motion/react";

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

/**
 * Scroll-viewport choreography: the grid reveals as one wave rolling down
 * the page (staggered children), each card rising with a soft spring.
 * Hover adds a spotlight wash + top accent beam + graphic lift.
 */
const LIST: Variants = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};

const CARD: Variants = {
  hidden: { opacity: 0, y: 32, scale: 0.97 },
  show: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

const HEAD: Variants = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  },
};

export function BentoFeatures() {
  const reduce = useReducedMotion();
  const scroll = reduce
    ? {}
    : {
        initial: "hidden" as const,
        whileInView: "show" as const,
        viewport: { once: true, amount: 0.15 } as const,
      };

  return (
    <section id="features" className="mx-auto w-full max-w-6xl scroll-mt-24 px-4 py-20">
      <motion.div {...scroll} variants={HEAD} className="mx-auto max-w-2xl text-center">
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
      </motion.div>

      <motion.div
        {...scroll}
        variants={LIST}
        className="mt-10 grid auto-rows-fr gap-4 md:grid-cols-6"
      >
        {FEATURES.map((f) => {
          const Graphic = BENTO_GRAPHICS[f.graphic];
          const big = f.graphic === "terminal";
          return (
            <motion.article
              key={f.title}
              variants={CARD}
              className={`group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-card/60 p-5 transition-[border-color,box-shadow,transform] duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/10 ${SPANS[f.graphic] ?? "md:col-span-2"}`}
            >
              {/* Hover spotlight wash */}
              <div
                aria-hidden
                className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_75%_60%_at_50%_0%,color-mix(in_oklab,var(--color-primary)_13%,transparent),transparent_70%)] opacity-0 transition-opacity duration-300 group-hover:opacity-100"
              />
              {/* Top accent beam that draws in on hover */}
              <div
                aria-hidden
                className="absolute inset-x-8 top-0 h-px scale-x-0 bg-gradient-to-r from-transparent via-primary to-transparent transition-transform duration-500 group-hover:scale-x-100"
              />
              <div className="relative flex items-center gap-2.5">
                <span className="flex size-8 shrink-0 items-center justify-center rounded-lg border border-border bg-background/60 transition-colors duration-300 group-hover:border-primary/50 group-hover:shadow-[0_0_14px_-4px_var(--color-primary)]">
                  <f.icon className="size-4 text-primary" />
                </span>
                <h3 className="font-medium">{f.title}</h3>
              </div>
              <p className="relative mt-2 max-w-md text-sm leading-relaxed text-muted-foreground">
                {f.desc}
              </p>
              {Graphic ? (
                <div
                  className={`relative mt-auto pt-4 transition-transform duration-300 ease-out group-hover:scale-[1.02] ${big ? "min-h-56 flex-1" : "h-24"}`}
                >
                  <Graphic />
                </div>
              ) : null}
            </motion.article>
          );
        })}
      </motion.div>
    </section>
  );
}
