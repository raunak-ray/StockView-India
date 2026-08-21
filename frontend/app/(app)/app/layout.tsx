import type { Metadata } from "next";

import { AppShell } from "./components/app-shell";

export const metadata: Metadata = {
  title: "StockView India — App",
};

export default function AppLayout({ children }: LayoutProps<"/app">) {
  return <AppShell>{children}</AppShell>;
}
