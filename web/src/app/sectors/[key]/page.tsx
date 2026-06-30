"use client";

import { use } from "react";
import { useVerticals } from "@/lib/useVerticals";
import { SectorWorkspace } from "@/components/SectorWorkspace";
import { ProcurementWorkspace } from "@/components/ProcurementWorkspace";

// Generic sector router: resolve the config from the registry, then render the
// investigation workspace — or the procurement (budget/PO) workspace for the one
// action-centric vertical. One component set, every sector.
export default function SectorPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = use(params);
  const verticals = useVerticals();

  if (verticals.isLoading) {
    return <div className="p-8 text-muted text-sm">Loading sector…</div>;
  }

  const config = verticals.data?.verticals.find((v) => v.key === key);
  if (!config) {
    return (
      <div className="p-8">
        <h1 className="text-2xl mb-2">Unknown sector</h1>
        <p className="text-muted text-sm">No cartridge registered for “{key}”.</p>
      </div>
    );
  }

  return key === "procurement" ? (
    <ProcurementWorkspace config={config} />
  ) : (
    <SectorWorkspace config={config} />
  );
}
