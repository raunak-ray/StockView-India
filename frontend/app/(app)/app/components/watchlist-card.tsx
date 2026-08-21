"use client";

import { Star } from "lucide-react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function WatchlistCard() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Star className="size-4 text-gold" /> My watchlist
        </CardTitle>
        <CardDescription>
          Track your favourite instruments in one place.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-1.5 rounded-lg border border-dashed border-border py-10 text-center">
          <p className="text-sm font-medium">Your watchlist is empty</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            Open any stock from the search bar (⌘K) and star it to add it here.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
