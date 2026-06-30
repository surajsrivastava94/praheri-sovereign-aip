"use client";

import { useState } from "react";
import type { VerticalConfig, ActionResult } from "@/lib/api";
import { useVerticalObjects } from "@/lib/useVerticals";
import { useAction } from "@/lib/useGovernance";

// Procurement is action-centric (a budget/PO gate), not investigation-centric.
// Over-budget POs hit the SAME MLRO approval queue as an AML account freeze —
// proving the governance layer is workflow-agnostic.
export function ProcurementWorkspace({ config }: { config: VerticalConfig }) {
  const reqs = useVerticalObjects(config.key, "Requisition");
  const budgets = useVerticalObjects(config.key, "Budget");
  const action = useAction();
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const budget = budgets.data?.[0];
  const budgetRemaining = Number(budget?.properties?.remaining ?? 0);

  const submitPO = (reqId: string, amount: number) => {
    setMsg(null);
    action.mutate(
      {
        name: "approve_purchase_order",
        params: { requisition_id: reqId, amount, budget_remaining: budgetRemaining },
      },
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
    <div className="p-8 max-w-5xl">
      <div
        className="rounded-xl border border-border p-5 mb-6"
        style={{ background: `linear-gradient(180deg, ${config.accent_color}14, transparent)` }}
      >
        <div className="flex items-center gap-2.5 mb-1">
          <span className="text-2xl">{config.icon}</span>
          <h1 className="text-2xl">{config.name}</h1>
        </div>
        <p className="text-muted text-sm mb-2">{config.tagline}</p>
        <span className="inline-block rounded-md border border-border px-2 py-0.5 text-[0.7rem] text-muted font-mono">
          {config.regulator}
        </span>
      </div>

      {budget && (
        <div className="rounded-xl border border-border bg-surface p-4 mb-6">
          <div className="text-muted text-xs">
            Budget · {String(budget.properties.department)}
          </div>
          <div className="text-fg text-lg font-semibold mt-1">
            ₹{Number(budget.properties.remaining).toLocaleString("en-IN")} remaining
            <span className="text-muted text-sm font-normal">
              {" "}
              of ₹{Number(budget.properties.cap).toLocaleString("en-IN")}
            </span>
          </div>
        </div>
      )}

      <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">Requisitions</h2>
      <p className="text-muted text-xs mb-3">
        Submit a PO. Over-budget requests hit the same MLRO approval queue as an AML freeze.
      </p>
      <div className="space-y-3">
        {reqs.data?.map((r) => {
          const amount = Number(r.properties.amount);
          const over = amount > budgetRemaining;
          return (
            <div key={r.id} className="rounded-xl border border-border bg-surface p-4 flex items-center justify-between gap-4">
              <div>
                <div className="text-sm font-semibold text-fg">
                  {r.id} · ₹{amount.toLocaleString("en-IN")}
                  {over && <span className="ml-2 text-file text-xs">over budget</span>}
                </div>
                <div className="text-muted text-xs mt-0.5">{String(r.properties.description)}</div>
              </div>
              <button
                onClick={() => submitPO(r.id, amount)}
                disabled={action.isPending}
                className="px-3 py-1.5 rounded-lg text-xs font-medium border border-file/50 text-file hover:bg-file/10 transition-colors disabled:opacity-50 whitespace-nowrap"
              >
                🔒 Submit PO
              </button>
            </div>
          );
        })}
      </div>
      {msg && (
        <div className={["mt-3 text-xs", msg.kind === "ok" ? "text-clear" : "text-escalate"].join(" ")}>
          {msg.kind === "ok" ? "✓ " : "⚠ "}
          {msg.text}
        </div>
      )}
    </div>
  );
}
