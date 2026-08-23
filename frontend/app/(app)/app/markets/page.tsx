"use client";

import { Card, CardContent } from "@/components/ui/card";
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
        <TabsList aria-label="Market data sections">
          <TabsTrigger value="quote">📊 NSE Quote</TabsTrigger>
          <TabsTrigger value="fii-dii">🏛 FII / DII</TabsTrigger>
          <TabsTrigger value="breadth">📉 Advances/Declines</TabsTrigger>
          <TabsTrigger value="options">⚖ Options / PCR</TabsTrigger>
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

      <Card className="border-dashed bg-transparent shadow-none">
        <CardContent className="px-4 py-3 text-center text-xs text-muted-foreground">
          Data via NSE India with layered public fallbacks · cached for a few
          minutes between refreshes.
        </CardContent>
      </Card>
    </div>
  );
}
