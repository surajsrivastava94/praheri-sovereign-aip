"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { getJSON, type Alert, type GraphData } from "@/lib/api";
import { useInvestigation } from "@/lib/useInvestigation";
import { GraphCanvas } from "@/components/GraphCanvas";
import { RecommendationBadge } from "@/components/RecommendationBadge";
import { SignalCards } from "@/components/SignalCards";
import { WhyTrail } from "@/components/WhyTrail";
import { StrPanel } from "@/components/StrPanel";
import { ObjectInspector } from "@/components/ObjectInspector";
import { OagRagPanel } from "@/components/OagRagPanel";

export default function AmlPage() {
  const [alertId, setAlertId] = useState("ALERT-R001");

  const alerts = useQuery({ queryKey: ["alerts"], queryFn: () => getJSON<Alert[]>("/api/alerts") });
  const graph = useQuery({
    queryKey: ["graph", alertId],
    queryFn: () => getJSON<GraphData>(`/api/alerts/${alertId}/graph`),
  });
  const inv = useInvestigation(alertId);

  return (
    <div className="p-8 max-w-6xl">
      <div className="eyebrow">AML · Anti-Money-Laundering · the hero</div>
      <h1 className="text-3xl mt-1 mb-1">Investigation</h1>
      <p className="text-muted text-sm mb-6">
        Llama traverses the typed ontology, exposes the fraud ring, and recommends an
        action — grounded in cited objects and policy. Served from the FastAPI layer
        over the unchanged on-prem engine.
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

      {/* recommendation header */}
      <section className="mb-8">
        {inv.isLoading && <div className="text-muted text-sm">Investigating…</div>}
        {inv.error && <div className="text-file text-sm">Investigation error: {String(inv.error)}</div>}
        {inv.data && (
          <div className="flex flex-wrap items-center gap-3">
            <RecommendationBadge recommendation={inv.data.recommendation} />
            <span className="text-muted text-sm">
              Typology: <span className="text-fg capitalize">{inv.data.typology}</span>
            </span>
            <SourceBadge source={inv.data.source} />
          </div>
        )}
      </section>

      {/* fraud-ring graph */}
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

      {/* detected signals */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-fg mb-2 border-l-2 border-accent pl-2.5">
          Detected signals
        </h2>
        {inv.data && <SignalCards signals={inv.data.signals} />}
      </section>

      {/* why this recommendation */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-fg mb-3 border-l-2 border-accent pl-2.5">
          Why this recommendation
        </h2>
        {inv.data && <WhyTrail inv={inv.data} />}
      </section>

      {/* suspicious transaction report — cached-first, live-stream opt-in */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-fg mb-3 border-l-2 border-accent pl-2.5">
          Suspicious Transaction Report
        </h2>
        {inv.data && <StrPanel inv={inv.data} />}
      </section>

      {/* object drill-down — the ontology is a queryable graph */}
      <section className="mb-8">
        <h2 className="text-sm font-semibold text-fg mb-1 border-l-2 border-accent pl-2.5">
          Inspect a cited object
        </h2>
        <p className="text-muted text-xs mb-3">
          The ontology is a live graph, not a chatbot — pick any object to see its real
          properties and links.
        </p>
        {inv.data && (
          <ObjectInspector ids={[...inv.data.cited_ids, ...inv.data.objects_touched]} />
        )}
      </section>

      {/* OAG vs RAG — the differentiator */}
      <section>
        <h2 className="text-sm font-semibold text-fg mb-1 border-l-2 border-accent pl-2.5">
          OAG vs RAG — why structured objects win
        </h2>
        <p className="text-muted text-xs mb-3">
          Same ring, two retrieval strategies. OAG keeps the links; RAG flattens them to text.
        </p>
        {inv.data && <OagRagPanel inv={inv.data} />}
      </section>
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
      title={cached ? "Replayed from golden cache (instant, crash-proof)" : "Generated live by Llama"}
    >
      <span className={["h-1.5 w-1.5 rounded-full", cached ? "bg-muted" : "bg-clear"].join(" ")} />
      {cached ? "cached" : "live"}
    </span>
  );
}
