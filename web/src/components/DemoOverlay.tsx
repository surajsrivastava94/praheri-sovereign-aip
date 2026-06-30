"use client";

import { useRouter } from "next/navigation";
import { useDemo } from "@/lib/demo";
import { DEMO_STEPS } from "@/lib/demoSteps";

// The persistent guided-demo banner (fixed at the top, above page content). Next/
// Back navigate to the step's route, then advance — route-aware, unlike Streamlit.
export function DemoOverlay() {
  const router = useRouter();
  const { active, index, next, prev, restart, stop } = useDemo();

  if (!active) return null;
  const step = DEMO_STEPS[index];
  const total = DEMO_STEPS.length;

  const go = (dir: "next" | "prev") => {
    const target = DEMO_STEPS[dir === "next" ? Math.min(index + 1, total - 1) : Math.max(index - 1, 0)];
    if (target.href) router.push(target.href);
    dir === "next" ? next() : prev();
  };

  return (
    <div className="sticky top-0 z-50 border-b border-accent/40 bg-[#0b1120]/95 backdrop-blur px-6 py-3">
      <div className="flex items-start gap-4 max-w-6xl">
        <span className="shrink-0 rounded-full bg-accent/15 text-accent text-xs font-mono px-2.5 py-1 ring-1 ring-accent/40">
          🎬 {step.n}/{total}
        </span>
        <div className="flex-1 min-w-0">
          <div className="text-fg text-sm font-semibold">{step.title}</div>
          <div className="text-muted text-sm mt-0.5 leading-relaxed">{step.say}</div>
          <div className="text-accent/80 text-xs mt-1 italic">→ {step.action}</div>
        </div>
        <div className="shrink-0 flex items-center gap-1.5">
          <button
            onClick={() => go("prev")}
            disabled={index === 0}
            className="px-2.5 py-1 rounded-lg border border-border text-muted hover:text-fg text-xs disabled:opacity-40"
          >
            Back
          </button>
          <button
            onClick={() => go("next")}
            disabled={index === total - 1}
            className="px-2.5 py-1 rounded-lg bg-accent text-[#04101f] font-medium text-xs disabled:opacity-40"
          >
            Next
          </button>
          <button onClick={restart} className="px-2.5 py-1 rounded-lg border border-border text-muted hover:text-fg text-xs">
            Restart
          </button>
          <button onClick={stop} className="px-2 py-1 rounded-lg text-muted hover:text-fg text-xs" title="Close">
            ✕
          </button>
        </div>
      </div>
    </div>
  );
}
