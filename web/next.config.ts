import type { NextConfig } from "next";

// Proxy /api/* to the FastAPI layer so the browser sees same-origin — kills CORS
// preflight (critical for the SSE stream). FastAPI runs on :8800 (8000 is taken
// by the explainer static server in this dev setup).
const nextConfig: NextConfig = {
  async rewrites() {
    return [{ source: "/api/:path*", destination: "http://localhost:8800/api/:path*" }];
  },
};

export default nextConfig;
