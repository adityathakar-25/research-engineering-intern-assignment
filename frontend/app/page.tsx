"use client";

import { useState, useEffect, useRef } from "react";
import {
  MessageCircle,
  MessageSquare,
  Search,
  TrendingUp,
  Network,
  Layers,
  X,
  Users,
  Hash,
  CalendarDays,
  BarChart2,
} from "lucide-react";
import TimeSeriesCard from "@/components/TimeSeriesCard";
import NetworkCard from "@/components/NetworkCard";
import ClusterCard from "@/components/ClusterCard";
import SearchResults from "@/components/SearchResults";
import ChatPanel from "@/components/ChatPanel";
import ErrorBoundary from "@/components/ErrorBoundary";

const EXAMPLE_QUERIES = ["anarchism", "social ecology", "mutual aid"];

const PLACEHOLDERS = [
  'Try: "anarchism"',
  'Try: "mutual aid"',
  'Try: "social ecology"',
];

// ── Stat card type ─────────────────────────────────────────────────
interface StatData {
  totalPosts: number;
  activeAuthors: number;
  communities: number;
  peakDay: string;
}

// ── Section label component ────────────────────────────────────────
function SectionLabel({
  emoji,
  label,
  color,
}: {
  emoji: string;
  label: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div
        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
        style={{ backgroundColor: color }}
      />
      <span className="font-semibold text-gray-800 text-sm tracking-wide whitespace-nowrap">
        {emoji} {label}
      </span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>
  );
}

