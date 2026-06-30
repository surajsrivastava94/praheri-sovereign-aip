"use client";

import { useState } from "react";
import { useConfidence } from "@/lib/useAmlExtras";

const BAND_COLOR: Record<string, string> = {
  High: "bg-clear",
  Medium: "bg-escalate",
  Low: "bg-muted",
};
const BAND_TEXT: Record<string, string> = {
  High: "text-clear",
  Medium: "text-escalate",
  Low: "text-muted",
};

// Deterministic, explainable confidence. The expandable breakdown is the
// "how is this computed?" answer — term-by-term, no black box.
export function ConfidenceMeter({ alertId }: { alertId: string }) {
  const conf = useConfidence(alertId);
  const [open, setOpen] = useState(false);

  if (!conf.data) return null;
  const { score, band, reasons } = conf.data;

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-muted text-xs">Confidence</span>
        <span className={["text-sm font-semibold", BAND_TEXT[band]].join(" ")}>
          {score}% · {band}
        </span>
      </div>
      <div className="h-2 rounded-full bg-bg/60 overflow-hidden">
        <div className={["h-full rounded-full transition-all", BAND_COLOR[band]].join(" ")} style={{ width: `${score}%` }} />
      </div>
      <button
        onClick={() => setOpen((v) => !v)}
        className="mt-2 text-muted hover:text-fg text-xs underline-offset-2 hover:underline"
      >
        {open ? "Hide" : "How is this computed?"}
      </button>
      {open && (
        <ul className="mt-2 space-y-1">
          {reasons.map((r, i) => (
            <li key={i} className="text-muted text-xs font-mono">
              · {r}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
