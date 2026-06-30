"use client";

import { useState } from "react";
import { useObject } from "@/lib/useObject";

// The ontology is a queryable graph, not a chatbot — pick any cited/touched
// object to see its real properties and links. Mirrors the Streamlit drill-down.
export function ObjectInspector({ ids }: { ids: string[] }) {
  const [selected, setSelected] = useState<string>("");
  const obj = useObject(selected || null);
  const options = Array.from(new Set(ids)).sort();

  return (
    <div>
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        className="w-full sm:w-80 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-fg font-mono"
      >
        <option value="">— select an object —</option>
        {options.map((id) => (
          <option key={id} value={id}>
            {id}
          </option>
        ))}
      </select>

      {obj.isLoading && <div className="text-muted text-sm mt-3">Loading…</div>}
      {obj.error && <div className="text-file text-sm mt-3">Inspect error: {String(obj.error)}</div>}
      {obj.data && (
        <div className="mt-4 rounded-xl border border-border bg-surface p-4">
          <div className="mb-3 text-sm">
            <span className="font-semibold text-fg">{obj.data.type}</span>{" "}
            <span className="font-mono text-muted">{obj.data.id}</span>
          </div>
          <table className="w-full text-sm mb-3">
            <tbody>
              {Object.entries(obj.data.properties).map(([k, v]) => (
                <tr key={k} className="border-t border-hairline">
                  <td className="py-1.5 pr-4 text-muted font-mono text-xs align-top w-40">{k}</td>
                  <td className="py-1.5 text-fg break-all">{String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {Object.values(obj.data.linked_ids).some((a) => a.length > 0) && (
            <div>
              <div className="text-xs font-semibold text-fg mb-1.5">Linked objects</div>
              <div className="space-y-1.5">
                {Object.entries(obj.data.linked_ids)
                  .filter(([, arr]) => arr.length > 0)
                  .map(([lt, arr]) => (
                    <div key={lt} className="text-xs">
                      <span className="text-muted italic">{lt}</span>{" "}
                      <span className="text-muted">→</span>{" "}
                      {arr.map((id) => (
                        <span
                          key={id}
                          className="inline-block rounded border border-border px-1.5 py-0.5 font-mono text-[0.7rem] text-muted mr-1 mb-1"
                        >
                          {id}
                        </span>
                      ))}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
