"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { useForm, Controller } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { LockKeyhole, UserRound } from "lucide-react";
import { toast } from "sonner";

import { Input } from "@/components/motion/input";
import { StatefulButton } from "@/components/motion/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useLogin } from "@/lib/hooks/use-auth";

const loginSchema = z.object({
  username: z.string().min(3, "Username is too short"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const login = useLogin();

  const {
    control,
    handleSubmit,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: "", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login.mutateAsync(values);
      toast.success(`Welcome back, ${values.username}`);
      router.replace(searchParams.get("next") ?? "/app");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Login failed");
    }
  });

  return (
    <Card className="w-full max-w-sm border-border bg-card/80 shadow-2xl backdrop-blur">
      <CardHeader className="space-y-1">
        <div className="mb-1 flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-sm font-bold text-primary-foreground">
            SV
          </span>
          <span className="text-sm font-semibold">StockView India</span>
        </div>
        <CardTitle className="text-2xl">Welcome back</CardTitle>
        <CardDescription>
          Sign in to continue to your trading terminal.
        </CardDescription>
      </CardHeader>
      <form onSubmit={onSubmit} noValidate>
        <CardContent className="space-y-4">
          <Controller
            name="username"
            control={control}
            render={({ field }) => (
              <Input
                label="Username"
                placeholder="demo"
                autoComplete="username"
                leftIcon={<UserRound className="size-4" />}
                value={field.value}
                onChange={(v) => {
                  setValue("username", v, { shouldValidate: true });
                  trigger("username");
                }}
                error={errors.username?.message}
              />
            )}
          />
          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                leftIcon={<LockKeyhole className="size-4" />}
                value={field.value}
                onChange={(v) => {
                  setValue("password", v, { shouldValidate: true });
                  trigger("password");
                }}
                error={errors.password?.message}
              />
            )}
          />
          <StatefulButton
            type="submit"
            size="lg"
            className="w-full"
            state={login.isPending ? "loading" : login.isError ? "error" : "idle"}
            loadingText="Signing in…"
            errorText="Failed"
          >
            Sign in
          </StatefulButton>
        </CardContent>
      </form>
      <CardFooter className="flex flex-col gap-2 text-sm text-muted-foreground">
        <p>
          Demo:{" "}
          <button
            type="button"
            className="text-foreground underline-offset-4 hover:underline"
            onClick={() => {
              setValue("username", "demo", { shouldValidate: true });
              setValue("password", "demo123", { shouldValidate: true });
              trigger();
            }}
          >
            demo / demo123
          </button>
        </p>
        <p>
          No account?{" "}
          <Link href="/register" className="text-foreground underline-offset-4 hover:underline">
            Create one
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}