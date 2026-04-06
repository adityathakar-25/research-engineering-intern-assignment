"use client";

import React, { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { Search } from "lucide-react";

interface SearchResult {
  post_id: string;
  text: string;
  author: string;
  timestamp: string;
  platform: string;
  community: string;
  score: number;
}

interface SearchResponse {
  results: SearchResult[];
  count: number;
  suggested_queries: string[];
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

export default function SearchResults({ query = "" }: { query?: string }) {
  const [data, setData] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const isMultiLingual = /[^\x00-\x7F]/.test(query);

  useEffect(() => {
    let isMounted = true;
    const fetchSearch = async () => {
      setLoading(true);
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const res = await fetch(`${API_BASE}/api/search`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, limit: 20 }),
        });
        if (!res.ok) {
          if (isMounted) setData({ results: [], count: 0, suggested_queries: [] });
          return;
        }
        const json = await res.json();
        if (isMounted) setData(json);
      } catch (err: any) {
        console.log("Search fetch issue:", err?.message || "Failed");
        if (isMounted) setData({ results: [], count: 0, suggested_queries: [] });
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    if (query.trim()) {
      fetchSearch();
    } else {
      setLoading(false);
      setData(null);
    }

    return () => { isMounted = false; };
  }, [query]);

  if (!query) return null;

  if (loading) {
    return (
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden animate-pulse">
        {/* Skeleton header */}
        <div className="flex items-center gap-3 p-6 border-b border-gray-100">
          <div className="w-10 h-10 rounded-xl bg-orange-100" />
          <div className="space-y-1.5">
            <div className="h-4 w-32 bg-gray-200 rounded" />
            <div className="h-3 w-20 bg-gray-100 rounded" />
          </div>
        </div>
        <div className="p-6 space-y-4">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="border border-gray-100 rounded-lg p-4">
              <div className="h-4 w-3/4 bg-gray-200 rounded mb-2" />
              <div className="h-4 w-1/2 bg-gray-200 rounded mb-4" />
              <div className="h-3 w-32 bg-gray-100 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!data || data.results.length === 0) {
    return (
      <div className="bg-white border border-gray-100 rounded-2xl shadow-sm p-8 text-center text-gray-500">
        No results found. Try rephrasing your query.
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "MMM dd, yyyy");
    } catch {
      return dateStr;
    }
  };

  const scoreBorderColor = (score: number) => {
    if (score > 0.5) return "#4ADE80"; // green-400
    if (score > 0.3) return "#FACC15"; // yellow-400
    return "#D1D5DB"; // gray-300
  };

  return (
    <div className="bg-white border border-gray-100 rounded-2xl shadow-sm overflow-hidden">
      {/* ── Card header ── */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-500 flex items-center justify-center">
            <Search className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-base">Top Matches</h3>
            <p className="text-xs text-gray-400">Most semantically relevant posts</p>
          </div>
        </div>
        <span className="bg-orange-50 text-orange-700 text-xs font-semibold px-3 py-1 rounded-full border border-orange-100">
          {data.count} results
        </span>
      </div>

      <div className="p-6">
        {isMultiLingual && (
          <div className="bg-blue-50 text-blue-700 border border-blue-100 px-4 py-2.5 rounded-lg text-sm flex items-center gap-2 mb-6 font-medium">
            <span className="text-lg">🌐</span> Searching in multiple languages
          </div>
        )}

        <div className="space-y-3 mb-8 max-h-[800px] overflow-y-auto pr-1">
          {data.results.map((item, idx) => {
            const isReddit = item.platform.toLowerCase() === "reddit";
            const cleaned = cleanText(item.text);
            const snippet = cleaned.length > 200 ? cleaned.substring(0, 200) + "..." : cleaned;
            const scorePercent = Math.min(100, Math.max(0, item.score * 100));
            const leftBarColor = scoreBorderColor(item.score);

            return (
              <div
                key={`${item.post_id}-${idx}`}
                className="relative flex gap-0 border border-gray-100 rounded-xl overflow-hidden hover:border-blue-300 hover:shadow-md transition-all group bg-gray-50/40"
              >
                {/* Relevance left bar */}
                <div
                  className="w-1 flex-shrink-0 rounded-l-xl"
                  style={{ backgroundColor: leftBarColor }}
                />

                <div className="flex-1 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${
                        isReddit ? "bg-blue-100 text-blue-700" : "bg-sky-100 text-sky-700"
                      }`}>
                        {item.platform}
                      </span>
                      <span className="text-sm font-medium text-gray-900">{item.author || "Unknown"}</span>
                      <span className="text-sm text-gray-400">{formatDate(item.timestamp)}</span>
                    </div>
                    {item.community && (
                      <span className="bg-blue-50 text-blue-700 border border-blue-200 rounded-full text-xs px-2 py-0.5 font-medium">
                        r/{item.community}
                      </span>
                    )}
                  </div>

                  <p className="text-gray-700 text-[14px] leading-relaxed mb-3 group-hover:text-gray-900 transition-colors">
                    {snippet}
                  </p>

                  {/* Relevance Bar */}
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-medium text-gray-400 w-16">Relevance</span>
                    <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-1000 ease-out"
                        style={{ width: `${scorePercent}%`, backgroundColor: leftBarColor }}
                      />
                    </div>
                    <span className="text-xs font-semibold text-gray-600 w-8 text-right">
                      {item.score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Suggestions ── */}
        {data.suggested_queries && data.suggested_queries.length > 0 && (
          <div className="pt-5 border-t border-gray-100">
            <p className="text-sm font-medium text-gray-500 mb-3">You might also search:</p>
            <div className="flex flex-wrap gap-2">
              {data.suggested_queries.map((sug, i) => (
                <button
                  key={i}
                  className="text-sm px-4 py-2 bg-gray-50 border border-gray-200 rounded-full text-gray-700 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 transition-colors font-medium shadow-sm"
                  onClick={() => console.log("Suggested query clicked:", sug)}
                >
                  {sug}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
