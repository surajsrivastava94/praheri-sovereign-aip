"use client";

import { useRole, type Role } from "@/lib/role";

const OPTS: { value: Role; label: string }[] = [
  { value: "analyst", label: "🔍 Analyst" },
  { value: "mlro", label: "✅ MLRO" },
];

// Demo role switch. Analyst proposes; MLRO approves high-stakes actions.
export function RoleToggle() {
  const { role, setRole } = useRole();
  return (
    <div>
      <div className="eyebrow mb-1.5">Acting as</div>
      <div className="flex gap-1 rounded-lg border border-border p-1">
        {OPTS.map((o) => (
          <button
            key={o.value}
            onClick={() => setRole(o.value)}
            className={[
              "flex-1 rounded-md px-2 py-1 text-xs font-medium transition-colors",
              role === o.value ? "bg-accent/15 text-fg ring-1 ring-accent/40" : "text-muted hover:text-fg",
            ].join(" ")}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  );
}
