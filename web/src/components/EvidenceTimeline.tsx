"use client";

import { useTimeline } from "@/lib/useAmlExtras";

// Ring transactions in chronological order. Sub-INR50,000 rows are flagged — the
// structuring tell (deposits kept just under the reporting threshold).
export function EvidenceTimeline({ alertId }: { alertId: string }) {
  const tl = useTimeline(alertId);
  if (!tl.data) return null;
  const { rows, total } = tl.data;

  return (
    <div>
      <div className="text-muted text-xs mb-3">
        Showing {rows.length} of {total} ring transactions, chronological.
      </div>
      <ol className="relative ml-2 border-l border-border pl-5 space-y-3">
        {rows.map((r) => (
          <li key={r.txn_id} className="relative">
            <span className="absolute -left-[23px] top-1.5 h-2 w-2 rounded-full bg-accent" />
            <div className="flex flex-wrap items-baseline gap-x-2 text-sm">
              <span className="text-muted font-mono text-[0.7rem]">
                {r.timestamp.replace("T", " ").slice(0, 19)}
              </span>
              <span className="font-mono text-xs text-fg">{r.from_account}</span>
              <span className="text-muted">→</span>
              <span className="font-mono text-xs text-fg">{r.to_account}</span>
              <span className="text-fg">₹{r.amount.toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
              <span className="text-muted text-xs">{r.channel}</span>
              {r.sub_threshold && (
                <span className="rounded border border-file/50 text-file px-1.5 py-0.5 text-[0.65rem]">
                  sub-₹50k
                </span>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
