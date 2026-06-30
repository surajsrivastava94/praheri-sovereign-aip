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

// --- verticals / platform (P4) ---
export type KPI = { label: string; value: string; delta?: string | null };
export type SignalSpec = { id: string; label: string; why: string };
export type ActionSpec = { id: string; label: string; requires_approval: boolean };

export type VerticalConfig = {
  key: string;
  name: string;
  icon: string;
  accent_color: string;
  tagline: string;
  regulator: string;
  use_case: string;
  what_you_see: string;
  link_types: string[];
  kpi_cards: KPI[];
  signals: SignalSpec[];
  actions: ActionSpec[];
};

export type PlatformCounters = {
  ontologies: number;
  object_types: number;
  link_types: number;
  actions: number;
};

export type VerticalsResponse = { verticals: VerticalConfig[]; counters: PlatformCounters };

// --- confidence + evidence timeline (P5) ---
export type Confidence = { score: number; band: "High" | "Medium" | "Low"; reasons: string[] };

export type TimelineRow = {
  txn_id: string;
  from_account: string;
  to_account: string;
  amount: number;
  currency: string;
  channel: string;
  timestamp: string;
  sub_threshold: boolean;
};
export type Timeline = { rows: TimelineRow[]; total: number };

export type VerticalAlert = {
  id: string;
  properties: Record<string, unknown>;
  linked_ids: Record<string, string[]>;
};

// compute_vertical_investigation() output — note `narrative` (not str_narrative).
export type VerticalInvestigation = {
  vertical: string;
  root_id: string;
  objects_touched: string[];
  signals: Signal[];
  recommendation: Recommendation;
  cited_ids: string[];
  narrative: string;
  source: "live" | "cached";
};
