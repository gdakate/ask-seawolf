"use client";
import { useEffect, useRef, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useAuth } from "@/hooks/useAuth";
import {
  getCourse, sendTeachMessage,
  getSessions, getSessionMessages, deleteSession,
} from "@/lib/api";
import type { TeachSession, TeachMessage } from "@/lib/api";

const KNOWLEDGE_LEVELS = [
  { value: "unknown",   label: "New to this",      desc: "Start from scratch",  icon: "🌱" },
  { value: "partial",   label: "Some background",  desc: "Know the basics",     icon: "🌿" },
  { value: "confident", label: "Pretty confident", desc: "Challenge me",        icon: "🌳" },
] as const;

const LEVEL_COLOR: Record<string, string> = {
  unknown: "text-green-500", partial: "text-yellow-500", confident: "text-blue-500",
};

interface Message { role: "user" | "assistant"; content: string; }

// Renders AI markdown in chat bubbles
function MsgContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        // No headers in chat — render as bold paragraph instead
        h1: ({ children }) => <p className="font-bold mb-1">{children}</p>,
        h2: ({ children }) => <p className="font-bold mb-1">{children}</p>,
        h3: ({ children }) => <p className="font-semibold mb-1">{children}</p>,
        p:  ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        code: ({ children, className }) => {
          const isBlock = className?.includes("language-");
          return isBlock
            ? <code className="block bg-black/10 dark:bg-white/10 rounded px-3 py-2 text-xs font-mono whitespace-pre-wrap my-2">{children}</code>
            : <code className="bg-black/10 dark:bg-white/10 rounded px-1 py-0.5 text-xs font-mono">{children}</code>;
        },
        pre: ({ children }) => <>{children}</>,
        ul: ({ children }) => <ul className="list-disc list-inside space-y-0.5 mb-2">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside space-y-0.5 mb-2">{children}</ol>,
        li: ({ children }) => <li className="text-sm">{children}</li>,
      }}>
      {content}
    </ReactMarkdown>
  );
}

