import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The frontend calls the backend directly via NEXT_PUBLIC_API_BASE
  // (see .env.example). The dev server does NOT proxy /api/* — that
  // kept the backend URL implicit and hidden from the browser. Now
  // the URL is explicit in .env, and the backend's CORS settings
  // allow http://localhost:3000 in dev.
  //
  // If you ever need to proxy (e.g. to avoid CORS in a particular
  // deployment), add `rewrites()` here — but the standard setup is
  // a direct browser → backend call.
};

export default nextConfig;
