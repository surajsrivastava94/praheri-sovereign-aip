// The scripted 3-minute walkthrough — ported from the Streamlit _DEMO_STEPS, with
// each "tab" mapped to a Next route so Back/Next actually navigate the console.
export type DemoStep = {
  n: number;
  title: string;
  href: string;
  action: string;
  say: string;
};

export const DEMO_STEPS: DemoStep[] = [
  {
    n: 1,
    title: "Hook — the sovereign OS",
    href: "/platform",
    action: "Point at the live counters + the cartridge tiles.",
    say: "An Indian bank cannot legally send this data to OpenAI — RBI forbids it. So we built the alternative on-prem on Llama. And it's not one app — it's an OS: one engine, six ontologies, zero lines of engine code changed per sector. Here's the flagship: financial crime.",
  },
  {
    n: 2,
    title: "Pick the hottest alert",
    href: "/aml",
    action: "The hottest alert (ALERT-R001) is selected by default.",
    say: "Open AML alerts, ranked by risk. Let's take the hottest — a funnel account.",
  },
  {
    n: 3,
    title: "Investigate → traverse",
    href: "/aml",
    action: "The fraud-ring graph is already traversed (cached, instant).",
    say: "Llama traverses the bank's ontology — accounts, transactions, devices — as structured objects. This is Ontology-Augmented Generation, not a chatbot guessing from text.",
  },
  {
    n: 4,
    title: "The ring lights up",
    href: "/aml",
    action: "Point at the lit-up fraud ring (mules → beneficiary) + confidence meter.",
    say: "There's the ring: mule accounts each fed sub-₹50,000 deposits to dodge reporting, all funnelling to one beneficiary. The engine detected the structuring pattern deterministically — 95% confidence, explained term by term.",
  },
  {
    n: 5,
    title: "STR narrative + signals",
    href: "/aml",
    action: "Scroll to the signals, the why-trail, and the draft STR; point at the cited IDs.",
    say: "It drafts a Suspicious Transaction Report, citing the actual account and transaction IDs as evidence, grounded in the bank's own AML policy. Recommendation: FILE.",
  },
  {
    n: 6,
    title: "Governance — propose, approve, audit",
    href: "/aml",
    action: "Propose Freeze, switch role to MLRO, approve on /approvals, then check /audit.",
    say: "The AI cannot act on its own. It proposes a freeze — which lands in the MLRO's queue. The officer approves, and every step is written to an immutable audit log: who, what, when, which model. Copilot, not autopilot.",
  },
  {
    n: 7,
    title: "OAG vs RAG",
    href: "/aml",
    action: "Run the OAG-vs-RAG comparison; contrast the decisive vs the hedged answer.",
    say: "Why structured objects? Side by side: OAG keeps the links and decides FILE with cited IDs. Naive RAG flattens the same facts to text — and hedges, because it can't reconstruct the ring.",
  },
  {
    n: 8,
    title: "Swap the sector — same engine",
    href: "/sectors/corporate",
    action: "Open Corporate, investigate the alert.",
    say: "Now the OS thesis. Same engine, same cockpit — a completely different sector. Corporate ownership: it unwinds a circular shell structure to the hidden beneficial owner. Zero engine code changed — Insurance, Lending, Wealth all run off the same loop.",
  },
  {
    n: 9,
    title: "Reusable governance",
    href: "/sectors/procurement",
    action: "Open Procurement, submit the over-budget PO.",
    say: "The governance layer is reusable too — this over-budget purchase order hits the exact same approval gate. One platform, every Reliance workflow. India shouldn't rent its intelligence — it should own it.",
  },
];