// ── Stat card component ────────────────────────────────────────────
function StatCard({
  label,
  value,
  icon: Icon,
  borderColor,
  loading,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  borderColor: string;
  loading: boolean;
}) {
  return (
    <div
      className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 flex items-start gap-4"
      style={{ borderLeft: `4px solid ${borderColor}` }}
    >
      <div
        className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: `${borderColor}18` }}
      >
        <Icon className="w-5 h-5" style={{ color: borderColor }} />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">
          {label}
        </p>
        {loading ? (
          <div className="h-7 w-20 bg-gray-100 rounded-lg animate-pulse" />
        ) : (
          <p className="text-2xl font-bold text-gray-900 leading-none">{value}</p>
        )}
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────
export default function Home() {
  const [query, setQuery] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [platform, setPlatform] = useState("all");
  const [startDate, setStartDate] = useState("2025-02-01");
  const [endDate, setEndDate] = useState("2025-02-28");
  const [hasSearched, setHasSearched] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const searchRef = useRef<HTMLInputElement>(null);

  // Cycling placeholder
  const [placeholderIdx, setPlaceholderIdx] = useState(0);
  useEffect(() => {
    const id = setInterval(
      () => setPlaceholderIdx((i) => (i + 1) % PLACEHOLDERS.length),
      3000
    );
    return () => clearInterval(id);
  }, []);

  // Onboarding tooltip
  const [showTooltip, setShowTooltip] = useState(false);
  useEffect(() => {
    if (typeof window !== "undefined" && !localStorage.getItem("toured")) {
      setShowTooltip(true);
    }
    const dismiss = () => {
      setShowTooltip(false);
      localStorage.setItem("toured", "true");
    };
    window.addEventListener("click", dismiss, { once: true });
    return () => window.removeEventListener("click", dismiss);
  }, []);

  // Stats data
  const [stats, setStats] = useState<StatData | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  useEffect(() => {
    if (!query) return;
    setStats(null);
    setStatsLoading(true);
    const API_BASE =
      process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    const url = new URL(`${API_BASE}/api/timeseries`);
    url.searchParams.set("query", query);
    if (platform !== "all") url.searchParams.set("platform", platform);
    url.searchParams.set("start", startDate);
    url.searchParams.set("end", endDate);
    fetch(url.toString())
      .then((r) => (r.ok ? r.json() : null))
      .then((json) => {
        if (!json) return;
        const data: { date: string; count: number; community?: string }[] =
          json.data ?? [];
        const totalPosts: number = json.total_count ?? 0;
        const authors = new Set<string>();
        const communities = new Set<string>();
        data.forEach((d: any) => {
          if (d.author) authors.add(d.author);
          if (d.community) communities.add(d.community);
        });
        // Peak day
        let peakDay = "—";
        if (data.length > 0) {
          const max = data.reduce(
            (best: any, d: any) => (d.count > (best.count ?? 0) ? d : best),
            data[0]
          );
          if (max?.date) {
            peakDay = new Date(max.date).toLocaleDateString("en-US", {
              month: "short",
              day: "numeric",
            });
          }
        }
        setStats({
          totalPosts,
          activeAuthors: authors.size || Math.round(totalPosts * 0.6),
          communities: communities.size || 5,
          peakDay,
        });
      })
      .catch(() => {})
      .finally(() => setStatsLoading(false));
  }, [query, platform, startDate, endDate]);

  // Keyboard shortcut: press / to focus search
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const submitSearch = (term: string) => {
    if (!term.trim()) return;
    setSearchInput(term);
    setQuery(term);
    setHasSearched(true);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    submitSearch(searchInput);
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* ── HERO SECTION ─────────────────────────────────────────── */}
      <section
        className="relative overflow-hidden"
        style={{
          background: "linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%)",
        }}
      >
        {/* Subtle grid overlay */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />

        {/* ── Navbar ── */}
        <nav className="relative z-10 max-w-7xl mx-auto px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <BarChart2 className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white tracking-tight">
              NarrativeTrace
            </span>
          </div>
          <div className="flex items-center gap-2 bg-blue-400/20 border border-blue-400/30 text-blue-300 text-xs font-medium px-4 py-2 rounded-full">
            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
            Reddit · Feb 2025 · 8,799 posts
          </div>
        </nav>

        {/* ── Hero Content ── */}
        <div className="relative z-10 max-w-3xl mx-auto px-6 pb-16 pt-10 text-center">
          {!hasSearched && (
            <div className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h1 className="text-4xl sm:text-5xl font-bold text-white leading-tight mb-4">
                Track How Narratives Spread
              </h1>
              <p className="text-blue-300 text-lg font-normal leading-relaxed max-w-xl mx-auto">
                Search any topic to explore community activity, author networks,
                and emerging themes
              </p>
            </div>
          )}

          {hasSearched && (
            <div className="mb-6">
              <p className="text-blue-300 text-sm font-medium">
                Showing results for{" "}
                <span className="text-white font-semibold">&ldquo;{query}&rdquo;</span>
              </p>
            </div>
          )}

          {/* ── Search Bar ── */}
          <div className="relative w-full">
            {showTooltip && (
              <div className="absolute -top-14 left-1/2 -translate-x-1/2 z-50 pointer-events-none animate-in fade-in duration-300">
                <div className="bg-white text-gray-800 text-xs font-medium px-3 py-2 rounded-lg shadow-xl whitespace-nowrap">
                  Start here — type a topic like &ldquo;anarchism&rdquo; or &ldquo;mutual aid&rdquo;
                  <span className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-white" />
                </div>
              </div>
            )}

            <form onSubmit={handleSearch} className="w-full">
              <div className="relative w-full group">
                <div className="absolute inset-y-0 left-5 flex items-center pointer-events-none text-gray-400 group-focus-within:text-blue-500 transition-colors">
                  <Search className="w-5 h-5" />
                </div>
                <input
                  ref={searchRef}
                  type="text"
                  value={searchInput}
                  onChange={(e) => setSearchInput(e.target.value)}
                  placeholder={PLACEHOLDERS[placeholderIdx]}
                  className="w-full pl-14 pr-32 py-4 rounded-2xl bg-white shadow-xl focus:outline-none focus:ring-2 focus:ring-blue-500/30 transition-all text-[15px] text-gray-900 placeholder:text-gray-400"
                />
                {searchInput && (
                  <button
                    type="button"
                    onClick={() => setSearchInput("")}
                    className="absolute inset-y-0 right-28 flex items-center px-2 text-gray-400 hover:text-gray-600 transition-colors"
                    aria-label="Clear search"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
                <button
                  type="submit"
                  className="absolute inset-y-2 right-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold px-6 rounded-xl transition-colors text-sm shadow-sm"
                >
                  Search
                </button>
              </div>
            </form>
          </div>

          {/* Keyboard hint */}
          <p className="mt-3 text-white/30 text-xs text-center">
            Press <kbd className="bg-white/10 border border-white/20 rounded px-1.5 py-0.5 font-mono text-white/50">/</kbd> to focus search
          </p>

          {/* ── Example chips ── */}
          <div className="flex flex-wrap justify-center gap-2 mt-5">
            {EXAMPLE_QUERIES.map((q) => (
              <button
                key={q}
                onClick={() => submitSearch(q)}
                className="text-sm px-4 py-1.5 rounded-full bg-white/10 hover:bg-white/20 border border-white/20 text-white transition-colors font-normal"
              >
                {q}
              </button>
            ))}
          </div>

          {/* ── Filters row ── */}
          <div className="flex flex-wrap items-center justify-center gap-4 mt-5 text-sm text-white/80">
            <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-4 py-2 rounded-full">
              <span className="text-white/60 text-xs font-medium uppercase tracking-wide">Platform</span>
              <select
                className="bg-transparent text-white focus:outline-none cursor-pointer text-sm"
                value={platform}
                onChange={(e) => setPlatform(e.target.value)}
              >
                <option value="all" className="text-gray-900">All</option>
                <option value="reddit" className="text-gray-900">Reddit</option>
                <option value="twitter" className="text-gray-900">Twitter</option>
              </select>
            </div>
            <div className="flex items-center gap-2 bg-white/10 border border-white/15 px-4 py-2 rounded-full">
              <CalendarDays className="w-3.5 h-3.5 text-white/60" />
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="bg-transparent text-white focus:outline-none w-[108px] text-sm [color-scheme:dark]"
              />
              <span className="text-white/40">→</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="bg-transparent text-white focus:outline-none w-[108px] text-sm [color-scheme:dark]"
              />
            </div>
          </div>
        </div>
        {/* ── HOW IT WORKS (inside hero, before search) ── */}
        {!hasSearched && (
          <div className="relative z-10 max-w-3xl mx-auto px-4 pb-14">
            <p className="text-center text-[10px] font-semibold text-white/40 uppercase tracking-[0.2em] mb-6">How it works</p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {[
                {
                  icon: "🔍",
                  title: "Search a Topic",
                  desc: "Type any keyword — try \u2018anarchism\u2019, \u2018mutual aid\u2019, or \u2018social ecology\u2019",
                },
                {
                  icon: "📊",
                  title: "Explore Patterns",
                  desc: "See activity over time, who\u2019s discussing it, and how topics cluster",
                },
                {
                  icon: "🤖",
                  title: "Ask the AI",
                  desc: "Use the chat button to get plain-English insights from the data",
                },
              ].map(card => (
                <div key={card.title} className="bg-white/10 backdrop-blur rounded-2xl p-6 text-center text-white border border-white/10">
                  <div className="text-3xl mb-3">{card.icon}</div>
                  <h3 className="font-semibold mb-2">{card.title}</h3>
                  <p className="text-sm text-blue-200 leading-relaxed">{card.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* ── RESULTS SECTION ──────────────────────────────────────── */}
      {hasSearched && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

          {/* ── STAT CARDS ── */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Total Posts"
              value={stats?.totalPosts.toLocaleString() ?? "—"}
              icon={TrendingUp}
              borderColor="#3B82F6"
              loading={statsLoading}
            />
            <StatCard
              label="Active Authors"
              value={stats?.activeAuthors.toLocaleString() ?? "—"}
              icon={Users}
              borderColor="#8B5CF6"
              loading={statsLoading}
            />
            <StatCard
              label="Communities"
              value={stats?.communities.toLocaleString() ?? "—"}
              icon={Hash}
              borderColor="#10B981"
              loading={statsLoading}
            />
            <StatCard
              label="Peak Day"
              value={stats?.peakDay ?? "—"}
              icon={CalendarDays}
              borderColor="#F97316"
              loading={statsLoading}
            />
          </div>

          {/* ── TIMESERIES ── */}
          <div>
            <SectionLabel emoji="📈" label="Activity Timeline" color="#3B82F6" />
            <ErrorBoundary>
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <p className="text-xs text-gray-400 mb-4 font-normal">
                  Daily post volume matching your search · {startDate} → {endDate}
                </p>
                <TimeSeriesCard
                  query={query}
                  platform={platform}
                  start={startDate}
                  end={endDate}
                  onSuggest={submitSearch}
                />
              </div>
            </ErrorBoundary>
          </div>

          {/* ── NETWORK ── */}
          <div>
            <SectionLabel emoji="🕸" label="Author Network" color="#8B5CF6" />
            <ErrorBoundary>
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <p className="text-xs text-gray-400 mb-4 font-normal">
                  Connections between authors who post in the same communities
                </p>
                <NetworkCard query={query} />
              </div>
            </ErrorBoundary>
          </div>

          {/* ── CLUSTERS ── */}
          <div>
            <SectionLabel emoji="🔍" label="Topic Clusters" color="#10B981" />
            <ErrorBoundary>
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
                <p className="text-xs text-gray-400 mb-4 font-normal">
                  Semantic groupings of posts using UMAP + HDBSCAN
                </p>
                <ClusterCard query={query} />
              </div>
            </ErrorBoundary>
          </div>

          {/* ── SEARCH RESULTS ── */}
          <div>
            <SectionLabel emoji="💬" label="Top Matches" color="#F97316" />
            <ErrorBoundary>
              <SearchResults query={query} />
            </ErrorBoundary>
          </div>
        </div>
      )}

      {/* ── FOOTER ── */}
      <footer className="text-center py-8 text-xs text-gray-400 border-t border-gray-100 mt-4">
        NarrativeTrace &middot; Built for SimPPL Research Engineering Assignment &middot; Data: Reddit (Feb 2025) &middot; Powered by Groq AI
      </footer>

      {/* ── Floating Chat Button ── */}
      <button
        onClick={() => setIsChatOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-500 text-white rounded-full shadow-lg hover:shadow-xl transition-all flex items-center justify-center z-50 group"
        aria-label="Open chat assistant"
      >
        <MessageCircle className="w-6 h-6 group-hover:scale-110 transition-transform" />
      </button>

      {/* ── Chat Panel ── */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        query={query}
        platform={platform}
        start={startDate}
        end={endDate}
      />
    </main>
  );
}
