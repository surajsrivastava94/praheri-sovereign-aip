"use client";

import { useQuery } from "@tanstack/react-query";
import { getJSON, type RagAnswer } from "@/lib/api";

// The RAG comparison answer is LIVE and slow (a model call each time), so this
// query is lazy: disabled by default, run only via refetch() on a button click.
export function useRag(alertId: string) {
  return useQuery({
    queryKey: ["rag", alertId],
    queryFn: () => getJSON<RagAnswer>(`/api/alerts/${alertId}/rag`),
    enabled: false,
    retry: false, // don't auto-retry a 503 when Ollama is down
  });
}
