"use client";

import { useQuery } from "@tanstack/react-query";
import { getConversations, getConversationMessages } from "@/lib/api";
import { Sidebar } from "@/components/sidebar";
import { useState } from "react";

export default function ConversationsPage() {
  const { data: sessions, isLoading } = useQuery({ queryKey: ["conversations"], queryFn: getConversations });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data: messages } = useQuery({
    queryKey: ["messages", selectedId],
    queryFn: () => getConversationMessages(selectedId!),
    enabled: !!selectedId,
  });

  return (
    <div className="flex">
      <Sidebar />
      <main className="ml-56 flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Conversations</h1>
        <p className="text-sm text-gray-500 mb-6">Chat session logs</p>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-600">Sessions</div>
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
              {isLoading ? (
                <div className="p-4 text-gray-400">Loading...</div>
              ) : (sessions || []).map((s: any) => (
                <button key={s.id} onClick={() => setSelectedId(s.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 ${selectedId === s.id ? "bg-sbu-red/5 border-l-2 border-sbu-red" : ""}`}>
                  <div className="text-sm font-medium text-gray-900">{s.session_token.slice(0, 12)}...</div>
                  <div className="text-xs text-gray-400 mt-0.5">{s.message_count} messages · {new Date(s.last_active_at).toLocaleString()}</div>
                </button>
              ))}
              {!isLoading && (!sessions || sessions.length === 0) && (
                <div className="p-4 text-sm text-gray-400">No conversations yet</div>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-4 py-3 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-600">Messages</div>
            <div className="p-4 space-y-3 max-h-[600px] overflow-y-auto">
              {!selectedId ? (
                <p className="text-sm text-gray-400">Select a session to view messages</p>
              ) : (messages || []).map((m: any) => (
                <div key={m.id} className={`p-3 rounded-lg ${m.role === "user" ? "bg-sbu-red/5 border border-sbu-red/10" : "bg-gray-50"}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs font-semibold ${m.role === "user" ? "text-sbu-red" : "text-gray-600"}`}>{m.role}</span>
                    {m.confidence_score != null && (
                      <span className="text-[10px] text-gray-400">{(m.confidence_score * 100).toFixed(0)}% confidence</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{m.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
