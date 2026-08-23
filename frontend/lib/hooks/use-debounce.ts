"use client";

import { useEffect, useState } from "react";

/**
 * Returns `value` only after it has stayed unchanged for `delayMs`.
 * Use for search inputs so queries fire after the user stops typing.
 */
export function useDebouncedValue<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);

  return debounced;
}
