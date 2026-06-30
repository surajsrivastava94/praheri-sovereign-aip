import localFont from "next/font/local";

// Bundled locally (no Google Fonts CDN) — preserves the sovereignty / zero-egress
// story. Same woff2 the Streamlit console + explainer use. Inter is variable.
export const inter = localFont({
  src: "../../public/fonts/inter.woff2",
  weight: "100 900",
  variable: "--font-sans",
  display: "swap",
});

export const ibmPlexMono = localFont({
  src: [
    { path: "../../public/fonts/ibmplexmono-400.woff2", weight: "400", style: "normal" },
    { path: "../../public/fonts/ibmplexmono-500.woff2", weight: "500", style: "normal" },
  ],
  variable: "--font-mono",
  display: "swap",
});
