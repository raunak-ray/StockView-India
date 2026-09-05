import Image from "next/image";

import { TextReveal } from "@/components/motion/text-reveal";

import { HERO, HERO_STATS } from "../constants";
import { HeroCta } from "./hero-cta";
import { HeroPreview } from "./hero-preview";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden pb-24 pt-28">
      {/* Layer 0: photo — dark candlestick terminal, slow Ken Burns drift */}
      <Image
        src="/images/hero-terminal.jpg"
        alt=""
        fill
        priority
        sizes="100vw"
        className="animate-hero-zoom object-cover"
      />
      {/* Layer 1: readability wash (theme-aware so text stays legible) */}
      <div
        aria-hidden
        className="absolute inset-0 bg-background/72 dark:bg-[#060b16]/80"
      />
      {/* Layer 2: top blend under the header + bottom fade into the page */}
      <div
        aria-hidden
        className="absolute inset-0 bg-gradient-to-b from-background/85 via-transparent to-background dark:from-[#060b16]/90 dark:via-transparent dark:to-background"
      />
      {/* Layer 3: emerald center glow + texture */}
      <div
        aria-hidden
        className="absolute inset-0 bg-[radial-gradient(ellipse_60%_45%_at_50%_38%,color-mix(in_oklab,var(--color-primary)_18%,transparent),transparent_70%)]"
      />
      <div
        aria-hidden
        className="dot-grid absolute inset-0 [mask-image:radial-gradient(ellipse_55%_45%_at_50%_35%,black_25%,transparent_75%)]"
      />
      <div
        aria-hidden
        className="animate-drift absolute -top-32 left-1/2 h-80 w-[42rem] -translate-x-1/2 rounded-full bg-primary/15 blur-3xl"
      />
      <div
        aria-hidden
        className="animate-drift absolute right-[8%] top-40 h-48 w-72 rounded-full bg-ai/10 blur-3xl"
        style={{ animationDelay: "-6s" }}
      />

      <div className="relative mx-auto flex w-full max-w-6xl flex-col items-center px-4 text-center">
        <p className="flex animate-in fade-in slide-in-from-bottom-4 duration-700 items-center gap-2 rounded-full border border-border bg-card/60 px-3.5 py-1.5 text-xs font-medium tracking-wide text-muted-foreground backdrop-blur">
          <span className="animate-soft-pulse size-1.5 rounded-full bg-primary" />
          {HERO.badge}
        </p>

        <h1 className="mt-7 text-4xl font-bold leading-[1.08] tracking-tight sm:text-6xl">
          {HERO.titleLines.map((line, i) => (
            <span
              key={line}
              className="block animate-in fade-in slide-in-from-bottom-6 duration-700"
              style={{ animationDelay: `${120 + i * 150}ms`, animationFillMode: "backwards" }}
            >
              {i === HERO.titleLines.length - 1 ? (
                <>
                  {line.slice(0, line.length - HERO.gradientWord.length)}
                  <span className="bg-gradient-to-r from-primary via-info to-ai bg-clip-text text-transparent">
                    {HERO.gradientWord}
                  </span>
                </>
              ) : (
                line
              )}
            </span>
          ))}
        </h1>

        <TextReveal
          as="p"
          text={HERO.subtitle}
          className="mt-6 max-w-xl text-base text-muted-foreground sm:text-lg"
        />

        <HeroCta />

        {/* Trust stats */}
        <dl className="mt-12 grid w-full max-w-2xl grid-cols-2 gap-y-6 sm:grid-cols-4">
          {HERO_STATS.map(([value, label], i) => (
            <div
              key={label}
              className="flex animate-in fade-in duration-700 flex-col items-center gap-0.5"
              style={{ animationDelay: `${400 + i * 90}ms`, animationFillMode: "backwards" }}
            >
              <dt className="sr-only">{label}</dt>
              <dd className="font-mono text-xl font-semibold text-foreground">{value}</dd>
              <dd className="text-xs text-muted-foreground">{label}</dd>
            </div>
          ))}
        </dl>

        <div
          className="w-full animate-in fade-in slide-in-from-bottom-10 duration-1000"
          style={{ animationDelay: "550ms", animationFillMode: "backwards" }}
        >
          <HeroPreview />
        </div>
      </div>
    </section>
  );
}
