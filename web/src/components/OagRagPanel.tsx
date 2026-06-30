"use client";

import type { Investigation } from "@/lib/api";
import { useRag } from "@/lib/useRag";

// The differentiator: OAG (structured objects + links) vs naive RAG (flattened
// text, links stripped). OAG is instant from the cached investigation; RAG is a
// live model call over text — same facts, but it can't reconstruct the ring.
export function OagRagPanel({ inv }: { inv: Investigation }) {
  const rag = useRag(inv.alert_id);
  const ran = rag.isFetching || rag.isFetched;

  return (
    <div>
      <button
        onClick={() => rag.refetch()}
        disabled={rag.isFetching}
        className="mb-4 px-3 py-1.5 rounded-lg border border-border text-fg text-xs hover:border-accent/50 disabled:opacity-50"
      >
        {rag.isFetching ? "Running RAG…" : "Run side-by-side comparison"}
      </button>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* OAG — instant */}
        <div className="rounded-xl border border-clear/40 bg-clear/5 p-4">
          <div className="text-sm font-semibold text-clear mb-2">
            OAG — structured objects + links
          </div>
          <div className="text-sm text-fg mb-1">
            {inv.typology} → {inv.recommendation}
          </div>
          <p className="text-muted text-sm leading-relaxed">{inv.rationale}</p>
          <p className="text-muted/80 text-xs mt-2">
            Traversed the ring via explicit links; cites real object_ids.
          </p>
        </div>

        {/* RAG — live */}
        <div className="rounded-xl border border-file/40 bg-file/5 p-4">
          <div className="text-sm font-semibold text-file mb-2">
            RAG — flattened text, links stripped
          </div>
          {!ran && <p className="text-muted text-sm">Run the comparison to generate the RAG answer.</p>}
          {rag.isFetching && <p className="text-muted text-sm">RAG over text chunks…</p>}
          {rag.error && (
            <p className="text-escalate text-sm">⚠ {String((rag.error as Error).message ?? rag.error)}</p>
          )}
          {rag.data && (
            <>
              <p className="text-muted text-sm leading-relaxed whitespace-pre-wrap">{rag.data.answer}</p>
              <p className="text-muted/80 text-xs mt-2">
                Same facts as prose — but the links are gone, so it can&apos;t reconstruct the ring.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
