import { QuoteView } from "./components/quote-view";

export default async function StockPage({
  params,
}: PageProps<"/app/stocks/[symbol]">) {
  const { symbol } = await params;
  return <QuoteView symbol={decodeURIComponent(symbol)} />;
}
