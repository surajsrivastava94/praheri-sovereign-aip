"use client";

import Link from "next/link";
import { useVerticals } from "@/lib/useVerticals";

// The platform thesis, made literal: one engine, every sector. Counters are
// derived from the live registry server-side, so they can't drift from reality.
export default function PlatformPage() {
  const verticals = useVerticals();
  const counters = verticals.data?.counters;
  const cartridges = verticals.data?.verticals ?? [];

  const COUNTER_LABELS: { key: keyof NonNullable<typeof counters>; label: string }[] = [
    { key: "ontologies", label: "Ontologies" },
    { key: "object_types", label: "Object types" },
    { key: "link_types", label: "Link types" },
    { key: "actions", label: "Governed actions" },
  ];

  return (
    <div className="p-8 max-w-6xl">
      <div className="eyebrow">Sovereign AIP · platform</div>
      <h1 className="text-3xl mt-1 mb-1">One engine, every sector</h1>
      <p className="text-muted text-sm mb-6 max-w-prose">
        The same typed-ontology engine — OAG traversal, signal detection, governed
        actions, audit — runs every vertical below. Each is a config cartridge:
        <span className="text-fg"> 0 lines of engine code per vertical.</span>
      </p>

      {/* engine box */}
      <div className="rounded-xl border border-accent/40 bg-accent/5 p-5 mb-6">
        <div className="text-sm font-semibold text-accent mb-1">Praheri engine (Llama · on-prem)</div>
        <div className="text-muted text-sm">
          Triage → traverse → detect → decide → govern → audit. Shared across sectors.
        </div>
      </div>

      {/* live counters */}
      {counters && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
          {COUNTER_LABELS.map((c) => (
            <div key={c.key} className="rounded-xl border border-border bg-surface p-4 text-center">
              <div className="text-3xl font-semibold text-fg">{counters[c.key]}</div>
              <div className="text-muted text-xs mt-1">{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {/* cartridge tiles */}
      <h2 className="text-sm font-semibold text-fg mb-3 border-l-2 border-accent pl-2.5">Cartridges</h2>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {cartridges.map((v) => (
          <Link
            key={v.key}
            href={`/sectors/${v.key}`}
            className="rounded-xl border border-border bg-surface p-4 hover:border-accent/50 transition-colors block"
            style={{ borderTop: `2px solid ${v.accent_color}` }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{v.icon}</span>
              <span className="text-sm font-semibold text-fg">{v.name.split("—")[0].trim()}</span>
            </div>
            <p className="text-muted text-xs mb-2">{v.tagline}</p>
            <span className="inline-block rounded border border-border px-1.5 py-0.5 text-[0.65rem] text-muted font-mono">
              {v.regulator}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
