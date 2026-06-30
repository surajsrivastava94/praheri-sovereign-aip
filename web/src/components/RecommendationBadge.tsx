import type { Recommendation } from "@/lib/api";

// Color-coded recommendation pill. Status tokens (file/escalate/clear) are
// defined in globals.css and already used across the AML page.
const STYLE: Record<Recommendation, { ring: string; text: string; dot: string }> = {
  FILE: { ring: "border-file/50 bg-file/10", text: "text-file", dot: "bg-file" },
  ESCALATE: { ring: "border-escalate/50 bg-escalate/10", text: "text-escalate", dot: "bg-escalate" },
  CLEAR: { ring: "border-clear/50 bg-clear/10", text: "text-clear", dot: "bg-clear" },
};

export function RecommendationBadge({ recommendation }: { recommendation: Recommendation }) {
  const s = STYLE[recommendation];
  return (
    <span
      className={[
        "inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wide",
        s.ring,
        s.text,
      ].join(" ")}
    >
      <span className={["h-1.5 w-1.5 rounded-full", s.dot].join(" ")} />
      Recommendation: {recommendation}
    </span>
  );
}
