"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getEvaluations, runEvaluation } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

export default function EvaluationsPage() {
  const qc = useQueryClient();
  const { data: evals, isLoading } = useQuery({ queryKey: ["evaluations"], queryFn: getEvaluations });
  const runMut = useMutation({ mutationFn: () => runEvaluation("Manual Run"), onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations"] }) });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
            <p className="text-sm text-gray-500 mt-1">Answer quality and retrieval diagnostics</p>
          </div>
          <button onClick={() => runMut.mutate()} className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark">
            {runMut.isPending ? "Running..." : "Run Evaluation"}
          </button>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Name</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Cases</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Passed</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Avg Retrieval</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Avg Answer</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              ) : (evals || []).length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No evaluations yet. Run one to get started.</td></tr>
              ) : (evals || []).map((e: any) => (
                <tr key={e.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-900">{e.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${e.status === "completed" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>{e.status}</span>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{e.total_cases}</td>
                  <td className="px-4 py-3 text-gray-600">{e.passed_cases}</td>
                  <td className="px-4 py-3 text-gray-600">{e.avg_retrieval_score ? `${(e.avg_retrieval_score * 100).toFixed(0)}%` : "—"}</td>
                  <td className="px-4 py-3 text-gray-600">{e.avg_answer_score ? `${(e.avg_answer_score * 100).toFixed(0)}%` : "—"}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{new Date(e.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
