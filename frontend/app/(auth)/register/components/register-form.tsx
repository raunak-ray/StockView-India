"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
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
import { useRegister } from "@/lib/hooks/use-auth";

const registerSchema = z
  .object({
    username: z
      .string()
      .min(3, "At least 3 characters")
      .max(50, "At most 50 characters")
      .regex(/^[a-zA-Z0-9_]+$/, "Letters, numbers and underscores only"),
    password: z.string().min(6, "At least 6 characters"),
    confirm: z.string().min(1, "Confirm your password"),
  })
  .refine((v) => v.password === v.confirm, {
    path: ["confirm"],
    message: "Passwords do not match",
  });

type RegisterFormValues = z.infer<typeof registerSchema>;

export function RegisterForm() {
  const router = useRouter();
  const register = useRegister();

  const {
    control,
    handleSubmit,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { username: "", password: "", confirm: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    try {
      await register.mutateAsync({
        username: values.username,
        password: values.password,
      });
      toast.success("Account created. Welcome aboard!");
      router.replace("/app");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Registration failed");
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
        <CardTitle className="text-2xl">Create your account</CardTitle>
        <CardDescription>
          Start researching, backtesting and paper trading.
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
                placeholder="trader_01"
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
                placeholder="At least 6 characters"
                autoComplete="new-password"
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
          <Controller
            name="confirm"
            control={control}
            render={({ field }) => (
              <Input
                label="Confirm password"
                type="password"
                placeholder="Repeat your password"
                autoComplete="new-password"
                leftIcon={<LockKeyhole className="size-4" />}
                value={field.value}
                onChange={(v) => {
                  setValue("confirm", v, { shouldValidate: true });
                  trigger("confirm");
                }}
                error={errors.confirm?.message}
              />
            )}
          />
          <StatefulButton
            type="submit"
            size="lg"
            className="w-full"
            state={
              register.isPending ? "loading" : register.isError ? "error" : "idle"
            }
            loadingText="Creating account…"
            errorText="Failed"
          >
            Create account
          </StatefulButton>
        </CardContent>
      </form>
      <CardFooter className="text-sm text-muted-foreground">
        <p>
          Already have an account?{" "}
          <Link href="/login" className="text-foreground underline-offset-4 hover:underline">
            Sign in
          </Link>
        </p>
      </CardFooter>
    </Card>
  );
}
