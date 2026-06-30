"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";
import type { GraphData } from "@/lib/api";

// react-force-graph-2d touches window/canvas → must be client-only (no SSR).
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const KIND_COLOR: Record<string, string> = {
  account: "#4c9aff",
  device: "#ff5630",
  counterparty: "#ffab00",
};
const HIGHLIGHT = "#36b37e"; // cited evidence nodes glow green

export function GraphCanvas({ data, height = 520 }: { data: GraphData; height?: number }) {
  // react-force-graph wants {nodes, links}; map source/target → links.
  const graph = useMemo(
    () => ({
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.edges.map((e) => ({ ...e, source: e.source, target: e.target })),
    }),
    [data],
  );

  return (
    <div className="rounded-xl border border-border bg-[#0b1120] overflow-hidden" style={{ height }}>
      <ForceGraph2D
        graphData={graph}
        backgroundColor="#0b1120"
        linkColor={() => "#2a3957"}
        linkDirectionalArrowLength={3}
        linkDirectionalArrowRelPos={1}
        linkLabel={(l: any) => l.label || ""}
        nodeLabel={(n: any) => `${n.kind}: ${n.id}`}
        nodeRelSize={5}
        nodeCanvasObject={(node: any, ctx, scale) => {
          const hi = node.highlight;
          const r = hi ? 7 : 5;
          const color = hi ? HIGHLIGHT : KIND_COLOR[node.kind] ?? "#4c9aff";
          if (hi) {
            ctx.shadowColor = HIGHLIGHT;
            ctx.shadowBlur = 14;
          }
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.fill();
          ctx.shadowBlur = 0;
          if (scale > 1.4 || hi) {
            ctx.font = `${hi ? 600 : 400} ${10 / scale * 1.2}px Inter, sans-serif`;
            ctx.fillStyle = "#cbd5e1";
            ctx.textAlign = "center";
            ctx.fillText(node.label, node.x, node.y + r + 8 / scale);
          }
        }}
      />
    </div>
  );
}
