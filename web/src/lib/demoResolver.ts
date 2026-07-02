// ─────────────────────────────────────────────────────────────────────────────
// DEMO MODE — the static, sovereign-safe twin of the console.
//
// When NEXT_PUBLIC_DEMO=1, the app is built as a static export (no FastAPI, no
// Ollama, no network egress). Every /api/* call is resolved from baked-in JSON
// snapshots captured from the real engine (public/demo-data/*), so the console
// renders BYTE-FOR-BYTE the same components — it doesn't mimic the console, it
// IS the console, fed from a local snapshot.
//
// This file is inert unless the flag is on: getJSON/postJSON/useEventStream only
// branch here when DEMO is true, so normal `next dev` against FastAPI is unchanged.
// ─────────────────────────────────────────────────────────────────────────────

import type {
  ActionResult,
  AuditRow,
  GraphData,
  PendingItem,
} from "@/lib/api";

export const DEMO = process.env.NEXT_PUBLIC_DEMO === "1";

// Where the baked JSON lives, relative to the deployed base path. In a static
// export under a subpath (e.g. /console), assets resolve from that prefix; we
// read it from the same env Next uses for basePath so links + data agree.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";
const DATA = `${BASE}/demo-data`;

async function fetchData<T>(rel: string): Promise<T> {
  const r = await fetch(`${DATA}/${rel}`);
  if (!r.ok) throw new Error(`demo-data ${rel} → ${r.status}`);
  return r.json() as Promise<T>;
}

