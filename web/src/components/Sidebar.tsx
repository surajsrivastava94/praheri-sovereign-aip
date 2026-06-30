"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Phase 0 shell: AML hero pinned, sectors as a static list (wired to the
// /api/verticals registry in a later phase), Platform overview. Clicking a
// sector routes to its own workspace — the left-nav model that replaces the
// flat 10-tab Streamlit layout.
const NAV = [
  { href: "/aml", icon: "🛡️", label: "AML", sub: "Anti-Money-Laundering", hero: true },
  { href: "/sectors/insurance_siu", icon: "🚑", label: "Insurance SIU", sub: "Claims fraud" },
  { href: "/sectors/lending_ews", icon: "🏦", label: "Lending EWS", sub: "Early warning" },
  { href: "/sectors/wealth", icon: "📈", label: "Wealth", sub: "Suitability" },
  { href: "/sectors/corporate", icon: "🏢", label: "Corporate", sub: "UBO / ownership" },
  { href: "/sectors/procurement", icon: "📦", label: "Procurement", sub: "Maverick spend" },
  { href: "/platform", icon: "🌐", label: "Platform", sub: "One engine, all sectors" },
];

export function Sidebar() {
  const path = usePathname();
  return (
    <aside className="w-64 shrink-0 border-r border-hairline bg-surface/60 flex flex-col">
      <div className="px-5 py-5 border-b border-hairline">
        <div className="flex items-center gap-2.5">
          <span className="text-xl">🛡️</span>
          <span className="font-bold tracking-tight text-fg">Praheri</span>
        </div>
        <div className="eyebrow mt-2">Sovereign AIP</div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {NAV.map((item) => {
          const active = path === item.href || path?.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={[
                "block rounded-lg px-3 py-2.5 transition-colors",
                active
                  ? "bg-accent/12 text-fg ring-1 ring-accent/40"
                  : "text-muted hover:bg-surface-2 hover:text-fg",
              ].join(" ")}
            >
              <div className="flex items-center gap-2.5">
                <span className="text-base">{item.icon}</span>
                <span className="text-sm font-medium">{item.label}</span>
                {item.hero && (
                  <span className="ml-auto text-[0.6rem] font-mono uppercase tracking-wider text-accent">
                    hero
                  </span>
                )}
              </div>
              <div className="ml-[26px] text-[0.7rem] text-muted/80">{item.sub}</div>
            </Link>
          );
        })}
      </nav>
      <div className="px-5 py-4 border-t border-hairline text-[0.7rem] text-muted">
        Llama · on-prem · zero egress
      </div>
    </aside>
  );
}
