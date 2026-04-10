"use client";

import { useQuery } from "@tanstack/react-query";
import { getDocuments } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import Link from "next/link";

export default function DocumentsPage() {
  const { data: docs, isLoading } = useQuery({ queryKey: ["documents"], queryFn: () => getDocuments() });

  const statusColors: Record<string, string> = {
    indexed: "bg-green-100 text-green-700",
    ingested: "bg-blue-100 text-blue-700",
    pending: "bg-yellow-100 text-yellow-700",
    failed: "bg-red-100 text-red-700",
    archived: "bg-gray-100 text-gray-500",
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Documents</h1>
        <p className="text-sm text-gray-500 mb-6">Ingested content from all sources</p>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Title</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Type</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Version</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Updated</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              ) : (docs || []).map((d: any) => (
                <tr key={d.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link href={`/documents/${d.id}`} className="font-medium text-gray-900 hover:text-sbu-red">{d.title}</Link>
                    <div className="text-xs text-gray-400 truncate max-w-sm">{d.source_url}</div>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{d.content_type}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColors[d.status] || "bg-gray-100 text-gray-600"}`}>{d.status}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">v{d.version}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{new Date(d.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
