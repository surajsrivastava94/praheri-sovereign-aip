"use client";

import { useQuery } from "@tanstack/react-query";
import { getJSON, type OntologyObject } from "@/lib/api";

// Drill-down fetch for a single ontology object. Only fires once an id is
// selected (enabled gate), so the inspector is idle until used.
export function useObject(objectId: string | null) {
  return useQuery({
    queryKey: ["object", objectId],
    queryFn: () => getJSON<OntologyObject>(`/api/objects/${objectId}`),
    enabled: !!objectId,
  });
}
