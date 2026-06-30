"use client";

import { use } from "react";

// Phase 0 placeholder — the generic SectorWorkspace (driven by VerticalConfig
// from /api/verticals) lands in a later phase. For now it confirms routing +
// the left-nav model work.
export default function SectorPage({ params }: { params: Promise<{ key: string }> }) {
  const { key } = use(params);
  return (
    <div className="p-8">
      <div className="eyebrow">Sector workspace</div>
      <h1 className="text-3xl mt-1 mb-2 capitalize">{key.replace(/_/g, " ")}</h1>
      <p className="text-muted text-sm max-w-prose">
        Placeholder. In a later phase this becomes the generic sector cockpit
        (Investigate / Approvals / Audit) rendered from the vertical's config —
        the same engine, a different ontology.
      </p>
    </div>
  );
}
