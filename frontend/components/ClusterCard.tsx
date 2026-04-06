"use client";

import React, { useEffect, useState } from "react";
import { Layers, HelpCircle } from "lucide-react";
import AISummary from "./AISummary";

const CLUSTER_COLORS = [
  "#3B82F6", "#8B5CF6", "#10B981", "#F59E0B",
  "#EF4444", "#06B6D4", "#EC4899", "#84CC16",
  "#F97316", "#6366F1", "#14B8A6", "#F43F5E",
];

interface ClusterPost {
  post_id: string;
  text: string;
  author: string;
  x: number;
  y: number;
}

interface ClusterData {
  id: number;
  label: string;
  size: number;
  posts: ClusterPost[];
}

interface ClusterResponse {
  clusters: ClusterData[];
  total_posts: number;
  noise_count: number;
  actual_clusters: number;
  warning: string | null;
}

function cleanText(text: string): string {
  return text
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/\^/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

export default function ClusterCard({ query = "" }: { query?: string }) {
  const [nClusters, setNClusters] = useState<number>(8);
  const [debouncedNClusters, setDebouncedNClusters] = useState<number>(8);

  const [data, setData] = useState<ClusterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<string>("");
  const [nomicUrl, setNomicUrl] = useState<string | null>("checking");
  const [selectedCluster, setSelectedCluster] = useState<number | null>(null);

  // Debounce slider
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedNClusters(nClusters);
    }, 500);
    return () => clearTimeout(handler);
  }, [nClusters]);

  // Fetch Nomic URL on mount
  useEffect(() => {
    const fetchNomic = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_BASE}/api/nomic-url`);
        if (res.ok) {
          const json = await res.json();
          setNomicUrl(json.url || null);
        } else {
          setNomicUrl(null);
        }
      } catch {
        setNomicUrl(null);
      }
    };
    fetchNomic();
  }, []);

  // Fetch clusters logic
  useEffect(() => {
    let isMounted = true;
    const fetchClusters = async () => {
      setLoading(true);
      setSummary("");
      setSelectedCluster(null);

      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = new URL(`${API_BASE}/api/clusters`);
        if (query) url.searchParams.append("query", query);
        url.searchParams.append("n_clusters", debouncedNClusters.toString());

        const res = await fetch(url.toString());
        if (!res.ok) { console.log("Clusters fetch failed:", res.status); return; }
        const json: ClusterResponse = await res.json();

        if (isMounted) {
          setData(json);
          if (json.total_posts > 0) fetchSummary(json);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const fetchSummary = async (scatterData: ClusterResponse) => {
      try {
        const summaryContext = scatterData.clusters
          .filter(c => c.id !== -1)
          .map(c => ({
            label: c.label,
            size: c.size,
            example_text: c.posts.slice(0, 3).map(p => p.text),
          }));

        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_BASE}/api/summary`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            chart_type: "clusters",
            data: summaryContext,
          }),
        });
        if (res.ok) {
          const json = await res.json();
          if (isMounted && json.summary) setSummary(json.summary);
        }
      } catch (e) {
        console.log("Summary fetch skipped:", e);
      }
    };

    fetchClusters();
    return () => { isMounted = false; };
  }, [query, debouncedNClusters]);

  const handleNomicClick = () => {
    if (nomicUrl && nomicUrl !== "checking") {
      window.open(nomicUrl, "_blank");
    }
  };

  if (loading && !data) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="h-28 bg-gray-100 rounded-xl" />
          ))}
        </div>
        <div className="h-[280px] bg-gray-50 rounded-xl" />
      </div>
    );
  }

  if (!data || data.clusters.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
        <Layers className="w-16 h-16 text-gray-200" />
        <p className="font-semibold text-gray-700">No topic clusters found</p>
        <p className="text-sm text-gray-400 max-w-xs">
          Try adjusting the slider to fewer clusters, or use a broader search term.
        </p>
      </div>
    );
  }

  const realClusters = data.clusters.filter(c => c.id !== -1).sort((a, b) => b.size - a.size);
  const noiseBucket = data.clusters.find(c => c.id === -1);
  const maxSize = realClusters[0]?.size || 1;

  return (
    <div className="space-y-6">
      {/* ── Card header ── */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100 -mx-6 -mt-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-emerald-600 flex items-center justify-center">
            <Layers className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-base">Topic Clusters</h3>
            <p className="text-xs text-gray-400">Semantic groupings using UMAP + HDBSCAN</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-emerald-50 text-emerald-700 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-100">
            {data.actual_clusters} clusters · {data.total_posts} posts
          </span>
          <div className="relative group">
            <HelpCircle className="w-4 h-4 text-gray-300 hover:text-gray-500 cursor-help transition-colors" />
            <div className="absolute right-0 top-6 w-60 bg-gray-900 text-white text-xs rounded-lg p-2.5 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
              Posts grouped by semantic similarity. Each cluster represents a distinct discussion theme.
            </div>
          </div>
        </div>
      </div>

      {/* ── Slider Controls ── */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col items-end gap-1 ml-auto">
          <span className="text-xs text-gray-500 font-medium">
            Adjust number of topic clusters (currently: {nClusters})
          </span>
          <div className="flex items-center gap-3 bg-gray-50 border px-4 py-2 rounded-full shadow-sm">
            {loading && (
              <span className="text-xs text-blue-500 font-medium animate-pulse">Reclustering…</span>
            )}
            <input
              type="range"
              min="2"
              max="20"
              step="1"
              value={nClusters}
              onChange={(e) => setNClusters(parseInt(e.target.value))}
              className="w-32 sm:w-48 accent-blue-600"
            />
            <span className="text-sm font-semibold text-gray-700 w-6 text-center">{nClusters}</span>
          </div>
        </div>
      </div>

      {data.warning && (
        <div className="bg-amber-50 text-amber-800 border border-amber-200 px-4 py-3 rounded-lg text-sm flex items-center gap-2">
          <span>⚠️</span> {data.warning}
        </div>
      )}

      {/* ── BUBBLE CHART ── */}
      <div className="relative w-full min-h-[320px] flex flex-wrap gap-5 items-center justify-center p-6 bg-gray-50 rounded-2xl">
        {loading && (
          <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-2xl">
            <span className="text-gray-500 font-medium bg-white px-4 py-2 rounded-full shadow-sm border">Recalculating...</span>
          </div>
        )}

        {realClusters.map((cluster, index) => {
          const diameter = Math.max(80, Math.min(180, (cluster.size / maxSize) * 180));
          const keywords = cluster.label.split("·").slice(0, 2);
          const color = CLUSTER_COLORS[index % CLUSTER_COLORS.length];
          const isSelected = selectedCluster === cluster.id;

          return (
            <div
              key={cluster.id}
              className={`relative flex flex-col items-center justify-center rounded-full cursor-pointer transition-all select-none ${
                isSelected ? "scale-110 shadow-xl ring-2" : "hover:scale-105 hover:shadow-lg"
              }`}
              style={{
                width: diameter,
                height: diameter,
                backgroundColor: color + "25",
                border: `2px solid ${color}60`,
                ...(isSelected ? { ringColor: color } : {}),
              }}
              onClick={() => setSelectedCluster(isSelected ? null : cluster.id)}
            >
              {/* Keywords inside bubble */}
              <div className="text-center px-2">
                {keywords.map((kw, i) => (
                  <p
                    key={i}
                    className="font-semibold leading-tight"
                    style={{
                      color,
                      fontSize: diameter > 120 ? "13px" : "10px",
                    }}
                  >
                    {kw.trim()}
                  </p>
                ))}
              </div>

              {/* Post count badge */}
              <div
                className="absolute -bottom-2 left-1/2 -translate-x-1/2 px-2 py-0.5 rounded-full text-white text-xs font-bold shadow-sm whitespace-nowrap"
                style={{ backgroundColor: color }}
              >
                {cluster.size} posts
              </div>
            </div>
          );
        })}

        {/* Noise bubble (gray, dashed) */}
        {noiseBucket && noiseBucket.size > 0 && (
          <div
            className="flex flex-col items-center justify-center rounded-full"
            style={{
              width: 70,
              height: 70,
              backgroundColor: "#94a3b820",
              border: "2px dashed #94a3b840",
            }}
          >
            <p className="text-xs text-gray-400 text-center px-1">Unclustered</p>
            <p className="text-xs font-bold text-gray-400">{noiseBucket.size}</p>
          </div>
        )}
      </div>

      {/* ── SELECTED CLUSTER DETAIL ── */}
      {selectedCluster !== null &&
        (() => {
          const cluster = data.clusters.find(c => c.id === selectedCluster);
          if (!cluster) return null;
          const colorIdx = realClusters.findIndex(c => c.id === selectedCluster);
          const color = CLUSTER_COLORS[(colorIdx >= 0 ? colorIdx : 0) % CLUSTER_COLORS.length];

          return (
            <div
              className="mt-4 p-5 rounded-2xl border-2 animate-in fade-in slide-in-from-top-2 duration-200"
              style={{ borderColor: color + "40", backgroundColor: color + "08" }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-4 h-4 rounded-full" style={{ backgroundColor: color }} />
                <h4 className="font-semibold text-gray-900">{cluster.label}</h4>
                <span className="ml-auto text-sm font-medium" style={{ color }}>
                  {cluster.size} posts
                </span>
              </div>
              <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto">
                {cluster.posts.slice(0, 5).map(post => (
                  <div key={post.post_id} className="bg-white rounded-xl p-3 border border-gray-100">
                    <p className="text-sm text-gray-700 leading-relaxed line-clamp-2">
                      {cleanText(post.text)}
                    </p>
                    <p className="text-xs text-gray-400 mt-1">@{post.author || "Unknown"}</p>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-3 text-center">
                Click a bubble to explore · Click again to close
              </p>
            </div>
          );
        })()}

      {/* ── AI Summary ── */}
      {summary && <AISummary text={summary} />}

      {/* ── Nomic Button ── */}
      <div className="pt-6 border-t mt-6 flex justify-center">
        {nomicUrl === "checking" ? (
          <button disabled className="text-sm px-6 py-2.5 bg-gray-100 text-gray-400 font-medium rounded-full cursor-not-allowed">
            Checking visualizer...
          </button>
        ) : nomicUrl === null ? (
          <button disabled className="text-sm px-6 py-2.5 bg-gray-100 text-gray-500 font-medium rounded-full cursor-not-allowed border border-dashed border-gray-300">
            Embedding viz not configured
          </button>
        ) : (
          <button
            onClick={handleNomicClick}
            className="text-sm px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-full transition-colors shadow-sm flex items-center gap-2"
          >
            <span>📈</span> View Embedding Visualization
          </button>
        )}
      </div>
    </div>
  );
}
