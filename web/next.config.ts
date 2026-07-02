import type { NextConfig } from "next";

// Two build modes:
//  • normal dev/build → proxy /api/* to FastAPI :8800 (same-origin, SSE-friendly).
//  • DEMO (NEXT_PUBLIC_DEMO=1) → static export: no backend, /api/* is resolved
//    client-side from baked JSON. Served under BASE_PATH (e.g. /console) on the
//    same static host as the explainer. Rewrites are unsupported in export mode,
//    so we drop them; the demo resolver needs no proxy.
const DEMO = process.env.NEXT_PUBLIC_DEMO === "1";
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig: NextConfig = DEMO
  ? {
      output: "export",
      basePath: BASE || undefined,
      images: { unoptimized: true },
      trailingSlash: true,
    }
  : {
      async rewrites() {
        return [{ source: "/api/:path*", destination: "http://localhost:8800/api/:path*" }];
      },
    };

export default nextConfig;
