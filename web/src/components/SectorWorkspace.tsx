"use client";

import { useState } from "react";
import type { VerticalConfig, ActionResult } from "@/lib/api";
import {
  useVerticalAlerts,
  useVerticalInvestigation,
  useVerticalGraph,
} from "@/lib/useVerticals";
import { useAction } from "@/lib/useGovernance";
import { GraphCanvas } from "@/components/GraphCanvas";
import { RecommendationBadge } from "@/components/RecommendationBadge";
import { SignalCards } from "@/components/SignalCards";

// One component renders ANY investigation vertical from its VerticalConfig +
// investigation output. The platform thesis: 0 lines of per-vertical UI code.
export function SectorWorkspace({ config }: { config: VerticalConfig }) {
  const [rootId, setRootId] = useState<string | null>(null);
  const alerts = useVerticalAlerts(config.key);
  const inv = useVerticalInvestigation(config.key, rootId);
  const graph = useVerticalGraph(config.key, rootId);
  const action = useAction();
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const runAction = (actionId: string) => {
    if (!rootId) return;
    setMsg(null);
    action.mutate(
      {
        name: "propose_vertical_action",
        params: { vertical: config.key, action_id: actionId, target_id: rootId, reason: inv.data?.recommendation ?? "" },
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
    <div className="p-8 max-w-6xl">
      {/* hero */}
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
        {config.use_case && <p className="text-muted/80 text-xs mt-3 max-w-prose">{config.use_case}</p>}
      </div>

      {/* KPI cards */}
      {config.kpi_cards.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-6">
          {config.kpi_cards.map((k) => (
            <div key={k.label} className="rounded-xl border border-border bg-surface p-4">
              <div className="text-muted text-xs">{k.label}</div>
              <div className="text-fg text-xl font-semibold mt-1">{k.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* alert queue */}
      <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">Alerts</h2>
      {alerts.isLoading && <div className="text-muted text-sm">Loading alerts…</div>}
      {alerts.error && <div className="text-file text-sm">Alerts error: {String(alerts.error)}</div>}
      <div className="flex flex-wrap gap-2 mb-6">
        {alerts.data?.map((a) => {
          const root =
            (a.linked_ids?.raised_on?.[0] as string) ??
            (a.properties?.root_id as string) ??
            a.id;
          return (
            <button
              key={a.id}
              onClick={() => setRootId(root)}
              className={[
                "px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors",
                rootId === root
                  ? "border-accent bg-accent/12 text-fg"
                  : "border-border text-muted hover:text-fg hover:border-accent/50",
              ].join(" ")}
            >
              Investigate {a.id}
            </button>
          );
        })}
      </div>

      {/* investigation */}
      {rootId && (
        <>
          <section className="mb-6">
            {inv.isLoading && <div className="text-muted text-sm">Investigating…</div>}
            {inv.data && (
              <div className="flex flex-wrap items-center gap-3">
                <RecommendationBadge recommendation={inv.data.recommendation} />
                <SourceBadge source={inv.data.source} />
              </div>
            )}
          </section>

          <section className="mb-8">
            <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
              Ring graph (OAG traversal)
            </h2>
            {graph.data && <GraphCanvas data={graph.data} />}
          </section>

          {inv.data && inv.data.signals.length > 0 && (
            <section className="mb-8">
              <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
                Detected signals
              </h2>
              <SignalCards signals={inv.data.signals} />
            </section>
          )}

          {inv.data?.narrative && (
            <section className="mb-8">
              <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">Narrative</h2>
              <div className="rounded-xl border border-border bg-surface p-4 text-sm leading-relaxed text-fg whitespace-pre-wrap">
                {inv.data.narrative}
              </div>
            </section>
          )}

          {/* governed actions — same MLRO queue as AML */}
          {config.actions.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
                Governed actions
              </h2>
              <p className="text-muted text-xs mb-2">
                Routed through the same MLRO approval queue + audit as every sector.
              </p>
              <div className="flex flex-wrap gap-2">
                {config.actions.map((a) => (
                  <button
                    key={a.id}
                    onClick={() => runAction(a.id)}
                    disabled={action.isPending}
                    title={a.requires_approval ? "High-stakes — requires MLRO approval" : ""}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium border border-file/50 text-file hover:bg-file/10 transition-colors disabled:opacity-50"
                  >
                    {a.requires_approval ? "🔒 " : ""}
                    {a.label}
                  </button>
                ))}
              </div>
              {msg && (
                <div className={["mt-2 text-xs", msg.kind === "ok" ? "text-clear" : "text-escalate"].join(" ")}>
                  {msg.kind === "ok" ? "✓ " : "⚠ "}
                  {msg.text}
                </div>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}

function SourceBadge({ source }: { source: "live" | "cached" }) {
  const cached = source === "cached";
  return (
    <span
      className={[
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.7rem] font-mono",
        cached ? "border-border text-muted" : "border-clear/50 text-clear",
      ].join(" ")}
    >
      <span className={["h-1.5 w-1.5 rounded-full", cached ? "bg-muted" : "bg-clear"].join(" ")} />
      {cached ? "cached" : "live"}
    </span>
  );
}
