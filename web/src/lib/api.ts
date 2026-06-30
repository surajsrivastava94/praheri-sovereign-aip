// All calls go through the Next rewrite proxy (/api/* -> FastAPI :8800), so the
// browser sees same-origin (no CORS, SSE-friendly).

export async function getJSON<T>(path: string): Promise<T> {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json() as Promise<T>;
}

export async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    // surface the FastAPI {detail} message when present
    const detail = await r.json().catch(() => null);
    throw new Error(detail?.detail ?? `${path} → ${r.status}`);
  }
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

export type OntologyObject = {
  type: string;
  id: string;
  properties: Record<string, unknown>;
  linked_ids: Record<string, string[]>;
};

export type RagAnswer = { answer: string; mode: string };

export type PendingItem = {
  ref: string;
  action: string;
  params: Record<string, unknown>;
  proposed_by: string;
  ts: string;
  status: string;
};

export type AuditRow = {
  id: string;
  ts: string;
  event: string;
  actor: string;
  role: string;
  action: string;
  params: Record<string, unknown>;
  result: unknown;
  model: string;
};

export type ActionResult = { status: string; ref?: string; result?: unknown };
