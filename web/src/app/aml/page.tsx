"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getJSON, type Alert, type GraphData } from "@/lib/api";
import { GraphCanvas } from "@/components/GraphCanvas";
import { useTokenStream } from "@/lib/useEventStream";

export default function AmlPage() {
  const [alertId, setAlertId] = useState("ALERT-R001");

  const alerts = useQuery({ queryKey: ["alerts"], queryFn: () => getJSON<Alert[]>("/api/alerts") });
  const graph = useQuery({
    queryKey: ["graph", alertId],
    queryFn: () => getJSON<GraphData>(`/api/alerts/${alertId}/graph`),
  });

  const stream = useTokenStream();

  return (
    <div className="p-8 max-w-6xl">
      <div className="eyebrow">AML · Anti-Money-Laundering · the hero</div>
      <h1 className="text-3xl mt-1 mb-1">Investigation</h1>
      <p className="text-muted text-sm mb-6">
        Phase 0 spike — interactive fraud-ring graph + live Llama token stream, both
        served from the FastAPI layer over the unchanged engine.
      </p>

      {/* alert picker */}
      <div className="flex gap-2 flex-wrap mb-6">
        {alerts.data?.slice(0, 6).map((a) => (
          <button
            key={a.id}
            onClick={() => setAlertId(a.id)}
            className={[
              "px-3 py-1.5 rounded-lg text-xs font-mono border transition-colors",
              a.id === alertId
                ? "border-accent bg-accent/12 text-fg"
                : "border-border text-muted hover:text-fg hover:border-accent/50",
            ].join(" ")}
          >
            {a.id} · {a.properties.score.toFixed(0)}
          </button>
        ))}
      </div>

      {/* SPIKE 2 — interactive graph */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
          Fraud-ring graph (OAG traversal)
        </h2>
        {graph.isLoading && <div className="text-muted text-sm">Loading ring…</div>}
        {graph.error && <div className="text-file text-sm">Graph error: {String(graph.error)}</div>}
        {graph.data && <GraphCanvas data={graph.data} />}
        {graph.data && (
          <div className="text-muted text-xs mt-2">
            {graph.data.nodes.length} nodes · {graph.data.edges.length} edges ·{" "}
            <span className="text-clear">
              {graph.data.nodes.filter((n) => n.highlight).length} cited (glowing)
            </span>
          </div>
        )}
      </section>

      {/* SPIKE 1 — live token stream */}
      <section>
        <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
          Live Llama stream (SSE spike)
        </h2>
        <button
          onClick={() =>
            stream.start(
              `/api/ask/stream?q=${encodeURIComponent(
                "In two sentences, why is a funnel account with many sub-50000 deposits suspicious?",
              )}`,
            )
          }
          disabled={stream.streaming}
          className="px-4 py-2 rounded-lg bg-accent text-[#04101f] font-medium text-sm disabled:opacity-50"
        >
          {stream.streaming ? "Streaming…" : "Ask Llama (stream)"}
        </button>
        <div className="mt-3 rounded-xl border border-border bg-surface p-4 min-h-[90px] text-sm leading-relaxed text-fg">
          {stream.error ? (
            <span className="text-escalate">⚠ {stream.error}</span>
          ) : (
            <>
              {stream.text || <span className="text-muted">Click to stream a live answer…</span>}
              {stream.streaming && <span className="animate-pulse">▋</span>}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
