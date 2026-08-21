"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export function HeroCta() {
  return (
    <div className="mt-10 flex flex-col items-center gap-3 sm:flex-row">
      <Button asChild size="lg" className="gap-2">
        <Link href="/register">
          Start trading free
          <ArrowRight className="size-4" />
        </Link>
      </Button>
      <Button asChild variant="secondary" size="lg">
        <Link href="/login">Try the demo account</Link>
      </Button>
    </div>
  );
}