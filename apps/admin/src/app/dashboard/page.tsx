"use client";

import { useQuery } from "@tanstack/react-query";
import { getDashboard, triggerCrawl, triggerReindex } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { useState } from "react";

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="text-sm text-gray-500 mb-1">{label}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-100 text-green-700",
    running: "bg-blue-100 text-blue-700",
    pending: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${colors[status] || "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

export default function DashboardPage() {
  const { data, isLoading, refetch } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
  const [acting, setActing] = useState(false);

  const handleCrawl = async () => { setActing(true); try { await triggerCrawl(); refetch(); } finally { setActing(false); } };
  const handleReindex = async () => { setActing(true); try { await triggerReindex(); refetch(); } finally { setActing(false); } };

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-sm text-gray-500 mt-1">Platform overview and quick actions</p>
          </div>
          <div className="flex gap-2">
            <button onClick={handleCrawl} disabled={acting}
              className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark disabled:opacity-50">
              Run Crawl
            </button>
            <button onClick={handleReindex} disabled={acting}
              className="px-4 py-2 bg-gray-800 text-white rounded-lg text-sm font-medium hover:bg-gray-700 disabled:opacity-50">
              Reindex
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-gray-400">Loading...</div>
        ) : data ? (
          <>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard label="Sources" value={data.active_sources} sub={`${data.total_sources} total`} />
              <StatCard label="Documents" value={data.indexed_documents} sub={`${data.total_documents} total`} />
              <StatCard label="Chunks" value={data.total_chunks} />
              <StatCard label="Chat Sessions" value={data.total_sessions} sub={`${data.total_messages} messages`} />
              <StatCard label="Feedback" value={data.total_feedback} />
              <StatCard label="Avg Confidence" value={data.avg_confidence ? `${(data.avg_confidence * 100).toFixed(0)}%` : "N/A"} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">Recent Crawl Jobs</h3>
                {data.recent_crawl_jobs.length === 0 ? (
                  <p className="text-sm text-gray-400">No crawl jobs yet</p>
                ) : (
                  <div className="space-y-2">
                    {data.recent_crawl_jobs.map((j: any) => (
                      <div key={j.id} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 font-mono text-xs">{j.id.slice(0, 8)}</span>
                        <StatusBadge status={j.status} />
                        <span className="text-gray-400 text-xs">{new Date(j.created_at).toLocaleDateString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">Recent Index Jobs</h3>
                {data.recent_index_jobs.length === 0 ? (
                  <p className="text-sm text-gray-400">No index jobs yet</p>
                ) : (
                  <div className="space-y-2">
                    {data.recent_index_jobs.map((j: any) => (
                      <div key={j.id} className="flex items-center justify-between text-sm">
                        <span className="text-gray-600 font-mono text-xs">{j.id.slice(0, 8)}</span>
                        <StatusBadge status={j.status} />
                        <span className="text-gray-400 text-xs">{j.chunks_created} chunks</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        ) : null}
      </main>
    </div>
  );
}
