"use client";

import { useQuery } from "@tanstack/react-query";
import { getJSON, type Confidence, type Timeline } from "@/lib/api";

export function useConfidence(alertId: string | null) {
  return useQuery({
    queryKey: ["confidence", alertId],
    queryFn: () => getJSON<Confidence>(`/api/alerts/${alertId}/confidence`),
    enabled: !!alertId,
  });
}

export function useTimeline(alertId: string | null) {
  return useQuery({
    queryKey: ["timeline", alertId],
    queryFn: () => getJSON<Timeline>(`/api/alerts/${alertId}/timeline`),
    enabled: !!alertId,
  });
}
