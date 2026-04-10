"use client";

import { useQuery } from "@tanstack/react-query";
import { getFeedback } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";

export default function FeedbackPage() {
  const { data: feedback, isLoading } = useQuery({ queryKey: ["feedback"], queryFn: getFeedback });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">User Feedback</h1>
        <p className="text-sm text-gray-500 mb-6">Reviews and ratings from chat users</p>

        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Rating</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Type</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Comment</th>
                <th className="text-left px-4 py-3 text-gray-600 font-medium">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
              ) : (feedback || []).length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-400">No feedback yet</td></tr>
              ) : (feedback || []).map((f: any) => (
                <tr key={f.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    {f.rating ? <span className="text-yellow-500">{"★".repeat(f.rating)}{"☆".repeat(5 - f.rating)}</span> : "—"}
                  </td>
                  <td className="px-4 py-3"><span className="px-2 py-0.5 bg-gray-100 rounded text-xs">{f.feedback_type}</span></td>
                  <td className="px-4 py-3 text-gray-700 max-w-md truncate">{f.comment || "—"}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{new Date(f.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
