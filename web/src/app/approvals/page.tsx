"use client";

import { useApprovals, useApprove } from "@/lib/useGovernance";
import { useRole } from "@/lib/role";

export default function ApprovalsPage() {
  const { role } = useRole();
  const approvals = useApprovals();
  const approve = useApprove();

  const items = approvals.data ?? [];

  return (
    <div className="p-8 max-w-4xl">
      <div className="eyebrow">Governance · MLRO sign-off</div>
      <h1 className="text-3xl mt-1 mb-1">Pending approvals</h1>
      <p className="text-muted text-sm mb-6">
        The human gate. High-stakes actions the model proposed wait here until the{" "}
        <span className="text-fg">MLRO</span> approves them — switch the sidebar role to
        MLRO to act. Nothing proposed has touched the data yet.
      </p>

      {approvals.isLoading && <div className="text-muted text-sm">Loading…</div>}

      {items.length === 0 && !approvals.isLoading && (
        <div className="text-muted text-sm rounded-xl border border-border bg-surface p-5">
          No pending actions. Propose a freeze or STR from the AML investigation.
        </div>
      )}

      <div className="space-y-3">
        {items.map((it) => (
          <div key={it.ref} className="rounded-xl border border-border bg-surface p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-fg">{it.action}</div>
                <div className="text-muted text-xs mt-0.5">
                  proposed by {it.proposed_by} · <span className="font-mono">{it.ref.slice(0, 8)}</span>
                </div>
              </div>
              {role === "mlro" ? (
                <button
                  onClick={() => approve.mutate(it.ref)}
                  disabled={approve.isPending}
                  className="px-3 py-1.5 rounded-lg bg-clear text-[#04101f] font-medium text-xs disabled:opacity-50"
                >
                  {approve.isPending ? "Approving…" : "Approve"}
                </button>
              ) : (
                <span className="text-muted text-xs">Switch to MLRO to approve</span>
              )}
            </div>
            <pre className="mt-3 text-[0.7rem] text-muted font-mono bg-bg/40 rounded-lg p-2 overflow-x-auto">
              {JSON.stringify(it.params, null, 2)}
            </pre>
          </div>
        ))}
      </div>

      {approve.error && (
        <div className="text-escalate text-sm mt-3">⚠ {(approve.error as Error).message}</div>
      )}
    </div>
  );
}
