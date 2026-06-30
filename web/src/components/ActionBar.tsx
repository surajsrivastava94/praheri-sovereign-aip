"use client";

import { useState } from "react";
import type { Investigation, ActionResult } from "@/lib/api";
import { useAction } from "@/lib/useGovernance";

// Governed actions. The model never writes data — it proposes; a human decides.
// Clear/Escalate are low-stakes (execute + log immediately). 🔒 Freeze/STR are
// high-stakes — they route to the MLRO approval queue. Everything is audited.
type Btn = { name: string; label: string; locked?: boolean; params: (inv: Investigation) => Record<string, unknown> };

const BUTTONS: Btn[] = [
  { name: "clear_alert", label: "Clear", params: (i) => ({ alert_id: i.alert_id, rationale: i.rationale.slice(0, 200) }) },
  { name: "escalate_alert_to_case", label: "Escalate", params: (i) => ({ alert_id: i.alert_id, reason: i.typology }) },
  { name: "request_account_freeze", label: "Propose Freeze", locked: true, params: (i) => ({ account_id: i.account_id, reason: i.typology }) },
  { name: "file_str", label: "Propose STR", locked: true, params: (i) => ({ case_id: i.alert_id, narrative: i.str_narrative || i.rationale }) },
];

export function ActionBar({ inv }: { inv: Investigation }) {
  const action = useAction();
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const run = (b: Btn) => {
    setMsg(null);
    action.mutate(
      { name: b.name, params: b.params(inv) },
      {
        onSuccess: (r: ActionResult) =>
          setMsg({
            kind: "ok",
            text:
              r.status === "PENDING_APPROVAL"
                ? `Routed to MLRO queue (${r.ref?.slice(0, 8)}) — see Approvals.`
                : `Executed: ${String(r.result ?? r.status)}`,
          }),
        onError: (e: Error) => setMsg({ kind: "err", text: e.message }),
      },
    );
  };

  return (
    <div>
      <p className="text-muted text-xs mb-2">
        The model never writes data — it <i>proposes</i>; a human decides. Clear/Escalate
        log immediately; 🔒 actions wait in the MLRO queue. Everything is audited.
      </p>
      <div className="flex flex-wrap gap-2">
        {BUTTONS.map((b) => (
          <button
            key={b.name}
            onClick={() => run(b)}
            disabled={action.isPending}
            title={b.locked ? "High-stakes — requires MLRO approval" : "Low-stakes — logged immediately"}
            className={[
              "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors disabled:opacity-50",
              b.locked
                ? "border-file/50 text-file hover:bg-file/10"
                : "border-border text-fg hover:border-accent/50",
            ].join(" ")}
          >
            {b.locked ? "🔒 " : ""}
            {b.label}
          </button>
        ))}
      </div>
      {msg && (
        <div className={["mt-2 text-xs", msg.kind === "ok" ? "text-clear" : "text-escalate"].join(" ")}>
          {msg.kind === "ok" ? "✓ " : "⚠ "}
          {msg.text}
        </div>
      )}
    </div>
  );
}