// Split "/api/alerts/ALERT-R001/graph?x=y" into segments + query params.
function parse(path: string): { seg: string[]; q: URLSearchParams } {
  const [p, qs] = path.replace(/^\/api\//, "").split("?");
  return { seg: p.split("/").filter(Boolean), q: new URLSearchParams(qs ?? "") };
}

// ── AML alert bundle cache (one file per alert holds all 5 sub-resources) ──────
type AmlBundle = {
  investigate: unknown;
  graph: unknown;
  confidence: unknown;
  timeline: unknown;
  rag: unknown;
};
const amlCache: Record<string, Promise<AmlBundle>> = {};
function amlBundle(id: string): Promise<AmlBundle> {
  return (amlCache[id] ??= fetchData<AmlBundle>(`aml/${id}.json`));
}

type VertBundle = {
  config: unknown;
  alerts: unknown[];
  defaultRoot?: string;
  investigate?: Record<string, unknown>;
  graph?: Record<string, unknown>;
  objectsByType?: Record<string, unknown[]>;
};
const vertCache: Record<string, Promise<VertBundle>> = {};
function vertBundle(key: string): Promise<VertBundle> {
  return (vertCache[key] ??= fetchData<VertBundle>(`verticals/${key}.json`));
}

// ── GET resolver ──────────────────────────────────────────────────────────────
export async function demoGet<T>(path: string): Promise<T> {
  const { seg, q } = parse(path);
  // seg: ["alerts"] | ["alerts", id, sub] | ["objects", id] | ["verticals", ...] | ["approvals"|"audit"]
  const [root, a, b] = seg;

  if (root === "alerts" && !a) return fetchData<T>("alerts.json");

  if (root === "alerts" && a) {
    const bundle = await amlBundle(a);
    const sub = (b ?? "investigate") as keyof AmlBundle;
    return bundle[sub] as T;
  }

  if (root === "objects" && a) {
    return fetchData<T>(`objects/${decodeURIComponent(a)}.json`);
  }

  if (root === "verticals" && !a) {
    // registry + counters
    return fetchData<T>("verticals.json");
  }

  if (root === "verticals" && a) {
    const bundle = await vertBundle(a);
    if (b === "alerts") return (bundle.alerts ?? []) as T;
    if (b === "investigate") {
      const root_id = q.get("root_id") ?? bundle.defaultRoot ?? "";
      return (bundle.investigate?.[root_id] ?? bundle.investigate?.[bundle.defaultRoot ?? ""]) as T;
    }
    if (b === "graph") {
      const root_id = q.get("root_id") ?? bundle.defaultRoot ?? "";
      return ((bundle.graph?.[root_id] ??
        bundle.graph?.[bundle.defaultRoot ?? ""]) ?? { nodes: [], edges: [] }) as T;
    }
    if (b === "objects") {
      const type = q.get("type") ?? "";
      return ((bundle.objectsByType?.[type]) ?? []) as T;
    }
  }

  if (root === "approvals") return store.approvals() as T;
  if (root === "audit") return store.audit() as T;

  throw new Error(`demo: no resolver for GET ${path}`);
}

// ── in-memory governance store (session-scoped; resets on reload — honest for a demo) ──
type Pending = PendingItem;
const seededAudit: AuditRow[] = [
  {
    id: "seed-1",
    ts: "demo",
    event: "system",
    actor: "system",
    role: "system",
    action: "demo_session_start",
    params: {},
    result: "in-memory · resets on reload",
    model: "llama3.1:8b (snapshot)",
  },
];

let pending: Pending[] = [];
let audit: AuditRow[] = [...seededAudit];
let refN = 1;

function nowLabel(): string {
  // Static export forbids Date.now() nondeterminism at build; at runtime in the
  // browser it's fine. Guard so SSR/prerender doesn't call it.
  if (typeof window === "undefined") return "demo";
  return new Date().toISOString().replace("T", " ").slice(0, 19);
}

const HIGH_STAKES = new Set([
  "request_account_freeze",
  "file_str",
  "refer_to_siu",
  "flag_misselling",
  "escalate_kyc_review",
  "margin_call",
  "downgrade_rating",
]);

export const store = {
  approvals: () => [...pending],
  audit: () => [...audit].reverse(),
  reset: () => {
    pending = [];
    audit = [...seededAudit];
    refN = 1;
  },
  // propose/run an action as a role
  action(name: string, role: string, params: Record<string, unknown>): ActionResult {
    const overBudget =
      name === "approve_purchase_order" &&
      Number(params.amount ?? 0) > Number(params.budget_remaining ?? 0);
    const needsApproval = HIGH_STAKES.has(name) || overBudget;

    if (needsApproval && role !== "MLRO") {
      const ref = `demo-${String(refN++).padStart(4, "0")}`;
      pending.push({
        ref,
        action: name,
        params,
        proposed_by: role,
        ts: nowLabel(),
        status: "PENDING_APPROVAL",
      });
      audit.push({
        id: ref,
        ts: nowLabel(),
        event: "proposed",
        actor: role,
        role,
        action: name,
        params,
        result: "PENDING_APPROVAL",
        model: "llama3.1:8b (snapshot)",
      });
      return { status: "PENDING_APPROVAL", ref };
    }
    // low-stakes or MLRO acting directly → execute immediately
    audit.push({
      id: `demo-${String(refN++).padStart(4, "0")}`,
      ts: nowLabel(),
      event: "executed",
      actor: role,
      role,
      action: name,
      params,
      result: "OK",
      model: "llama3.1:8b (snapshot)",
    });
    return { status: "OK", result: "executed (demo)" };
  },
  approve(ref: string, role: string): ActionResult {
    const item = pending.find((p) => p.ref === ref);
    if (!item) throw new Error(`no pending action ${ref}`);
    pending = pending.filter((p) => p.ref !== ref);
    audit.push({
      id: ref,
      ts: nowLabel(),
      event: "approved",
      actor: role,
      role,
      action: item.action,
      params: item.params,
      result: "EXECUTED",
      model: "llama3.1:8b (snapshot)",
    });
    return { status: "EXECUTED", ref, result: "approved + executed (demo)" };
  },
};

// ── POST resolver ─────────────────────────────────────────────────────────────
export function demoPost<T>(path: string, body: unknown): Promise<T> {
  const { seg } = parse(path);
  const b = (body ?? {}) as { role?: string; params?: Record<string, unknown> };
  const role = b.role ?? "Analyst";

  // /api/actions/{name}
  if (seg[0] === "actions" && seg[1]) {
    return Promise.resolve(store.action(seg[1], role, b.params ?? {}) as T);
  }
  // /api/approvals/{ref}/approve
  if (seg[0] === "approvals" && seg[1] && seg[2] === "approve") {
    return Promise.resolve(store.approve(seg[1], role) as T);
  }
  return Promise.reject(new Error(`demo: no resolver for POST ${path}`));
}

// ── SSE replay: type the cached narrative out token-by-token ────────────────────
// Mirrors the real /str/stream so the "Stream live" button animates identically.
export async function demoStream(
  path: string,
  onToken: (t: string) => void,
  onDone: () => void,
): Promise<void> {
  // path: /api/alerts/{id}/str/stream
  const { seg } = parse(path);
  const id = seg[1];
  const bundle = await amlBundle(id);
  const text = String((bundle.investigate as { str_narrative?: string })?.str_narrative ?? "");
  // chunk into word-ish tokens for a natural typing cadence
  const tokens = text.match(/\S+\s*/g) ?? [text];
  let i = 0;
  const tick = () => {
    if (i >= tokens.length) return onDone();
    onToken(tokens[i++]);
    setTimeout(tick, 18);
  };
  tick();
}

export type { GraphData };
