"use client";

import { useQuery } from "@tanstack/react-query";
import { getChunks } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

export default function ChunksPage() {
  const { data: chunks, isLoading } = useQuery({ queryKey: ["chunks"], queryFn: () => getChunks() });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Chunks</h1>
        <p className="text-sm text-gray-500 mb-6">Vector-indexed content chunks</p>

        <div className="space-y-3">
          {isLoading ? (
            <div className="text-gray-400">Loading...</div>
          ) : (chunks || []).map((c: any) => (
            <div key={c.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center gap-3 mb-2">
                {c.heading && <span className="px-2 py-0.5 bg-gray-100 rounded text-xs font-medium text-gray-700">{c.heading}</span>}
                <span className="text-xs text-gray-400">#{c.chunk_index}</span>
                <span className="text-xs text-gray-400">{c.token_count} tokens</span>
                <span className="text-xs text-gray-400 font-mono">{c.id.slice(0, 8)}</span>
              </div>
              <p className="text-sm text-gray-700 leading-relaxed line-clamp-3">{c.content}</p>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
