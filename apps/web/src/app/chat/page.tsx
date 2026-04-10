"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { sendChatQuery, type ChatResponse, type Citation } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  office_routing?: ChatResponse["office_routing"];
  follow_up_questions?: string[];
  confidence_score?: number;
  warning?: string;
  loading?: boolean;
}

function ChatContent() {
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const processedInitial = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (initialQuery && !processedInitial.current) {
      processedInitial.current = true;
      handleSend(initialQuery);
    }
  }, [initialQuery]);

  const handleSend = async (text?: string) => {
    const query = (text || input).trim();
    if (!query || isLoading) return;
    setInput("");

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: query };
    const loadingMsg: Message = { id: crypto.randomUUID(), role: "assistant", content: "", loading: true };
    setMessages((prev) => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);

    try {
      const res = await sendChatQuery(query, sessionId);
      setSessionId(res.session_id);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? {
                ...m,
                content: res.answer,
                citations: res.citations,
                office_routing: res.office_routing,
                follow_up_questions: res.follow_up_questions,
                confidence_score: res.confidence_score,
                warning: res.warning,
                loading: false,
              }
            : m
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: "Sorry, something went wrong. Please try again.", loading: false }
            : m
        )
      );
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-col" style={{ minHeight: "calc(100vh - 12rem)" }}>
      {/* Messages area */}
      <div className="flex-1 space-y-6 pb-4">
        {messages.length === 0 && (
          <div className="text-center pt-20">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-sbu-red/10 text-sbu-red mb-4">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
              </svg>
            </div>
            <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] mb-2">
              Ask me anything about Stony Brook
            </h2>
            <p className="text-[var(--text-muted)] text-sm">
              Admissions, tuition, housing, financial aid, registration, and more.
            </p>
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] ${
                msg.role === "user"
                  ? "bg-sbu-red text-white rounded-2xl rounded-br-md px-4 py-3"
                  : "bg-white dark:bg-[var(--bg-secondary)] border border-[var(--border)] rounded-2xl rounded-bl-md px-5 py-4 shadow-sm"
              }`}
            >
              {msg.loading ? (
                <div className="flex items-center gap-2 text-[var(--text-muted)]">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 rounded-full bg-sbu-red/40 animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 rounded-full bg-sbu-red/40 animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 rounded-full bg-sbu-red/40 animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                  <span className="text-sm">Searching university sources...</span>
                </div>
              ) : (
                <>
                  {/* Warning badge */}
                  {msg.warning && (
                    <div className="mb-3 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-xs text-amber-800 dark:text-amber-200">
                      ⚠️ {msg.warning}
                    </div>
                  )}

                  {/* Answer text */}
                  <div className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</div>

                  {/* Citations */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-[var(--border)]">
                      <h4 className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider mb-2">
                        Sources
                      </h4>
                      <div className="space-y-2">
                        {msg.citations.map((c, i) => (
                          <a
                            key={i}
                            href={c.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block p-2.5 rounded-lg bg-[var(--bg-secondary)] dark:bg-[var(--bg-chat)] hover:bg-sbu-red/5 border border-transparent hover:border-sbu-red/20 transition-colors group"
                          >
                            <div className="text-xs font-medium text-sbu-red group-hover:underline">{c.title}</div>
                            <div className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">{c.snippet}</div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Office routing */}
                  {msg.office_routing && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                      <h4 className="text-xs font-semibold text-blue-800 dark:text-blue-200 mb-1">
                        📞 Contact {msg.office_routing.name}
                      </h4>
                      <div className="text-xs text-blue-700 dark:text-blue-300 space-y-0.5">
                        {msg.office_routing.phone && <div>Phone: {msg.office_routing.phone}</div>}
                        {msg.office_routing.email && <div>Email: {msg.office_routing.email}</div>}
                        {msg.office_routing.url && (
                          <a href={msg.office_routing.url} target="_blank" rel="noopener noreferrer" className="underline">
                            Visit website →
                          </a>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Follow-up questions */}
                  {msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                    <div className="mt-4 flex flex-wrap gap-1.5">
                      {msg.follow_up_questions.map((q, i) => (
                        <button
                          key={i}
                          onClick={() => handleSend(q)}
                          className="text-xs px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--text-muted)] hover:text-sbu-red hover:border-sbu-red/30 transition-colors"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Confidence indicator */}
                  {msg.confidence_score !== undefined && msg.role === "assistant" && (
                    <div className="mt-3 flex items-center gap-1.5">
                      <div
                        className={`w-1.5 h-1.5 rounded-full ${
                          msg.confidence_score > 0.7
                            ? "bg-green-500"
                            : msg.confidence_score > 0.3
                            ? "bg-amber-500"
                            : "bg-red-400"
                        }`}
                      />
                      <span className="text-[10px] text-[var(--text-muted)]">
                        {msg.confidence_score > 0.7
                          ? "High confidence"
                          : msg.confidence_score > 0.3
                          ? "Moderate confidence"
                          : "Low confidence — verify with office"}
                      </span>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="sticky bottom-0 bg-[var(--bg-primary)] pt-3 pb-4 border-t border-[var(--border)]">
        <div className="flex items-center gap-2 bg-white dark:bg-[var(--bg-secondary)] rounded-xl border border-[var(--border)] shadow-sm focus-within:ring-2 focus-within:ring-sbu-red/20">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Type your question..."
            className="flex-1 px-4 py-3 text-sm bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
            disabled={isLoading}
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            className="m-1.5 p-2 bg-sbu-red text-white rounded-lg hover:bg-sbu-red-dark disabled:opacity-40 transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
        <p className="text-[10px] text-[var(--text-muted)] text-center mt-2">
          Answers are generated from official Stony Brook University sources. Always verify important details.
        </p>
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
