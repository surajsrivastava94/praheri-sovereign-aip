import type { Investigation } from "@/lib/api";
import { RecommendationBadge } from "@/components/RecommendationBadge";

// "Why this recommendation" — a 3-step trail composed ONLY from the investigation
// dict (no new computation), so every line traces to what the engine produced:
//   1. signals detected  2. typology classified  3. recommendation + rationale.
export function WhyTrail({ inv }: { inv: Investigation }) {
  const policySources = Array.from(new Set(inv.policy_citations.map((p) => p.source)));

  return (
    <ol className="relative ml-2 border-l border-border pl-5 space-y-5">
      <Step n={1} title={`${inv.signals.length} signal${inv.signals.length === 1 ? "" : "s"} detected`}>
        {inv.signals.length > 0 ? (
          <ul className="space-y-1">
            {inv.signals.map((s, i) => (
              <li key={i} className="text-muted text-sm leading-relaxed">
                {s.detail}
              </li>
            ))}
          </ul>
        ) : (
          <span className="text-muted text-sm">No deterministic signals fired.</span>
        )}
      </Step>

      <Step n={2} title="Typology classified">
        <span className="text-sm text-fg capitalize">{inv.typology}</span>
        <span className="text-muted text-sm"> — Llama classified the structured ring objects.</span>
      </Step>

      <Step n={3} title="Recommendation">
        <div className="mb-2">
          <RecommendationBadge recommendation={inv.recommendation} />
        </div>
        <p className="text-muted text-sm leading-relaxed">{inv.rationale}</p>
        {policySources.length > 0 && (
          <p className="text-muted/80 text-xs mt-2">
            Grounded in {policySources.join(", ")}
          </p>
        )}
      </Step>
    </ol>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <li className="relative">
      <span className="absolute -left-[27px] flex h-5 w-5 items-center justify-center rounded-full border border-accent/50 bg-surface text-[0.65rem] font-mono text-accent">
        {n}
      </span>
      <h4 className="text-sm font-semibold text-fg mb-1">{title}</h4>
      {children}
    </li>
  );
}
