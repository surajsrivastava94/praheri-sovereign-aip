"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getJSON,
  postJSON,
  type ActionResult,
  type AuditRow,
  type PendingItem,
} from "@/lib/api";
import { useRole } from "@/lib/role";

export function useApprovals() {
  return useQuery({
    queryKey: ["approvals"],
    queryFn: () => getJSON<PendingItem[]>("/api/approvals"),
  });
}

export function useAudit() {
  return useQuery({
    queryKey: ["audit"],
    queryFn: () => getJSON<AuditRow[]>("/api/audit"),
  });
}

// Propose/run a governed action as the current role. Refreshes the queue + audit.
export function useAction() {
  const { role } = useRole();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, params }: { name: string; params: Record<string, unknown> }) =>
      postJSON<ActionResult>(`/api/actions/${name}`, { role, params }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });
}

// MLRO approves a pending action; it executes + is audited.
export function useApprove() {
  const { role } = useRole();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ref: string) =>
      postJSON<ActionResult>(`/api/approvals/${ref}/approve`, { role }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["approvals"] });
      qc.invalidateQueries({ queryKey: ["audit"] });
    },
  });
}
