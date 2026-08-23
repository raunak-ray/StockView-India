"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity,
  Bell,
  Blocks,
  LayoutDashboard,
  LineChart,
  LogOut,
  Menu,
  PieChart,
  Search,
  Settings,
  Wallet,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { CommandPalette } from "@/components/search/command-palette";
import { MarketStatusChip } from "@/components/market/market-status-chip";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { RequireAuth } from "@/components/auth/require-auth";
import { useLogout, useMe } from "@/lib/hooks/use-auth";
import { cn } from "@/lib/utils";

const NAV = [
  { href: "/app", label: "Dashboard", icon: LayoutDashboard },
  { href: "/app/markets", label: "Markets", icon: Activity },
  { href: "/app/sectors", label: "Sectors", icon: PieChart },
  { href: "/app/compare", label: "Compare", icon: LineChart },
  { href: "/app/backtest", label: "Backtest", icon: Blocks },
  { href: "/app/paper-trading", label: "Paper Trading", icon: Wallet },
];

function brandLink() {
  return (
    <Link
      href="/app"
      className="flex h-14 items-center gap-2 border-b border-border px-5"
    >
      <span className="flex size-7 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
        SV
      </span>
      <span className="text-sm font-semibold">StockView</span>
    </Link>
  );
}

/** Nav rows shared by the desktop sidebar and the mobile sheet. */
function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  return (
    <>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV.map((item) => {
          const active =
            item.href === "/app"
              ? pathname === "/app"
              : pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-primary/5 hover:text-foreground",
                active && "bg-primary/10 text-foreground",
              )}
            >
              <item.icon className="size-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3">
        <Link
          href="/app/settings"
          onClick={onNavigate}
          className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-primary/5 hover:text-foreground"
        >
          <Settings className="size-4" />
          Settings
        </Link>
      </div>
    </>
  );
}

function Sidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh w-60 shrink-0 flex-col border-r border-border bg-card/40 md:flex">
      {brandLink()}
      <NavLinks />
    </aside>
  );
}

/** Hamburger drawer for small screens — same destinations as the sidebar. */
function MobileNav({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const pathname = usePathname();

  // Close the drawer whenever a navigation happens from inside it.
  useEffect(() => {
    onOpenChange(false);
  }, [pathname, onOpenChange]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="left" className="w-72 gap-0 p-0">
        <SheetHeader className="border-b border-border p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          {brandLink()}
        </SheetHeader>
        <div className="flex min-h-0 flex-1 flex-col">
          <NavLinks />
        </div>
      </SheetContent>
    </Sheet>
  );
}

function Topbar() {
  const { data: user } = useMe();
  const logout = useLogout();
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [navOpen, setNavOpen] = useState(false);

  const initials = (user?.username ?? "?").slice(0, 2).toUpperCase();

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur md:gap-4 md:px-6">
      <Button
        variant="ghost"
        size="icon"
        aria-label="Open navigation"
        className="md:hidden"
        onClick={() => setNavOpen(true)}
      >
        <Menu className="size-5" />
      </Button>
      <button
        type="button"
        onClick={() => setPaletteOpen(true)}
        className="flex items-center gap-2 rounded-lg border border-border bg-card px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:border-primary/40 hover:text-foreground md:w-80"
      >
        <Search className="size-4" />
        <span className="flex-1 truncate text-left">Search instruments…</span>
        <kbd className="hidden rounded border border-border px-1 text-[10px] md:block">
          ⌘K
        </kbd>
      </button>
      <div className="ml-auto flex items-center gap-2 md:gap-3">
        <span className="hidden sm:block">
          <MarketStatusChip />
        </span>
        <ThemeToggle />
        <Button variant="ghost" size="icon" aria-label="Alerts">
          <Bell className="size-4" />
        </Button>
        <Separator orientation="vertical" className="hidden h-6 md:block" />
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center gap-2 rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <Avatar className="size-8">
                <AvatarFallback>{initials}</AvatarFallback>
              </Avatar>
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel>
              {user?.username}
              <span className="block text-xs font-normal text-muted-foreground">
                {user?.role}
              </span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onClick={() => {
                toast.promise(logout.mutateAsync(), {
                  loading: "Logging out…",
                  success: "Logged out",
                  error: "Could not log out",
                });
              }}
            >
              <LogOut className="size-4" />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
      <MobileNav open={navOpen} onOpenChange={setNavOpen} />
    </header>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <div className="flex min-h-dvh bg-background">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar />
          <main className="flex-1 p-4 md:p-6">{children}</main>
        </div>
      </div>
    </RequireAuth>
  );
}
