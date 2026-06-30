"use client";

import { useAudit } from "@/lib/useGovernance";

const EVENT_COLOR: Record<string, string> = {
  ACTION_PROPOSED: "text-escalate",
  ACTION_EXECUTED: "text-clear",
  ACTION_APPROVED_AND_EXECUTED: "text-clear",
};

export default function AuditPage() {
  const audit = useAudit();
  const rows = (audit.data ?? []).slice().reverse(); // newest first

  return (
    <div className="p-8 max-w-6xl">
      <div className="eyebrow">Governance · compliance artifact</div>
      <h1 className="text-3xl mt-1 mb-1">Immutable audit trail</h1>
      <p className="text-muted text-sm mb-6">
        Every proposed action and approval — with actor, role, timestamp and model.
        This append-only log proves who did what, and that a human (not the model)
        authorized each high-stakes action.
      </p>

      {audit.isLoading && <div className="text-muted text-sm">Loading…</div>}

      {rows.length === 0 && !audit.isLoading ? (
        <div className="text-muted text-sm rounded-xl border border-border bg-surface p-5">
          No audit entries yet.
        </div>
      ) : (
        <div className="rounded-xl border border-border bg-surface overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-muted text-xs border-b border-hairline">
                <th className="px-3 py-2 font-medium">Time</th>
                <th className="px-3 py-2 font-medium">Actor</th>
                <th className="px-3 py-2 font-medium">Role</th>
                <th className="px-3 py-2 font-medium">Event</th>
                <th className="px-3 py-2 font-medium">Action</th>
                <th className="px-3 py-2 font-medium">Result</th>
                <th className="px-3 py-2 font-medium">Model</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-b border-hairline/60 align-top">
                  <td className="px-3 py-2 text-muted font-mono text-[0.7rem] whitespace-nowrap">
                    {r.ts.replace("T", " ").slice(0, 19)}
                  </td>
                  <td className="px-3 py-2 text-fg whitespace-nowrap">{r.actor}</td>
                  <td className="px-3 py-2 text-muted">{r.role}</td>
                  <td className={["px-3 py-2 font-medium whitespace-nowrap", EVENT_COLOR[r.event] ?? "text-fg"].join(" ")}>
                    {r.event}
                  </td>
                  <td className="px-3 py-2 text-fg font-mono text-xs">{r.action}</td>
                  <td className="px-3 py-2 text-muted text-xs break-all">{String(r.result ?? "")}</td>
                  <td className="px-3 py-2 text-muted font-mono text-[0.7rem]">{r.model}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
