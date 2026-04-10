"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { sendChatQuery, type ChatResponse, type Citation } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";

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
  const router = useRouter();
  const { isLoggedIn, loading: authLoading } = useAuth();
  const initialQuery = searchParams.get("q");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sessionId, setSessionId] = useState<string | undefined>();
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const processedInitial = useRef(false);

  useEffect(() => {
    if (!authLoading && !isLoggedIn) {
      const current = window.location.pathname + window.location.search;
      router.replace(`/login?redirect=${encodeURIComponent(current)}`);
    }
  }, [isLoggedIn, authLoading, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (initialQuery && !processedInitial.current && isLoggedIn) {
      processedInitial.current = true;
      handleSend(initialQuery);
    }
  }, [initialQuery, isLoggedIn]);

  if (authLoading || !isLoggedIn) {
    return (
      <div className="flex items-center justify-center h-64 text-[var(--text-muted)]">
        <div className="flex gap-1.5">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              className="w-2 h-2 rounded-full bg-water-current/60 animate-bounce"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </div>
      </div>
    );
  }

  const handleSend = async (text?: string) => {
    const query = (text || input).trim();
    if (!query || isLoading) return;
    setInput("");

    const userMsg: Message  = { id: crypto.randomUUID(), role: "user",      content: query };
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
                content:              res.answer,
                citations:            res.citations,
                office_routing:       res.office_routing,
                follow_up_questions:  res.follow_up_questions,
                confidence_score:     res.confidence_score,
                warning:              res.warning,
                loading:              false,
              }
            : m
        )
      );
    } catch {
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
    <div
      className="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex flex-col"
      style={{ minHeight: "calc(100vh - 12rem)" }}
    >
      {/* ── Messages ── */}
      <div className="flex-1 space-y-6 pb-4">
        {messages.length === 0 && (
          <div className="text-center pt-20">
            {/* Icon with water glow */}
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-water-sky dark:bg-water-abyss border border-water-shallow/60 text-[var(--accent)] mb-4 shadow-[0_0_20px_rgba(14,165,233,0.15)]">
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
                  /* user bubble: deep ocean blue */
                  ? "bg-[var(--accent)] text-white rounded-2xl rounded-br-md px-4 py-3 shadow-[0_2px_12px_var(--accent-glow)]"
                  /* assistant bubble: glass */
                  : "glass-card rounded-2xl rounded-bl-md px-5 py-4"
              }`}
            >
              {msg.loading ? (
                <div className="flex items-center gap-2 text-[var(--text-muted)]">
                  <div className="flex gap-1">
                    {[0, 150, 300].map((delay) => (
                      <span
                        key={delay}
                        className="w-2 h-2 rounded-full bg-water-current/50 animate-bounce"
                        style={{ animationDelay: `${delay}ms` }}
                      />
                    ))}
                  </div>
                  <span className="text-sm">Searching university sources...</span>
                </div>
              ) : (
                <>
                  {/* Warning */}
                  {msg.warning && (
                    <div className="mb-3 px-3 py-2 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg text-xs text-amber-800 dark:text-amber-200">
                      ⚠️ {msg.warning}
                    </div>
                  )}

                  {/* Answer */}
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
                            className="block p-2.5 rounded-lg bg-water-sky/40 dark:bg-water-abyss/60 hover:bg-water-sky dark:hover:bg-water-abyss border border-transparent hover:border-water-current/30 transition-all group"
                          >
                            <div className="text-xs font-medium text-[var(--accent)] group-hover:underline">{c.title}</div>
                            <div className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">{c.snippet}</div>
                          </a>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Office routing */}
                  {msg.office_routing && (
                    <div className="mt-4 p-3 bg-water-sky/60 dark:bg-water-abyss/60 border border-water-shallow dark:border-water-deep rounded-lg">
                      <h4 className="text-xs font-semibold text-[var(--accent)] mb-1">
                        Contact {msg.office_routing.name}
                      </h4>
                      <div className="text-xs text-[var(--text-secondary)] space-y-0.5">
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
                          className="text-xs px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--accent)] hover:border-water-current/40 hover:bg-water-sky/50 dark:hover:bg-water-abyss/50 transition-all"
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
                            ? "bg-water-current shadow-[0_0_5px_rgba(14,165,233,0.6)]"
                            : msg.confidence_score > 0.3
                            ? "bg-amber-400"
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

      {/* ── Input bar ── */}
      <div className="sticky bottom-0 bg-[var(--bg-primary)] pt-3 pb-4 border-t border-[var(--border)]">
        <div className="glass-card flex items-center rounded-xl transition-all focus-within:water-ring">
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
            className="btn-water m-1.5 p-2 text-white rounded-lg disabled:opacity-40"
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
    <Suspense fallback={
      <div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Loading...</div>
    }>
      <ChatContent />
    </Suspense>
  );
}
