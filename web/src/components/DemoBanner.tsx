"use client";

import { DEMO } from "@/lib/demoResolver";

// Persistent, unmissable framing for the hosted demo. Renders ONLY in the static
// demo build. Makes the sovereign distinction explicit: this instance runs on
// baked synthetic snapshots in your browser; the REAL console runs air-gapped
// on the institution's own hardware, no network egress. Links back to the
// run-it-locally steps on the explainer.
const RUN_LOCAL = "/#run";

export function DemoBanner() {
  if (!DEMO) return null;
  return (
    <div className="sticky top-0 z-40 border-b border-escalate/40 bg-escalate/10 backdrop-blur-sm">
      <div className="flex items-center gap-3 px-6 py-2 text-xs">
        <span className="inline-flex items-center gap-1.5 rounded-md border border-escalate/50 bg-escalate/15 px-2 py-0.5 font-mono uppercase tracking-wider text-escalate">
          <span className="h-1.5 w-1.5 rounded-full bg-escalate" />
          Demo
        </span>
        <span className="text-fg/90">
          You&apos;re exploring a hosted walkthrough on <b>synthetic data</b> —
          feel the real clicks, graphs and STR drafting.
        </span>
        <span className="hidden text-muted sm:inline">
          The production console runs <b className="text-fg/80">air-gapped on your own hardware</b>, no
          network egress.
        </span>
        <a
          href={RUN_LOCAL}
          className="ml-auto shrink-0 rounded-md border border-accent/50 px-2.5 py-1 font-mono text-[0.7rem] text-accent transition-colors hover:bg-accent hover:text-[#04101f]"
        >
          Run the sovereign console →
        </a>
      </div>
    </div>
  );
}
