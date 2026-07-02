import type { Metadata } from "next";
import "./globals.css";
import { inter, ibmPlexMono } from "./fonts";
import { Providers } from "./providers";
import { Sidebar } from "@/components/Sidebar";
import { DemoOverlay } from "@/components/DemoOverlay";
import { DemoBanner } from "@/components/DemoBanner";

export const metadata: Metadata = {
  title: "Praheri — Sovereign AIP Console",
  description: "On-prem financial-crime investigation over a typed ontology.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${ibmPlexMono.variable} h-full`}>
      <body className="min-h-full">
        <Providers>
          <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              <DemoBanner />
              <DemoOverlay />
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
