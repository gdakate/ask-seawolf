"use client";

import { useQuery } from "@tanstack/react-query";
import { getEvaluations, getEvaluationCases } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import Link from "next/link";
import { use } from "react";

export default function EvaluationDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: evals } = useQuery({ queryKey: ["evaluations"], queryFn: getEvaluations });
  const { data: cases, isLoading } = useQuery({
    queryKey: ["evaluation-cases", id],
    queryFn: () => getEvaluationCases(id),
    enabled: !!id,
  });

  const run = evals?.find((e: any) => e.id === id);
  const passRate = run && run.total_cases > 0 ? run.passed_cases / run.total_cases : null;

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8 bg-gray-50 min-h-screen">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Link href="/evaluations" className="text-sm text-gray-400 hover:text-gray-600">← Evaluations</Link>
          <span className="text-gray-300">/</span>
          <h1 className="text-2xl font-bold text-gray-900">{run?.name || "Evaluation Run"}</h1>
        </div>

        {/* Summary cards */}
        {run && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Pass Rate</div>
              <div className={`text-2xl font-bold ${passRate !== null && passRate >= 0.8 ? "text-green-600" : passRate !== null && passRate >= 0.5 ? "text-yellow-600" : "text-red-500"}`}>
                {passRate !== null ? `${(passRate * 100).toFixed(0)}%` : "—"}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">{run.passed_cases}/{run.total_cases} cases</div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Avg Retrieval</div>
              <div className="text-2xl font-bold text-gray-900">
                {run.avg_retrieval_score ? `${(run.avg_retrieval_score * 100).toFixed(0)}%` : "—"}
              </div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Avg Answer</div>
              <div className="text-2xl font-bold text-gray-900">
                {run.avg_answer_score ? `${(run.avg_answer_score * 100).toFixed(0)}%` : "—"}
              </div>
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">Status</div>
              <div className={`text-sm font-semibold mt-1 ${run.status === "completed" ? "text-green-600" : "text-blue-600"}`}>
                {run.status}
              </div>
              <div className="text-xs text-gray-400 mt-0.5">{new Date(run.created_at).toLocaleString()}</div>
            </div>
          </div>
        )}

        {/* Cases table */}
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-700">Test Cases</h2>
            {cases && (
              <span className="text-xs text-gray-400">{cases.length} total</span>
            )}
          </div>
          {isLoading ? (
            <div className="p-8 text-center text-gray-400 text-sm">Loading...</div>
          ) : (cases || []).length === 0 ? (
            <div className="p-8 text-center text-gray-400 text-sm">No cases found</div>
          ) : (
            <div className="divide-y divide-gray-50">
              {(cases || []).map((c: any) => (
                <div key={c.id} className={`p-4 ${c.passed ? "" : "bg-red-50/30"}`}>
                  <div className="flex items-start gap-3">
                    <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs flex-shrink-0 ${c.passed ? "bg-green-100 text-green-700" : "bg-red-100 text-red-600"}`}>
                      {c.passed ? "✓" : "✗"}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 mb-1">{c.question}</p>
                      {c.actual_answer && (
                        <p className="text-xs text-gray-600 leading-relaxed mb-2 line-clamp-2">{c.actual_answer}</p>
                      )}
                      {c.expected_answer && (
                        <p className="text-xs text-gray-400 italic mb-2">Expected: {c.expected_answer}</p>
                      )}
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        {c.retrieval_score != null && (
                          <span>Retrieval: <span className="font-medium text-gray-600">{(c.retrieval_score * 100).toFixed(0)}%</span></span>
                        )}
                        {c.answer_score != null && (
                          <span>Answer: <span className="font-medium text-gray-600">{(c.answer_score * 100).toFixed(0)}%</span></span>
                        )}
                        {c.notes && <span className="text-gray-400">{c.notes}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
