"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getJSON,
  type GraphData,
  type VerticalAlert,
  type VerticalInvestigation,
  type VerticalsResponse,
} from "@/lib/api";

// The registry + platform counters (sidebar + platform page).
export function useVerticals() {
  return useQuery({
    queryKey: ["verticals"],
    queryFn: () => getJSON<VerticalsResponse>("/api/verticals"),
  });
}

export function useVerticalAlerts(key: string) {
  return useQuery({
    queryKey: ["vertical-alerts", key],
    queryFn: () => getJSON<VerticalAlert[]>(`/api/verticals/${key}/alerts`),
    enabled: !!key,
  });
}

export function useVerticalInvestigation(key: string, rootId: string | null) {
  return useQuery({
    queryKey: ["vertical-investigation", key, rootId],
    queryFn: () =>
      getJSON<VerticalInvestigation>(
        `/api/verticals/${key}/investigate?root_id=${rootId}`,
      ),
    enabled: !!key && !!rootId,
  });
}

export function useVerticalGraph(key: string, rootId: string | null) {
  return useQuery({
    queryKey: ["vertical-graph", key, rootId],
    queryFn: () => getJSON<GraphData>(`/api/verticals/${key}/graph?root_id=${rootId}`),
    enabled: !!key && !!rootId,
  });
}

// Objects of a type (procurement: Requisition / Budget).
export function useVerticalObjects(key: string, type: string) {
  return useQuery({
    queryKey: ["vertical-objects", key, type],
    queryFn: () => getJSON<VerticalAlert[]>(`/api/verticals/${key}/objects?type=${type}`),
    enabled: !!key && !!type,
  });
}
