"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { RoleToggle } from "@/components/RoleToggle";
import { useVerticals } from "@/lib/useVerticals";

type NavItem = { href: string; icon: string; label: string; sub: string; hero?: boolean };

// Core console tabs stay pinned; the sector list is registry-driven (P4).
const CORE: NavItem[] = [
  { href: "/aml", icon: "🛡️", label: "AML", sub: "Anti-Money-Laundering", hero: true },
  { href: "/approvals", icon: "✅", label: "Approvals", sub: "MLRO sign-off gate" },
  { href: "/audit", icon: "📜", label: "Audit", sub: "Immutable trail" },
];
const PLATFORM: NavItem = { href: "/platform", icon: "🌐", label: "Platform", sub: "One engine, all sectors" };

// Fallback sector list (used while /api/verticals loads or if it fails).
const FALLBACK_SECTORS: NavItem[] = [
  { href: "/sectors/insurance_siu", icon: "🚑", label: "Insurance SIU", sub: "Claims fraud" },
  { href: "/sectors/lending_ews", icon: "🏦", label: "Lending EWS", sub: "Early warning" },
  { href: "/sectors/wealth", icon: "📈", label: "Wealth", sub: "Suitability" },
  { href: "/sectors/corporate", icon: "🏢", label: "Corporate", sub: "UBO / ownership" },
  { href: "/sectors/procurement", icon: "📦", label: "Procurement", sub: "Maverick spend" },
];

export function Sidebar() {
  const path = usePathname();
  const verticals = useVerticals();

  const sectors: NavItem[] = verticals.data
    ? verticals.data.verticals.map((v) => ({
        href: `/sectors/${v.key}`,
        icon: v.icon,
        label: v.name.split("—")[0].trim(),
        sub: v.tagline,
      }))
    : FALLBACK_SECTORS;

  const items = [...CORE, ...sectors, PLATFORM];

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
        {items.map((item) => {
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
      <div className="px-4 py-3 border-t border-hairline">
        <RoleToggle />
      </div>
      <div className="px-5 py-3 border-t border-hairline text-[0.7rem] text-muted">
        Llama · on-prem · zero egress
      </div>
    </aside>
  );
}
