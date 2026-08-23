"use client";

import { Activity, CandlestickChart, Landmark, Scale } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AdvancesDeclinesTab } from "./components/advances-declines-tab";
import { FiiDiiTab } from "./components/fii-dii-tab";
import { NseQuoteTab } from "./components/nse-quote-tab";
import { OptionsTab } from "./components/options-tab";

/** Markets — India (NSE): quote, FII/DII flows, breadth and options. */
export default function MarketsPage() {
  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Markets — India (NSE)</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Live quotes, institutional flows, market breadth and options data.
        </p>
      </div>

      <Tabs defaultValue="quote">
        <TabsList
          aria-label="Market data sections"
          className="grid h-auto w-full grid-cols-2 gap-1 sm:grid-cols-4"
        >
          <TabsTrigger value="quote" className="gap-1.5 py-2">
            <CandlestickChart className="size-4" />
            NSE Quote
          </TabsTrigger>
          <TabsTrigger value="fii-dii" className="gap-1.5 py-2">
            <Landmark className="size-4" />
            FII / DII
          </TabsTrigger>
          <TabsTrigger value="breadth" className="gap-1.5 py-2">
            <Activity className="size-4" />
            Advances / Declines
          </TabsTrigger>
          <TabsTrigger value="options" className="gap-1.5 py-2">
            <Scale className="size-4" />
            Options / PCR
          </TabsTrigger>
        </TabsList>

        <TabsContent value="quote">
          <NseQuoteTab />
        </TabsContent>
        <TabsContent value="fii-dii">
          <FiiDiiTab />
        </TabsContent>
        <TabsContent value="breadth">
          <AdvancesDeclinesTab />
        </TabsContent>
        <TabsContent value="options">
          <OptionsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
