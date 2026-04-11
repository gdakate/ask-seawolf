"use client";

import { useQuery } from "@tanstack/react-query";
import { getAnalytics } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

const CATEGORY_COLORS: Record<string, string> = {
  admissions:    "bg-blue-500",
  bursar:        "bg-green-500",
  financial_aid: "bg-yellow-500",
  housing:       "bg-purple-500",
  registrar:     "bg-orange-500",
  dining:        "bg-pink-500",
  academics:     "bg-teal-500",
  it_services:   "bg-cyan-500",
  general:       "bg-gray-400",
};

function StatCard({ label, value, sub, color }: { label: string; value: string | number; sub?: string; color?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="text-xs text-gray-500 font-medium uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color ?? "text-gray-900"}`}>{value ?? "—"}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  );
}

function ConfBadge({ conf }: { conf: number | null }) {
  if (conf === null || conf === undefined) return <span className="text-gray-300 text-xs">—</span>;
  const color = conf >= 0.7 ? "text-green-600" : conf >= 0.3 ? "text-yellow-600" : "text-red-500";
  const label = conf >= 0.7 ? "High" : conf >= 0.3 ? "Med" : "Low";
  return <span className={`text-xs font-medium ${color}`}>{label} ({(conf * 100).toFixed(0)}%)</span>;
}

export default function AnalyticsPage() {
  const { data, isLoading } = useQuery({ queryKey: ["analytics"], queryFn: getAnalytics, refetchInterval: 30000 });

  const maxCat = data?.top_categories?.[0]?.count || 1;

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8 bg-gray-50 min-h-screen">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
          <p className="text-sm text-gray-500 mt-1">Live stats from conversation history</p>
        </div>

        {isLoading ? (
          <div className="text-gray-400 text-sm">Loading...</div>
        ) : (
          <>
            {/* ── Stat cards ── */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
              <StatCard label="Sources"   value={data.total_sources}   />
              <StatCard label="Documents" value={data.total_documents} />
              <StatCard label="Chunks"    value={data.total_chunks}    />
              <StatCard label="Sessions"  value={data.total_sessions}  />
              <StatCard label="Messages"  value={data.total_messages}  />
              <StatCard label="FAQ Hits"  value={data.faq_hit_count}   sub="confidence = 1.0" color="text-green-600" />
              <StatCard label="Low Confidence" value={data.low_confidence_count} sub="conf < 0.3" color="text-red-500" />
              <StatCard label="Avg Confidence"
                value={data.avg_confidence ? `${(data.avg_confidence * 100).toFixed(1)}%` : "—"}
                color={data.avg_confidence >= 0.7 ? "text-green-600" : data.avg_confidence >= 0.3 ? "text-yellow-600" : "text-red-500"}
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              {/* ── Top categories ── */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Top Question Categories</h2>
                {(data.top_categories || []).length === 0 ? (
                  <div className="text-gray-400 text-sm">No data yet</div>
                ) : (
                  <div className="space-y-3">
                    {data.top_categories.map((cat: any) => (
                      <div key={cat.category}>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span className="capitalize">{cat.category.replace("_", " ")}</span>
                          <span className="font-medium">{cat.count}</span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${CATEGORY_COLORS[cat.category] ?? "bg-gray-400"}`}
                            style={{ width: `${Math.round((cat.count / maxCat) * 100)}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* ── Confidence breakdown ── */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h2 className="text-sm font-semibold text-gray-700 mb-4">Answer Quality Breakdown</h2>
                {data.total_messages === 0 ? (
                  <div className="text-gray-400 text-sm">No messages yet</div>
                ) : (() => {
                  const total = (data.faq_hit_count || 0) + (data.low_confidence_count || 0);
                  const mid   = Math.max(0, (data.total_messages / 2) - (data.faq_hit_count || 0) - (data.low_confidence_count || 0));
                  const items = [
                    { label: "FAQ exact match", value: data.faq_hit_count, color: "bg-green-500" },
                    { label: "Good (conf ≥ 0.7)", value: Math.round(mid), color: "bg-blue-400" },
                    { label: "Low confidence",   value: data.low_confidence_count, color: "bg-red-400" },
                  ];
                  const total2 = items.reduce((s, i) => s + i.value, 0) || 1;
                  return (
                    <div className="space-y-3">
                      {items.map((item) => (
                        <div key={item.label}>
                          <div className="flex justify-between text-xs text-gray-600 mb-1">
                            <span>{item.label}</span>
                            <span className="font-medium">{item.value}</span>
                          </div>
                          <div className="w-full bg-gray-100 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${item.color}`}
                              style={{ width: `${Math.round((item.value / total2) * 100)}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* ── Recent queries ── */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-4 border-b border-gray-100">
                <h2 className="text-sm font-semibold text-gray-700">Recent Queries</h2>
              </div>
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="text-left px-5 py-2.5 text-xs text-gray-500 font-medium">Query</th>
                    <th className="text-left px-4 py-2.5 text-xs text-gray-500 font-medium w-24">Confidence</th>
                    <th className="text-left px-4 py-2.5 text-xs text-gray-500 font-medium w-36">Time</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {(data.recent_queries || []).length === 0 ? (
                    <tr><td colSpan={3} className="px-5 py-6 text-center text-gray-400 text-sm">No queries yet</td></tr>
                  ) : (data.recent_queries || []).map((q: any, i: number) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="px-5 py-3 text-gray-800 max-w-md truncate">{q.query}</td>
                      <td className="px-4 py-3"><ConfBadge conf={q.confidence} /></td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {new Date(q.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
