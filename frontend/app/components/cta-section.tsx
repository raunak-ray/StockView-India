import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

import { CTA_BAND } from "../constants";

export function CtaSection() {
  return (
    <section className="mx-auto w-full max-w-6xl px-4 pb-24">
      <div className="relative overflow-hidden rounded-3xl border border-border bg-card/60 px-6 py-14 text-center sm:px-12">
        {/* Subtle depth: dot texture + one calm glow, no rainbow */}
        <div
          aria-hidden
          className="dot-grid absolute inset-0 opacity-60 [mask-image:radial-gradient(ellipse_60%_70%_at_50%_50%,black_20%,transparent_75%)]"
        />
        <div
          aria-hidden
          className="absolute -top-24 left-1/2 h-48 w-[30rem] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl"
        />
        <div className="relative">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            {CTA_BAND.title}
          </h2>
          <p className="mx-auto mt-3 max-w-md text-sm text-muted-foreground sm:text-base">
            {CTA_BAND.subtitle}
          </p>
          <Button asChild size="lg" className="mt-8 gap-2">
            <Link href="/register">
              {CTA_BAND.button}
              <ArrowRight className="size-4" />
            </Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
