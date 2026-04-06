"use client";

import React, { useEffect, useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format, parseISO } from "date-fns";
import { TrendingUp, HelpCircle } from "lucide-react";
import AISummary from "./AISummary";

interface TimeSeriesCardProps {
  query: string;
  platform: string;
  start: string;
  end: string;
  onSuggest?: (term: string) => void;
}

interface DataPoint {
  date: string;
  count: number;
  platform: string;
}

interface TimeseriesResponse {
  query: string;
  total_count: number;
  date_range_used: { start: string; end: string };
  data: DataPoint[];
}

export default function TimeSeriesCard({ query, platform, start, end, onSuggest }: TimeSeriesCardProps) {
  const [data, setData] = useState<TimeseriesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<string>("");

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setLoading(true);
      setSummary("");
      
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const url = new URL(`${API_BASE}/api/timeseries`);
        url.searchParams.append("query", query);
        if (platform !== "all") url.searchParams.append("platform", platform);
        if (start) url.searchParams.append("start", start);
        if (end) url.searchParams.append("end", end);

        const res = await fetch(url.toString());
        if (!res.ok) { console.log("Timeseries fetch failed:", res.status); return; }
        const json = await res.json();
        
        if (isMounted) {
          setData(json);
          // Fetch AI summary if we have data
          if (json.data && json.data.length > 0) {
            fetchSummary(json.data);
          }
        }
      } catch (error) {
        console.error(error);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const fetchSummary = async (chartData: DataPoint[]) => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const res = await fetch(`${API_BASE}/api/summary`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query,
            chart_type: "timeseries",
            data: chartData.slice(0, 50),
          }),
        });
        if (res.ok) {
          const summaryJson = await res.json();
          if (isMounted && summaryJson.summary) {
            setSummary(summaryJson.summary);
          }
        }
      } catch (e) {
        console.log("Summary fetch skipped:", e);
      }
    };

    fetchData();
    return () => { isMounted = false; };
  }, [query, platform, start, end]);

  if (loading) {
    return (
      <div className="animate-pulse space-y-3 pt-2">
        <div className="flex items-end gap-2 h-[280px] px-2">
          <div className="flex-1 bg-blue-50 rounded-t-md" style={{ height: "65%" }} />
          <div className="flex-1 bg-blue-100 rounded-t-md" style={{ height: "40%" }} />
          <div className="flex-1 bg-blue-50 rounded-t-md" style={{ height: "80%" }} />
          <div className="flex-1 bg-blue-100 rounded-t-md" style={{ height: "55%" }} />
          <div className="flex-1 bg-blue-50 rounded-t-md" style={{ height: "70%" }} />
          <div className="flex-1 bg-blue-100 rounded-t-md" style={{ height: "45%" }} />
          <div className="flex-1 bg-blue-50 rounded-t-md" style={{ height: "90%" }} />
          <div className="flex-1 bg-blue-100 rounded-t-md" style={{ height: "60%" }} />
          <div className="flex-1 bg-blue-50 rounded-t-md" style={{ height: "50%" }} />
        </div>
        <div className="h-px bg-gray-100" />
        <div className="flex justify-between">
          {[1,2,3,4].map(i => <div key={i} className="h-3 w-10 bg-gray-100 rounded" />)}
        </div>
      </div>
    );
  }

  if (!data || data.data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
        <TrendingUp className="w-16 h-16 text-gray-200" />
        <p className="font-semibold text-gray-700">No activity found</p>
        <p className="text-sm text-gray-400 max-w-xs">
          Try searching &lsquo;anarchism&rsquo; for Feb 2025 data
        </p>
        {onSuggest && (
          <button
            onClick={() => onSuggest("anarchism")}
            className="mt-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-full transition-colors"
          >
            Try anarchism &rarr;
          </button>
        )}
      </div>
    );
  }

  // Process data for recharts - Group by date
  const chartDataMap = new Map<string, { date: string; reddit: number; twitter: number }>();
  
  data.data.forEach(item => {
    if (!chartDataMap.has(item.date)) {
      chartDataMap.set(item.date, { date: item.date, reddit: 0, twitter: 0 });
    }
    const current = chartDataMap.get(item.date)!;
    if (item.platform.toLowerCase() === "reddit") {
      current.reddit += item.count;
    } else if (item.platform.toLowerCase() === "twitter") {
      current.twitter += item.count;
    }
  });

  const chartData = Array.from(chartDataMap.values()).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

  const hasReddit = chartData.some(d => d.reddit > 0);
  const hasTwitter = chartData.some(d => d.twitter > 0);

  const formatXAxisDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "MMM dd");
    } catch {
      return dateStr;
    }
  };

  return (
    <div>
      {/* Card header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100 -mx-6 -mt-6 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center">
            <TrendingUp className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-base">Post Volume Over Time</h3>
            <p className="text-xs text-gray-400">Daily post activity matching your search</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-3 py-1 rounded-full border border-blue-100">
            {data.total_count.toLocaleString()} posts
          </span>
          <div className="relative group">
            <HelpCircle className="w-4 h-4 text-gray-300 hover:text-gray-500 cursor-help transition-colors" />
            <div className="absolute right-0 top-6 w-56 bg-gray-900 text-white text-xs rounded-lg p-2.5 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-30">
              Shows daily post count for your query over time. Spikes indicate viral moments.
            </div>
          </div>
        </div>
      </div>

      <div className="h-[280px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
            <defs>
              <linearGradient id="redditGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.20} />
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="twitterGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#38BDF8" stopOpacity={0.15} />
                <stop offset="95%" stopColor="#38BDF8" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
            <XAxis
              dataKey="date"
              tickFormatter={formatXAxisDate}
              tickMargin={12}
              tick={{ fill: '#94A3B8', fontSize: 12, fontWeight: 400 }}
              minTickGap={30}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              allowDecimals={false}
              axisLine={false}
              tickLine={false}
              tickMargin={10}
              tick={{ fill: '#94A3B8', fontSize: 12, fontWeight: 400 }}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  return (
                    <div className="bg-white border border-gray-100 rounded-xl shadow-lg p-3 text-sm flex flex-col gap-2 min-w-[140px]">
                      <p className="font-semibold text-gray-900 text-xs">{formatXAxisDate(String(label))}</p>
                      <div className="flex flex-col gap-1">
                        {payload.map((entry) => (
                          <div key={String(entry.dataKey)} className="flex items-center justify-between gap-4">
                            <div className="flex items-center gap-2">
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }}></span>
                              <span className="capitalize text-gray-500 text-xs">{String(entry.dataKey)}</span>
                            </div>
                            <span className="font-semibold text-gray-900">{String(entry.value)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {hasReddit && (
              <Area
                type="monotone"
                dataKey="reddit"
                stroke="#3B82F6"
                strokeWidth={2.5}
                fill="url(#redditGrad)"
                dot={false}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            )}
            {hasTwitter && (
              <Area
                type="monotone"
                dataKey="twitter"
                stroke="#38BDF8"
                strokeWidth={2.5}
                fill="url(#twitterGrad)"
                dot={false}
                activeDot={{ r: 5, strokeWidth: 0 }}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {summary && <AISummary text={summary} />}
    </div>
  );
}
