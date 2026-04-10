"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFaqs, createFaq, deleteFaq } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { useState } from "react";

export default function FaqsPage() {
  const qc = useQueryClient();
  const { data: faqs, isLoading } = useQuery({ queryKey: ["faqs"], queryFn: getFaqs });
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ question: "", answer: "", category: "general", office_key: "", priority: 0 });

  const addMut = useMutation({
    mutationFn: () => createFaq(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["faqs"] }); setShowAdd(false); setForm({ question: "", answer: "", category: "general", office_key: "", priority: 0 }); },
  });
  const delMut = useMutation({ mutationFn: (id: string) => deleteFaq(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["faqs"] }) });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">FAQ Overrides</h1>
            <p className="text-sm text-gray-500 mt-1">Curated answers for common questions</p>
          </div>
          <button onClick={() => setShowAdd(!showAdd)} className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark">
            {showAdd ? "Cancel" : "Add FAQ"}
          </button>
        </div>

        {showAdd && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 space-y-3">
            <input placeholder="Question" value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            <textarea placeholder="Answer" value={form.answer} onChange={(e) => setForm({ ...form, answer: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-24" />
            <div className="grid grid-cols-3 gap-3">
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {["general","admissions","registrar","bursar","financial_aid","housing","dining","academics"].map(c => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
              <input placeholder="Office key" value={form.office_key} onChange={(e) => setForm({ ...form, office_key: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              <input type="number" placeholder="Priority" value={form.priority} onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) || 0 })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <button onClick={() => addMut.mutate()} disabled={!form.question || !form.answer}
              className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {addMut.isPending ? "Adding..." : "Add FAQ"}
            </button>
          </div>
        )}

        <div className="space-y-3">
          {isLoading ? <div className="text-gray-400">Loading...</div> : (faqs || []).map((f: any) => (
            <div key={f.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-medium text-gray-900 text-sm">{f.question}</h3>
                  <p className="text-sm text-gray-600 mt-1 leading-relaxed">{f.answer}</p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{f.category}</span>
                    {f.office_key && <span className="text-xs text-gray-400">{f.office_key}</span>}
                    <span className="text-xs text-gray-400">Priority: {f.priority}</span>
                  </div>
                </div>
                <button onClick={() => { if (confirm("Delete?")) delMut.mutate(f.id); }} className="text-xs text-red-500 hover:text-red-700 ml-4">Delete</button>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
