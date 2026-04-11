"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getEvaluations, runEvaluation } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import Link from "next/link";

export default function EvaluationsPage() {
  const qc = useQueryClient();
  const { data: evals, isLoading } = useQuery({ queryKey: ["evaluations"], queryFn: getEvaluations });
  const runMut = useMutation({
    mutationFn: () => runEvaluation("Manual Run"),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["evaluations"] }),
  });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8 bg-gray-50 min-h-screen">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Evaluations</h1>
            <p className="text-sm text-gray-500 mt-1">Answer quality and retrieval diagnostics</p>
          </div>
          <button
            onClick={() => runMut.mutate()}
            disabled={runMut.isPending}
            className="px-4 py-2 bg-sbu-red text-white rounded-lg text-sm font-medium hover:bg-sbu-red-dark disabled:opacity-50"
          >
            {runMut.isPending ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Running...
              </span>
            ) : "Run Evaluation"}
          </button>
        </div>

        {runMut.isPending && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-700">
            Running eval cases against the alignment dataset — this may take 30–60s...
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Name</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Status</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Pass Rate</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Avg Retrieval</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Avg Answer</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Date</th>
                <th className="text-right px-4 py-3 text-gray-600 font-medium" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              ) : (evals || []).length === 0 ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No evaluations yet. Run one to get started.</td></tr>
              ) : (evals || []).map((e: any) => {
                const passRate = e.total_cases > 0 ? (e.passed_cases / e.total_cases) : null;
                return (
                  <tr key={e.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{e.name}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${e.status === "completed" ? "bg-green-100 text-green-700" : e.status === "running" ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600"}`}>
                        {e.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {passRate !== null ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                            <div className={`h-full rounded-full ${passRate >= 0.8 ? "bg-green-500" : passRate >= 0.5 ? "bg-yellow-500" : "bg-red-500"}`}
                              style={{ width: `${passRate * 100}%` }} />
                          </div>
                          <span className={`text-xs font-medium ${passRate >= 0.8 ? "text-green-600" : passRate >= 0.5 ? "text-yellow-600" : "text-red-500"}`}>
                            {e.passed_cases}/{e.total_cases}
                          </span>
                        </div>
                      ) : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {e.avg_retrieval_score ? `${(e.avg_retrieval_score * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
                      {e.avg_answer_score ? `${(e.avg_answer_score * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{new Date(e.created_at).toLocaleDateString()}</td>
                    <td className="px-4 py-3 text-right">
                      <Link href={`/evaluations/${e.id}`} className="text-xs text-blue-500 hover:text-blue-700">
                        View cases →
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
