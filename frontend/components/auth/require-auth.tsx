"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";

import { Loader } from "@/components/motion/loader";
import { useMe } from "@/lib/hooks/use-auth";

export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isLoading } = useMe();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <Loader className="size-6 text-primary" />
      </div>
    );
  }

  return <>{children}</>;
}