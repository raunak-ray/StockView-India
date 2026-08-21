"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { Loader } from "@/components/motion/loader";
import { useLogout, useMe } from "@/lib/hooks/use-auth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading, isError } = useMe();
  const logout = useLogout();

  useEffect(() => {
    if (isLoading || user) return;

    // Auth is definitively dead (refresh already attempted by the api
    // client). Clear the stale cookies server-side BEFORE redirecting,
    // otherwise proxy.ts sees the leftover refresh cookie and bounces
    // us straight back to /app — an infinite loop.
    if (isError) {
      logout.mutateAsync().catch(() => undefined).finally(() => {
        router.replace("/login");
      });
      return;
    }

    router.replace("/login");
  }, [isLoading, user, isError, logout, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Loader className="size-6 text-primary" />
      </div>
    );
  }

  return <>{children}</>;
}
