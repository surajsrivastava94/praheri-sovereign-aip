import type { Signal } from "@/lib/api";

// One card per detected typology signal. evidence_ids render as monospace chips
// (the cited objects — same visual language as the graph's glowing nodes).
export function SignalCards({ signals }: { signals: Signal[] }) {
  if (signals.length === 0) {
    return <div className="text-muted text-sm">No typology signals fired.</div>;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {signals.map((sig, i) => (
        <div key={i} className="rounded-xl border border-border bg-surface p-4">
          <div className="flex items-center gap-2 mb-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-file" />
            <h3 className="text-sm font-semibold text-fg capitalize">{sig.typology}</h3>
          </div>
          <p className="text-muted text-sm leading-relaxed mb-3">{sig.detail}</p>
          <div className="flex flex-wrap gap-1.5">
            {sig.evidence_ids.map((id) => (
              <span
                key={id}
                className="rounded-md border border-border px-1.5 py-0.5 font-mono text-[0.7rem] text-muted"
              >
                {id}
              </span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
