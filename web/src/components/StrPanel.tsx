"use client";

import type { Investigation } from "@/lib/api";
import { useTokenStream } from "@/lib/useEventStream";

// Structured-first STR: the cached narrative shows instantly; "Stream live" then
// streams a freshly-drafted STR token-by-token (the capability Streamlit lacked).
export function StrPanel({ inv }: { inv: Investigation }) {
  const stream = useTokenStream();
  const live = stream.streaming || !!stream.text || !!stream.error;

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <button
          onClick={() => stream.start(`/api/alerts/${inv.alert_id}/str/stream`)}
          disabled={stream.streaming}
          className="px-3 py-1.5 rounded-lg bg-accent text-[#04101f] font-medium text-xs disabled:opacity-50"
        >
          {stream.streaming ? "Streaming…" : "Stream live"}
        </button>
        <span className="text-muted text-xs">
          Instant from cache · stream live to watch Llama draft it, grounded in cited ids.
        </span>
      </div>
      <div className="rounded-xl border border-border bg-surface p-4 text-sm leading-relaxed text-fg whitespace-pre-wrap">
        {stream.error ? (
          <span className="text-escalate">⚠ {stream.error}</span>
        ) : live ? (
          <>
            {stream.text}
            {stream.streaming && <span className="animate-pulse">▋</span>}
          </>
        ) : (
          inv.str_narrative || <span className="text-muted">No narrative for this case.</span>
        )}
      </div>
    </div>
  );
}
