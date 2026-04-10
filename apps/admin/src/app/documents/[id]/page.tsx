"use client";

import { useQuery } from "@tanstack/react-query";
import { getDocument, getChunks } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { use } from "react";

export default function DocumentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: doc, isLoading } = useQuery({ queryKey: ["document", id], queryFn: () => getDocument(id) });
  const { data: chunks } = useQuery({ queryKey: ["chunks", id], queryFn: () => getChunks(`document_id=${id}`), enabled: !!id });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        {isLoading ? (
          <div className="text-gray-400">Loading...</div>
        ) : doc ? (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900">{doc.title}</h1>
              <a href={doc.source_url} target="_blank" rel="noopener noreferrer" className="text-sm text-sbu-red hover:underline">{doc.source_url}</a>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              {[
                { label: "Status", value: doc.status },
                { label: "Type", value: doc.content_type },
                { label: "Version", value: `v${doc.version}` },
                { label: "Chunks", value: doc.chunk_count },
              ].map((s) => (
                <div key={s.label} className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="text-xs text-gray-500">{s.label}</div>
                  <div className="text-lg font-semibold text-gray-900 mt-1">{s.value}</div>
                </div>
              ))}
            </div>

            {doc.cleaned_content && (
              <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
                <h3 className="font-semibold text-gray-900 mb-3">Cleaned Content</h3>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto bg-gray-50 p-4 rounded-lg">{doc.cleaned_content}</pre>
              </div>
            )}

            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3">Chunks ({chunks?.length || 0})</h3>
              <div className="space-y-3">
                {(chunks || []).map((c: any) => (
                  <div key={c.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-600">#{c.chunk_index}</span>
                      {c.heading && <span className="text-xs px-2 py-0.5 bg-white border border-gray-200 rounded">{c.heading}</span>}
                      <span className="text-xs text-gray-400">{c.token_count} tokens</span>
                    </div>
                    <p className="text-sm text-gray-700 line-clamp-3">{c.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="text-gray-400">Document not found</div>
        )}
      </main>
    </div>
  );
}