function TeachContent({ id }: { id: string }) {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const searchParams = useSearchParams();

  const preSection = searchParams.get("section");
  const preTitle   = searchParams.get("title");

  type View = "history" | "resume_prompt" | "setup" | "chat" | "view_session";
  const [view, setView]             = useState<View>(preSection ? "resume_prompt" : "history");
  const [sessionId, setSessionId]   = useState<string | undefined>(undefined);
  const [viewingSession, setViewingSession] = useState<string | null>(null);
  const [knowledgeLevel, setKnowledgeLevel] = useState<"unknown" | "partial" | "confident">("unknown");
  const [messages, setMessages]     = useState<Message[]>([]);
  const [input, setInput]           = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const { data: course } = useQuery({
    queryKey: ["course", id],
    queryFn: () => getCourse(id),
    enabled: isLoggedIn,
  });

  // Sessions for this course (used by history + resume prompt)
  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ["sessions", id],
    queryFn: () => getSessions(id),
    enabled: isLoggedIn && (view === "history" || view === "resume_prompt"),
  });

  const { data: viewMessages = [], isLoading: viewLoading } = useQuery({
    queryKey: ["session_msgs", viewingSession],
    queryFn: () => getSessionMessages(viewingSession!),
    enabled: !!viewingSession && view === "view_session",
  });

  const sendMut = useMutation({
    mutationFn: (message: string) =>
      sendTeachMessage({
        course_id: id, message, session_id: sessionId,
        section_id: preSection ?? undefined,
        knowledge_level: knowledgeLevel,
      }),
    onSuccess: (data) => {
      setSessionId(data.session_id);
      setMessages((prev) => [...prev, { role: "assistant", content: data.response }]);
      qc.invalidateQueries({ queryKey: ["sessions", id] });
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sessions", id] }),
  });

  const resumeSession = (s: TeachSession) => {
    setSessionId(s.id);
    setKnowledgeLevel(s.knowledge_level as "unknown" | "partial" | "confident");
    getSessionMessages(s.id).then((msgs: TeachMessage[]) => {
      setMessages(msgs.map(m => ({ role: m.role, content: m.content })));
      setView("chat");
    });
  };

  const startFresh = () => {
    setSessionId(undefined);
    setMessages([]);
    setView("setup");
  };

  const handleStart = () => {
    setView("chat");
    const greeting = preTitle
      ? `Let's study "${preTitle}". My level: "${KNOWLEDGE_LEVELS.find(k => k.value === knowledgeLevel)?.label}".`
      : `I want to study this course. My level: "${KNOWLEDGE_LEVELS.find(k => k.value === knowledgeLevel)?.label}". Where should we start?`;
    setMessages([{ role: "user", content: greeting }]);
    sendMut.mutate(greeting);
  };

  const handleSend = () => {
    const msg = input.trim();
    if (!msg || sendMut.isPending) return;
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setInput("");
    sendMut.mutate(msg);
  };

  if (loading || !isLoggedIn) return null;

  // Existing sessions for this specific section
  const sectionSessions = preSection
    ? sessions.filter((s: TeachSession) => s.section_id === preSection)
    : [];

  // ── Resume prompt ───────────────────────────────────────────────────
  if (view === "resume_prompt") {
    const hasPrev = !sessionsLoading && sectionSessions.length > 0;
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <button onClick={() => router.back()}
          className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] mb-6 block transition-colors">
          ← Back
        </button>
        <div className="glass-card rounded-xl overflow-hidden">
          <div className="hero-bg px-6 py-8 text-center relative">
            <div className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(255,255,255,0.3) 0%, transparent 70%)" }} />
            <div className="relative">
              <div className="w-12 h-12 rounded-2xl bg-white/30 backdrop-blur-sm border border-white/40 flex items-center justify-center text-2xl mx-auto mb-3">🧠</div>
              {preTitle && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/30 backdrop-blur-sm border border-white/40 text-xs font-medium text-[var(--text-primary)]">
                  📍 {preTitle}
                </span>
              )}
            </div>
          </div>

          <div className="p-6">
            {sessionsLoading ? (
              <p className="text-sm text-[var(--text-muted)] text-center py-4">Loading...</p>
            ) : hasPrev ? (
              <div className="space-y-4">
                <p className="text-sm font-semibold text-[var(--text-primary)] text-center">
                  You have {sectionSessions.length} previous session{sectionSessions.length > 1 ? "s" : ""} for this section.
                </p>
                <div className="space-y-2">
                  {sectionSessions.slice(0, 3).map((s: TeachSession) => (
                    <button key={s.id} onClick={() => resumeSession(s)}
                      className="w-full text-left p-3 rounded-xl border border-[var(--border)] hover:border-[var(--accent)]/50 hover:bg-[var(--accent)]/4 transition-colors">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-medium ${LEVEL_COLOR[s.knowledge_level]}`}>
                          {KNOWLEDGE_LEVELS.find(k => k.value === s.knowledge_level)?.icon}{" "}
                          {KNOWLEDGE_LEVELS.find(k => k.value === s.knowledge_level)?.label}
                        </span>
                        <span className="text-xs text-[var(--text-muted)]">· {s.message_count} messages</span>
                        <span className="text-xs text-[var(--text-muted)] ml-auto">
                          {new Date(s.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      {s.preview && (
                        <p className="text-xs text-[var(--text-muted)] line-clamp-1">{s.preview}</p>
                      )}
                    </button>
                  ))}
                </div>
                <div className="border-t border-[var(--border)] pt-4">
                  <button onClick={startFresh}
                    className="w-full py-2.5 rounded-xl border border-[var(--border)] text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--accent)]/40 transition-colors">
                    Start a new session instead
                  </button>
                </div>
              </div>
            ) : (
              // No previous sessions — go straight to setup
              <div className="text-center py-2">
                <p className="text-sm text-[var(--text-muted)] mb-4">No previous sessions for this section.</p>
                <button onClick={() => setView("setup")}
                  className="px-6 py-2.5 btn-water text-white rounded-xl font-semibold text-sm">
                  Start Session
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ── History ─────────────────────────────────────────────────────────
  if (view === "history") {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => router.back()}
            className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">← Back</button>
          <h1 className="font-display text-xl font-bold text-[var(--text-primary)] flex-1">Study Sessions</h1>
          <button onClick={() => setView("setup")}
            className="px-4 py-2 btn-water text-white rounded-lg text-sm font-medium">
            + New Session
          </button>
        </div>
        <p className="text-sm text-[var(--text-muted)] mb-4">{course?.name}</p>

        {sessionsLoading ? (
          <div className="h-32 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
        ) : sessions.length === 0 ? (
          <div className="glass-card rounded-xl p-12 text-center">
            <div className="text-4xl mb-4">🧠</div>
            <p className="text-[var(--text-muted)] text-sm mb-4">No study sessions yet.</p>
            <button onClick={() => setView("setup")}
              className="px-5 py-2.5 btn-water text-white rounded-lg text-sm font-medium">
              Start Your First Session
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((s: TeachSession) => (
              <div key={s.id} className="glass-card rounded-xl p-4">
                <div className="flex items-start gap-3 mb-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      {s.section_title && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
                          {s.section_title}
                        </span>
                      )}
                      <span className={`text-xs font-medium ${LEVEL_COLOR[s.knowledge_level] ?? ""}`}>
                        {KNOWLEDGE_LEVELS.find(k => k.value === s.knowledge_level)?.icon}{" "}
                        {KNOWLEDGE_LEVELS.find(k => k.value === s.knowledge_level)?.label}
                      </span>
                      <span className="text-xs text-[var(--text-muted)]">{s.message_count} messages</span>
                      <span className="text-xs text-[var(--text-muted)] ml-auto">
                        {new Date(s.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    {s.preview && (
                      <p className="text-xs text-[var(--text-muted)] line-clamp-2">{s.preview}</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => resumeSession(s)}
                    className="px-3 py-1.5 text-xs rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 font-medium transition-colors">
                    Resume →
                  </button>
                  <button onClick={() => { setViewingSession(s.id); setView("view_session"); }}
                    className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                    View
                  </button>
                  <button onClick={() => { if (confirm("Delete this session?")) deleteMut.mutate(s.id); }}
                    className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-red-500 hover:border-red-300 transition-colors ml-auto">
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ── View past session ────────────────────────────────────────────────
  if (view === "view_session") {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <button onClick={() => { setView("history"); setViewingSession(null); }}
          className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] mb-6 block transition-colors">
          ← Back to sessions
        </button>
        <div className="space-y-4">
          {viewLoading ? (
            <div className="h-20 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
          ) : (viewMessages as TeachMessage[]).map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              {msg.role === "assistant" && (
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-sky-400 flex items-center justify-center text-white text-xs font-bold mr-2 mt-0.5 shrink-0">SC</div>
              )}
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-[var(--accent)] text-white rounded-tr-sm"
                  : "glass-card border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm"
              }`}>
                {msg.role === "assistant" ? <MsgContent content={msg.content} /> : msg.content}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // ── Setup ────────────────────────────────────────────────────────────
  if (view === "setup") {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center gap-3 mb-6">
          <button onClick={() => preSection ? setView("resume_prompt") : setView("history")}
            className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">← Back</button>
        </div>
        <div className="glass-card rounded-xl overflow-hidden">
          <div className="hero-bg px-6 py-8 text-center relative">
            <div className="absolute inset-0 pointer-events-none"
              style={{ background: "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(255,255,255,0.3) 0%, transparent 70%)" }} />
            <div className="relative">
              <div className="w-14 h-14 rounded-2xl bg-white/30 backdrop-blur-sm border border-white/40 flex items-center justify-center text-2xl mx-auto mb-3">🧠</div>
              <h1 className="font-display text-xl font-bold text-[var(--text-primary)]">New Study Session</h1>
              {preTitle ? (
                <div className="mt-2 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/30 backdrop-blur-sm border border-white/40">
                  <span className="text-xs font-medium text-[var(--text-primary)]">📍 {preTitle}</span>
                </div>
              ) : (
                <p className="text-sm text-[var(--text-secondary)] mt-1">{course?.name}</p>
              )}
            </div>
          </div>
          <div className="p-6 space-y-5">
            <div>
              <label className="block text-xs font-semibold text-[var(--text-secondary)] mb-3 uppercase tracking-wide">
                Your Knowledge Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {KNOWLEDGE_LEVELS.map((k) => (
                  <button key={k.value} onClick={() => setKnowledgeLevel(k.value)}
                    className={`p-3 rounded-xl border-2 text-center transition-all ${
                      knowledgeLevel === k.value
                        ? "border-[var(--accent)] bg-[var(--accent)]/8"
                        : "border-[var(--border)] hover:border-[var(--accent)]/40"
                    }`}>
                    <div className="text-2xl mb-1">{k.icon}</div>
                    <div className={`text-xs font-semibold leading-tight ${knowledgeLevel === k.value ? "text-[var(--accent)]" : "text-[var(--text-primary)]"}`}>
                      {k.label}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] mt-0.5">{k.desc}</div>
                  </button>
                ))}
              </div>
            </div>
            <button onClick={handleStart}
              className="w-full py-3 btn-water text-white rounded-xl font-semibold text-sm">
              Start Session
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ── Chat ─────────────────────────────────────────────────────────────
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 flex flex-col" style={{ height: "calc(100vh - 3.5rem)" }}>
      <div className="py-3 border-b border-[var(--border)] flex items-center gap-3 shrink-0">
        <button onClick={() => setView("history")}
          className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">←</button>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-[var(--text-primary)] truncate">
            {preTitle ?? course?.name ?? "Study Session"}
          </p>
          <p className="text-xs text-[var(--text-muted)]">
            {KNOWLEDGE_LEVELS.find(k => k.value === knowledgeLevel)?.icon}{" "}
            {KNOWLEDGE_LEVELS.find(k => k.value === knowledgeLevel)?.label}
          </p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-sky-400 flex items-center justify-center text-white text-xs font-bold mr-2 mt-0.5 shrink-0">
                SC
              </div>
            )}
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
              msg.role === "user"
                ? "bg-[var(--accent)] text-white rounded-tr-sm"
                : "glass-card border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm"
            }`}>
              {msg.role === "assistant" ? <MsgContent content={msg.content} /> : msg.content}
            </div>
          </div>
        ))}

        {sendMut.isPending && messages[messages.length - 1]?.role === "user" && (
          <div className="flex justify-start">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[var(--accent)] to-sky-400 flex items-center justify-center text-white text-xs font-bold mr-2 mt-0.5 shrink-0">SC</div>
            <div className="glass-card border border-[var(--border)] rounded-2xl rounded-tl-sm px-4 py-3">
              <span className="inline-flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[var(--text-muted)] animate-bounce" style={{ animationDelay: "300ms" }} />
              </span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="py-3 border-t border-[var(--border)] shrink-0">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="Ask a question or share your thinking..."
            className="flex-1 px-4 py-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60 transition-colors"
            disabled={sendMut.isPending}
          />
          <button onClick={handleSend} disabled={!input.trim() || sendMut.isPending}
            className="px-4 py-2.5 btn-water text-white rounded-xl text-sm font-medium disabled:opacity-50">
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TeachPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<div className="flex items-center justify-center h-64 text-[var(--text-muted)] text-sm">Loading...</div>}>
      <TeachContent id={params.id} />
    </Suspense>
  );
}
