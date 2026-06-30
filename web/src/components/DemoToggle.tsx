"use client";

import { useRouter } from "next/navigation";
import { useDemo } from "@/lib/demo";
import { DEMO_STEPS } from "@/lib/demoSteps";

// Sidebar control to start/stop the guided demo. Starting jumps to step 1's route.
export function DemoToggle() {
  const router = useRouter();
  const { active, start, stop } = useDemo();

  const onClick = () => {
    if (active) {
      stop();
    } else {
      start();
      if (DEMO_STEPS[0].href) router.push(DEMO_STEPS[0].href);
    }
  };

  return (
    <button
      onClick={onClick}
      className={[
        "w-full rounded-lg px-3 py-2 text-xs font-medium transition-colors border",
        active
          ? "border-accent/50 bg-accent/15 text-fg"
          : "border-border text-muted hover:text-fg hover:border-accent/50",
      ].join(" ")}
    >
      🎬 {active ? "Stop guided demo" : "Start guided demo"}
    </button>
  );
}
