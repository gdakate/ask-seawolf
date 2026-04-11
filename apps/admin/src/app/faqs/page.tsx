"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getFaqs, createFaq, updateFaq, deleteFaq, getFaqSuggestions } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { useState } from "react";

const CATEGORIES = [
  "general","admissions","registrar","bursar","financial_aid",
  "housing","dining","academics","it_services","student_affairs",
];

const EMPTY_FORM = { question: "", answer: "", category: "general", office_key: "", priority: 5, is_active: true };

export default function FaqsPage() {
  const qc = useQueryClient();
  const { data: faqs, isLoading } = useQuery({ queryKey: ["faqs"], queryFn: getFaqs });
  const { data: suggestions } = useQuery({ queryKey: ["faq-suggestions"], queryFn: getFaqSuggestions });

  const [showAdd, setShowAdd]     = useState(false);
  const [editId, setEditId]       = useState<string | null>(null);
  const [form, setForm]           = useState({ ...EMPTY_FORM });
  const [editForm, setEditForm]   = useState<any>(null);
  const [tab, setTab]             = useState<"faqs" | "suggestions">("faqs");
  const [promoteQ, setPromoteQ]   = useState<any>(null); // suggestion being promoted

  const invalidate = () => qc.invalidateQueries({ queryKey: ["faqs"] });

  const addMut = useMutation({
    mutationFn: () => createFaq(form),
    onSuccess: () => { invalidate(); setShowAdd(false); setForm({ ...EMPTY_FORM }); },
  });

  const editMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateFaq(id, data),
    onSuccess: () => { invalidate(); setEditId(null); },
  });

  const toggleMut = useMutation({
    mutationFn: ({ id, active }: { id: string; active: boolean }) => updateFaq(id, { is_active: active }),
    onSuccess: invalidate,
  });

  const delMut = useMutation({
    mutationFn: (id: string) => deleteFaq(id),
    onSuccess: invalidate,
  });

  const promoteMut = useMutation({
    mutationFn: (data: any) => createFaq(data),
    onSuccess: () => { invalidate(); qc.invalidateQueries({ queryKey: ["faq-suggestions"] }); setPromoteQ(null); },
  });

  const startEdit = (faq: any) => {
    setEditId(faq.id);
    setEditForm({ question: faq.question, answer: faq.answer, category: faq.category, office_key: faq.office_key || "", priority: faq.priority });
  };

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8 bg-gray-50 min-h-screen">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">FAQ Management</h1>
            <p className="text-sm text-gray-500 mt-1">Curated answers + AI-suggested candidates</p>
          </div>
          <button
            onClick={() => { setShowAdd(!showAdd); setTab("faqs"); }}
            className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark"
          >
            {showAdd ? "Cancel" : "+ Add FAQ"}
          </button>
        </div>

        {/* Add form */}
        {showAdd && (
          <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6 space-y-3">
            <h3 className="text-sm font-semibold text-gray-700">New FAQ Entry</h3>
            <input
              placeholder="Question"
              value={form.question}
              onChange={(e) => setForm({ ...form, question: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            />
            <textarea
              placeholder="Answer"
              value={form.answer}
              onChange={(e) => setForm({ ...form, answer: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-24 resize-none"
            />
            <div className="grid grid-cols-3 gap-3">
              <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <input placeholder="Office key" value={form.office_key} onChange={(e) => setForm({ ...form, office_key: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
              <input type="number" placeholder="Priority (0–10)" value={form.priority}
                onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) || 0 })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm" />
            </div>
            <button onClick={() => addMut.mutate()} disabled={!form.question || !form.answer}
              className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {addMut.isPending ? "Adding..." : "Add FAQ"}
            </button>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-5 bg-white border border-gray-200 rounded-lg p-1 w-fit">
          {([["faqs", "Curated FAQs"], ["suggestions", "AI Suggestions"]] as const).map(([key, label]) => (
            <button key={key} onClick={() => setTab(key)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                tab === key ? "bg-sbu-red text-white" : "text-gray-500 hover:text-gray-700"
              }`}>
              {label}
              {key === "suggestions" && suggestions && suggestions.length > 0 && (
                <span className="ml-1.5 px-1.5 py-0.5 bg-orange-100 text-orange-600 rounded-full text-[10px] font-semibold">
                  {suggestions.length}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── Curated FAQs tab ── */}
        {tab === "faqs" && (
          <div className="space-y-3">
            {isLoading ? (
              <div className="text-gray-400 text-sm">Loading...</div>
            ) : (faqs || []).length === 0 ? (
              <div className="text-gray-400 text-sm text-center py-12">No FAQs yet. Add one above.</div>
            ) : (faqs || []).map((f: any) => (
              <div key={f.id} className={`bg-white rounded-xl border p-4 transition-all ${f.is_active ? "border-gray-200" : "border-gray-100 opacity-60"}`}>
                {editId === f.id ? (
                  /* Edit mode */
                  <div className="space-y-3">
                    <input value={editForm.question} onChange={(e) => setEditForm({ ...editForm, question: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium" />
                    <textarea value={editForm.answer} onChange={(e) => setEditForm({ ...editForm, answer: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-20 resize-none" />
                    <div className="grid grid-cols-3 gap-2">
                      <select value={editForm.category} onChange={(e) => setEditForm({ ...editForm, category: e.target.value })}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">
                        {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                      <input value={editForm.office_key} onChange={(e) => setEditForm({ ...editForm, office_key: e.target.value })}
                        placeholder="Office key" className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                      <input type="number" value={editForm.priority} onChange={(e) => setEditForm({ ...editForm, priority: parseInt(e.target.value) || 0 })}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={() => editMut.mutate({ id: f.id, data: editForm })}
                        className="px-3 py-1.5 bg-sbu-red text-white rounded-lg text-xs font-medium">
                        {editMut.isPending ? "Saving..." : "Save"}
                      </button>
                      <button onClick={() => setEditId(null)} className="px-3 py-1.5 text-gray-500 text-xs hover:text-gray-700">Cancel</button>
                    </div>
                  </div>
                ) : (
                  /* View mode */
                  <div className="flex items-start gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-900 text-sm">{f.question}</span>
                        {f.hit_count > 0 && (
                          <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded text-[10px] font-semibold">
                            ✓ exact match
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">{f.answer}</p>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                        <span className="px-1.5 py-0.5 bg-gray-100 rounded capitalize">{f.category}</span>
                        {f.office_key && <span>{f.office_key}</span>}
                        <span>Priority: {f.priority}</span>
                        <span className="text-green-600 font-medium">↑ {f.hit_count} hits</span>
                        {f.last_used_at && (
                          <span>Last: {new Date(f.last_used_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {/* Active toggle */}
                      <button
                        onClick={() => toggleMut.mutate({ id: f.id, active: !f.is_active })}
                        className={`px-2 py-1 rounded-full text-[11px] font-semibold transition-colors ${
                          f.is_active ? "bg-green-100 text-green-700 hover:bg-green-200" : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                        }`}
                      >
                        {f.is_active ? "Active" : "Inactive"}
                      </button>
                      <button onClick={() => startEdit(f)} className="text-xs text-blue-500 hover:text-blue-700">Edit</button>
                      <button onClick={() => { if (confirm("Delete this FAQ?")) delMut.mutate(f.id); }}
                        className="text-xs text-red-400 hover:text-red-600">Delete</button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* ── AI Suggestions tab ── */}
        {tab === "suggestions" && (
          <div className="space-y-3">
            {!suggestions || suggestions.length === 0 ? (
              <div className="bg-white rounded-xl border border-gray-200 p-10 text-center text-gray-400 text-sm">
                No suggestions yet — more conversations needed to generate recommendations.
              </div>
            ) : suggestions.map((s: any, i: number) => (
              <div key={i} className="bg-white rounded-xl border border-gray-200 p-4">
                {promoteQ?.query === s.query ? (
                  /* Inline promote form */
                  <div className="space-y-3">
                    <p className="text-xs text-gray-500 font-medium">Converting suggestion to FAQ</p>
                    <input value={promoteQ.question} onChange={(e) => setPromoteQ({ ...promoteQ, question: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="Question" />
                    <textarea value={promoteQ.answer} onChange={(e) => setPromoteQ({ ...promoteQ, answer: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm h-20 resize-none" placeholder="Answer" />
                    <div className="grid grid-cols-2 gap-2">
                      <select value={promoteQ.category} onChange={(e) => setPromoteQ({ ...promoteQ, category: e.target.value })}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm">
                        {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                      <input type="number" value={promoteQ.priority}
                        onChange={(e) => setPromoteQ({ ...promoteQ, priority: parseInt(e.target.value) || 5 })}
                        className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" placeholder="Priority" />
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => promoteMut.mutate({ question: promoteQ.question, answer: promoteQ.answer, category: promoteQ.category, priority: promoteQ.priority })}
                        disabled={!promoteQ.answer}
                        className="px-3 py-1.5 bg-sbu-red text-white rounded-lg text-xs font-medium disabled:opacity-50">
                        {promoteMut.isPending ? "Creating..." : "Create FAQ"}
                      </button>
                      <button onClick={() => setPromoteQ(null)} className="px-3 py-1.5 text-gray-500 text-xs hover:text-gray-700">Cancel</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">{s.query}</p>
                      {s.variants && s.variants.length > 1 && (
                        <div className="mt-1 space-y-0.5">
                          {s.variants.slice(1).map((v: string, vi: number) => (
                            <p key={vi} className="text-xs text-gray-400 italic pl-2 border-l border-gray-200">
                              "{v}"
                            </p>
                          ))}
                        </div>
                      )}
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-gray-400">
                        <span className="capitalize px-1.5 py-0.5 bg-gray-100 rounded">{s.category}</span>
                        <span className="font-medium text-gray-600">{s.count}× asked</span>
                        <span className={`font-medium ${s.avg_confidence < 0.3 ? "text-red-500" : s.avg_confidence < 0.7 ? "text-yellow-600" : "text-green-600"}`}>
                          {s.avg_confidence < 0.3 ? "Low conf" : s.avg_confidence < 0.7 ? "Med conf" : "Good conf"} ({(s.avg_confidence * 100).toFixed(0)}%)
                        </span>
                      </div>
                    </div>
                    <button
                      onClick={() => setPromoteQ({ query: s.query, question: s.query, answer: "", category: s.category, priority: 5 })}
                      className="px-3 py-1.5 bg-blue-50 text-blue-600 hover:bg-blue-100 rounded-lg text-xs font-medium shrink-0 transition-colors"
                    >
                      + Add as FAQ
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
