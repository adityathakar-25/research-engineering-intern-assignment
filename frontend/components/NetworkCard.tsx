import React, { useEffect, useState, useMemo, useRef, useCallback } from "react";
import dynamic from "next/dynamic";
import { Share2, Network, HelpCircle } from "lucide-react";
import AISummary from "./AISummary";

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

const COMMUNITY_COLORS = [
  "#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
  "#06B6D4", "#EC4899", "#84CC16", "#F97316", "#6B7280"
];

interface NetworkNode {
  id: string;
  pagerank: number;
  community: number;
  degree: number;
  post_count: number;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
}

interface NetworkLink {
  source: string | NetworkNode;
  target: string | NetworkNode;
  weight: number;
}

interface NetworkResponse {
  nodes: NetworkNode[];
  edges: NetworkLink[];
  message?: string;
}

export default function NetworkCard({ query = "" }: { query?: string }) {
  const [loading, setLoading] = useState(true);
  const [originalData, setOriginalData] = useState<{ nodes: NetworkNode[]; links: NetworkLink[] } | null>(null);
  const [graphData, setGraphData] = useState<{ nodes: NetworkNode[]; links: NetworkLink[] } | null>(null);
  const [summary, setSummary] = useState<string>("");
  const [hoverNode, setHoverNode] = useState<NetworkNode | null>(null);
  const [highlightId, setHighlightId] = useState<string | null>(null);
  const graphRef = useRef<any>(null);

  useEffect(() => {
    let isMounted = true;
    const fetchGraph = async () => {
      setLoading(true);
      setSummary("");

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const url = new URL(`${API_BASE}/api/network`);
        if (query) url.searchParams.append("query", query);
        url.searchParams.append("limit", "150");

        const res = await fetch(url.toString());
        if (!res.ok) { console.log("Network fetch failed:", res.status); return; }
        const json: NetworkResponse = await res.json();

        if (isMounted && json.nodes) {
          const cleanNodes = json.nodes.map(n => ({ ...n }));
          const cleanLinks = json.edges.map(e => ({ ...e }));
          setOriginalData({ nodes: cleanNodes, links: cleanLinks });

          const activeNodes = json.nodes.map(n => ({ ...n }));
          const activeLinks = json.edges.map(e => ({ ...e }));
          setGraphData({ nodes: activeNodes, links: activeLinks });

          if (cleanNodes.length > 0) fetchSummary(json);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const fetchSummary = async (data: NetworkResponse) => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${API_BASE}/api/summary`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            chart_type: "network",
            data: [
              ...data.nodes.slice(0, 25).map(n => ({ author: n.id, pagerank: n.pagerank, community: n.community })),
              ...data.edges.slice(0, 25).map(e => ({ source: e.source, target: e.target, weight: e.weight })),
            ],
          }),
        });
        if (res.ok) {
          const sumJson = await res.json();
          if (isMounted && sumJson.summary) setSummary(sumJson.summary);
        }
      } catch (e) {
        console.log("Summary fetch skipped:", e);
      }
    };

    fetchGraph();
    return () => { isMounted = false; };
  }, [query]);

  // Auto zoom-to-fit after data loads
  useEffect(() => {
    if (graphData && graphData.nodes.length > 0 && graphRef.current) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400, 50);
      }, 800);
    }
  }, [graphData]);

  const handleRemoveTopNode = () => {
    if (!graphData || graphData.nodes.length === 0) return;
    let maxNode = graphData.nodes[0];
    for (const node of graphData.nodes) {
      if (node.pagerank > maxNode.pagerank) maxNode = node;
    }
    const newNodes = graphData.nodes.filter(n => n.id !== maxNode.id);
    const newLinks = graphData.links.filter(l => {
      const srcId = typeof l.source === "object" ? l.source.id : l.source;
      const tgtId = typeof l.target === "object" ? l.target.id : l.target;
      return srcId !== maxNode.id && tgtId !== maxNode.id;
    });
    setGraphData({ nodes: newNodes, links: newLinks });
  };

  const handleResetGraph = () => {
    if (originalData) {
      const cleanNodes = originalData.nodes.map(n => ({ ...n }));
      const cleanLinks = originalData.links.map(l => ({
        source: typeof l.source === "object" ? l.source.id : l.source,
        target: typeof l.target === "object" ? l.target.id : l.target,
        weight: l.weight,
      }));
      setGraphData({ nodes: cleanNodes, links: cleanLinks });
    }
  };

  const highlightNode = (nodeId: string) => {
    setHighlightId(nodeId === highlightId ? null : nodeId);
    // Center graph on the node
    if (graphRef.current) {
      const node = graphData?.nodes.find(n => n.id === nodeId);
      if (node && node.x !== undefined && node.y !== undefined) {
        graphRef.current.centerAt(node.x, node.y, 600);
        graphRef.current.zoom(3, 600);
      }
    }
  };

  // Custom node renderer — draws circle + label
  const nodeCanvasObject = useCallback((node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const label = node.id as string;
    const fontSize = Math.max(8, 11 / globalScale);
    const x = node.x as number;
    const y = node.y as number;
    const r = Math.sqrt((node.pagerank || 0.01) * 200 + 3);
    const isHighlighted = node.id === highlightId;

    // Draw highlight ring
    if (isHighlighted) {
      ctx.beginPath();
      ctx.arc(x, y, r + 3, 0, 2 * Math.PI);
      ctx.strokeStyle = "#facc15";
      ctx.lineWidth = 2.5;
      ctx.stroke();
    }

    // Draw circle
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fillStyle = COMMUNITY_COLORS[(node.community as number) % 10];
    ctx.fill();
    ctx.strokeStyle = "white";
    ctx.lineWidth = 0.5;
    ctx.stroke();

    // Draw label below node (only if zoomed in enough or highlighted)
    if (globalScale > 1.2 || isHighlighted) {
      ctx.font = `${isHighlighted ? "bold " : ""}${fontSize}px Poppins, sans-serif`;
      ctx.fillStyle = isHighlighted ? "#1e293b" : "#475569";
      ctx.textAlign = "center";
      ctx.textBaseline = "top";
      ctx.fillText(
        label.length > 12 ? label.slice(0, 12) + "\u2026" : label,
        x, y + r + 2
      );
    }
  }, [highlightId]);

  // Sorted nodes for leaderboard
  const sortedNodes = useMemo(() => {
    if (!graphData) return [];
    return [...graphData.nodes].sort((a, b) => b.pagerank - a.pagerank);
  }, [graphData]);

  // Community breakdown
  const communityBreakdown = useMemo(() => {
    if (!graphData) return [];
    const acc: Record<number, number> = {};
    graphData.nodes.forEach(n => {
      acc[n.community] = (acc[n.community] || 0) + 1;
    });
    return Object.entries(acc)
      .sort((a, b) => Number(b[1]) - Number(a[1]))
      .map(([c, count]) => ({ community: Number(c), count: count as number }));
  }, [graphData]);

  if (loading) {
    return (
      <div className="animate-pulse flex flex-col items-center justify-center h-[450px] gap-4">
        <div className="w-32 h-32 rounded-full bg-gray-100 border-4 border-gray-200" />
        <div className="flex flex-col items-center gap-2">
          <div className="h-4 w-36 bg-gray-100 rounded" />
          <p className="text-sm text-gray-400">Building network&hellip;</p>
        </div>
      </div>
    );
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
        <Share2 className="w-16 h-16 text-gray-200" />
        <p className="font-semibold text-gray-700">Not enough connections</p>
        <p className="text-sm text-gray-400 max-w-xs">
          Need at least 3 posts to build a network graph.
        </p>
        <p className="text-xs text-gray-400 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 mt-1">
          💡 Tip: Broader terms like &lsquo;anarchism&rsquo; work best
        </p>
      </div>
    );
  }

  const topPagerank = sortedNodes[0]?.pagerank || 1;

  return (
    <div className="overflow-visible relative">
      {/* Card header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100 -mx-6 -mt-6 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-600 flex items-center justify-center">
            <Network className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-base">Author Network</h3>
            <p className="text-xs text-gray-400">Who is engaging with whom</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-purple-50 text-purple-700 text-xs font-semibold px-3 py-1 rounded-full border border-purple-100">
            {graphData.nodes.length} nodes · {graphData.links.length} edges
          </span>
          <div className="relative group">
            <HelpCircle className="w-4 h-4 text-gray-300 hover:text-gray-500 cursor-help transition-colors" />
            <div className="absolute right-0 top-6 w-60 bg-gray-900 text-white text-xs rounded-lg p-2.5 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
              Authors connected by shared activity. Larger nodes = more influential. Colors = communities.
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center justify-between mb-3 gap-3">
        <span className="text-xs text-gray-400 italic">
          Drag nodes apart to separate labels · Scroll to zoom
        </span>
        <div className="flex gap-2">
          <button
            onClick={handleRemoveTopNode}
            className="text-xs px-3 py-1.5 bg-red-50 hover:bg-red-100 text-red-600 font-medium rounded-full transition-colors border border-red-200"
          >
            Remove Top Node
          </button>
          <button
            onClick={handleResetGraph}
            className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-600 font-medium rounded-full transition-colors"
          >
            Reset
          </button>
        </div>
      </div>

      {/* ── TWO-PANEL LAYOUT ── */}
      <div className="flex gap-4">
        {/* LEFT: Force Graph */}
        <div className="flex-[6] min-h-[450px] border border-gray-100 rounded-xl overflow-hidden bg-slate-50 relative cursor-grab active:cursor-grabbing">
          {/* Custom hover tooltip */}
          {hoverNode && (
            <div className="absolute top-3 left-3 bg-white/95 backdrop-blur shadow-lg border border-gray-100 rounded-xl p-3 text-sm z-10 w-52 pointer-events-none">
              <h4 className="font-bold text-gray-900 truncate pb-2 border-b mb-2">{hoverNode.id}</h4>
              <div className="space-y-1.5 text-xs text-gray-600">
                <div className="flex justify-between">
                  <span>Influence score</span>
                  <span className="font-semibold text-gray-900">{(hoverNode.pagerank || 0).toFixed(4)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Community</span>
                  <span className="font-semibold text-gray-900 flex items-center gap-1">
                    <span
                      className="w-2 h-2 rounded-full inline-block"
                      style={{ backgroundColor: COMMUNITY_COLORS[hoverNode.community % 10] }}
                    />
                    {hoverNode.community}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Posts</span>
                  <span className="font-semibold text-gray-900">{hoverNode.post_count}</span>
                </div>
              </div>
            </div>
          )}

          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={undefined}
            height={450}
            backgroundColor="transparent"
            nodeCanvasObject={nodeCanvasObject}
            nodeCanvasObjectMode={() => "replace"}
            nodeVal={node => {
              const n = node as NetworkNode;
              return (n.pagerank || 0.01) * 200 + 3;
            }}
            linkColor={() => "rgba(100, 116, 139, 0.6)"}
            linkWidth={link => Math.max(0.5, Math.sqrt((link as NetworkLink).weight || 1))}
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={1.5}
            onNodeHover={node => setHoverNode((node as NetworkNode) || null)}
            nodeLabel=""
            enableNodeDrag={true}
            enableZoomInteraction={true}
            cooldownTicks={200}
            warmupTicks={100}
            d3AlphaDecay={0.008}
            d3VelocityDecay={0.15}
            // @ts-expect-error linkDistance is valid for d3-force but missing from TS defs
            linkDistance={60}
            onEngineStop={() => {
              graphRef.current?.zoomToFit(600, 60);
            }}
          />
        </div>

        {/* RIGHT: Top Influencers Leaderboard */}
        <div className="flex-[4] overflow-y-auto max-h-[450px] border-l border-gray-100 pl-4">
          <div className="flex flex-col gap-2">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              Top Influencers by PageRank
            </h4>
            {sortedNodes.slice(0, 10).map((node, index) => (
              <div
                key={node.id}
                className={`flex items-center gap-3 p-3 rounded-xl transition-colors cursor-pointer ${
                  highlightId === node.id
                    ? "bg-purple-50 ring-1 ring-purple-200"
                    : "bg-gray-50 hover:bg-blue-50"
                }`}
                onClick={() => highlightNode(node.id)}
              >
                {/* Rank number */}
                <span className="text-lg font-bold text-gray-300 w-6 text-center">
                  {index + 1}
                </span>

                {/* Color dot = community */}
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: COMMUNITY_COLORS[node.community % 10] }}
                />

                {/* Author name */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {node.id}
                  </p>
                  <p className="text-xs text-gray-400">
                    Community {node.community} · {node.post_count} posts
                  </p>
                </div>

                {/* PageRank bar */}
                <div className="w-16 flex flex-col items-end gap-1">
                  <span className="text-xs font-semibold text-purple-600">
                    {(node.pagerank * 100).toFixed(1)}
                  </span>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 rounded-full h-1.5 transition-all"
                      style={{
                        width: `${(node.pagerank / topPagerank) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}

            <p className="text-xs text-gray-400 mt-2 text-center">
              PageRank score = relative influence in network
            </p>
          </div>
        </div>
      </div>

      {/* ── COMMUNITY BREAKDOWN ── */}
      {communityBreakdown.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide">
            Community Breakdown
          </p>
          <div className="flex gap-2 flex-wrap">
            {communityBreakdown.map(({ community, count }) => (
              <div
                key={community}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border"
                style={{
                  backgroundColor: COMMUNITY_COLORS[community % 10] + "20",
                  borderColor: COMMUNITY_COLORS[community % 10] + "40",
                  color: COMMUNITY_COLORS[community % 10],
                }}
              >
                <div
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: COMMUNITY_COLORS[community % 10] }}
                />
                Community {community}
                <span className="font-bold">{count} authors</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary && <AISummary text={summary} />}
    </div>
  );
}
