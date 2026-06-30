// All calls go through the Next rewrite proxy (/api/* -> FastAPI :8800), so the
// browser sees same-origin (no CORS, SSE-friendly).

export async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json() as Promise<T>;
}

export type GraphNode = { id: string; kind: string; label: string; highlight: boolean };
export type GraphEdge = {
  source: string;
  target: string;
  kind: string;
  label: string;
  txn_id: string | null;
};
export type GraphData = { nodes: GraphNode[]; edges: GraphEdge[] };

export type Alert = {
  id: string;
  properties: { alert_id: string; account_id: string; rule: string; score: number; status: string };
};

export type Recommendation = "FILE" | "ESCALATE" | "CLEAR";

export type Signal = { typology: string; detail: string; evidence_ids: string[] };
export type PolicyCitation = { source: string; text: string };

// Mirrors the engine's investigate() dict (demo_cache/{alert_id}.json).
export type Investigation = {
  alert_id: string;
  account_id: string;
  objects_touched: string[];
  ring_summary: Record<string, unknown>; // counts/accounts/devices — not consumed this phase
  signals: Signal[];
  typology: string;
  recommendation: Recommendation;
  rationale: string;
  cited_ids: string[];
  policy_citations: PolicyCitation[];
  str_narrative: string;
  source: "live" | "cached";
};
