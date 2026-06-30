"use client";

import { useQuery } from "@tanstack/react-query";
import { getJSON, type Investigation } from "@/lib/api";

// Cached investigation for an alert. ALERT-R001 is golden-cached server-side,
// so this resolves instantly. Mirrors the inline `graph` query in aml/page.tsx.
export function useInvestigation(alertId: string) {
  return useQuery({
    queryKey: ["investigation", alertId],
    queryFn: () => getJSON<Investigation>(`/api/alerts/${alertId}/investigate`),
  });
}
