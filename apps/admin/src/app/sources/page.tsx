"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getSources, createSource, deleteSource, updateSource } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { useState } from "react";

export default function SourcesPage() {
  const qc = useQueryClient();
  const { data: sources, isLoading } = useQuery({ queryKey: ["sources"], queryFn: getSources });
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", category: "general", office: "", authority_score: 1 });

  const addMut = useMutation({
    mutationFn: () => createSource(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["sources"] }); setShowAdd(false); setForm({ name: "", url: "", category: "general", office: "", authority_score: 1 }); },
  });

  const delMut = useMutation({
    mutationFn: (id: string) => deleteSource(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  const toggleMut = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => updateSource(id, { is_active: active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sources</h1>
            <p className="text-sm text-gray-500 mt-1">Manage content source URLs</p>
          </div>
          <button onClick={() => setShowAdd(!showAdd)} className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark">
            {showAdd ? "Cancel" : "Add Source"}
          </button>
        </div>

        {showAdd && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              <input placeholder="URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {["general","admissions","registrar","bursar","financial_aid","housing","dining","academics","student_affairs","it_services"].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <input placeholder="Office key" value={form.office} onChange={(e) => setForm({ ...form, office: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <button onClick={() => addMut.mutate()} disabled={!form.name || !form.url}
              className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {addMut.isPending ? "Adding..." : "Add Source"}
            </button>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Name</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Category</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Office</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Authority</th>
                <th className="text-right px-4 py-3 text-gray-600 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              ) : (sources || []).map((s: any) => (
                <tr key={s.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{s.name}</div>
                    <div className="text-xs text-gray-400 truncate max-w-xs">{s.url}</div>
                  </td>
                  <td className="px-4 py-3"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{s.category}</span></td>
                  <td className="px-4 py-3 text-gray-600">{s.office || "—"}</td>
                  <td className="px-4 py-3">
                    <button onClick={() => toggleMut.mutate({ id: s.id, active: !s.is_active })}
                      className={`px-2 py-0.5 rounded-full text-xs font-medium ${s.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {s.is_active ? "Active" : "Inactive"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{s.authority_score}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => { if (confirm("Delete this source?")) delMut.mutate(s.id); }}
                      className="text-xs text-red-500 hover:text-red-700">Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
