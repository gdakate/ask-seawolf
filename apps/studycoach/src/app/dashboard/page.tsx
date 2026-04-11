"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient, useQueries } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import {
  getCourses, getPlan, updatePlanItem,
  getAllSessions, getSessionMessages, deleteSession,
} from "@/lib/api";
import type { Course, PlanItem, TeachSessionWithCourse, TeachMessage } from "@/lib/api";

const TYPE_ICON: Record<string, string> = {
  study: "📖", review: "🔁", practice: "✏️", exam: "🎯",
  assignment: "📋", lecture: "📝", other: "📌",
};
const LEVEL_ICON: Record<string, string> = { unknown: "🌱", partial: "🌿", confident: "🌳" };

export default function DashboardPage() {
  const { isLoggedIn, loading, name } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [tab, setTab] = useState<"courses" | "sessions">("courses");
  const [planFilter, setPlanFilter] = useState<"upcoming" | "done">("upcoming");
  const [viewingSession, setViewingSession] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  const { data: courses = [], isLoading: coursesLoading } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
    enabled: isLoggedIn,
  });

  const planResults = useQueries({
    queries: courses.map((c: Course) => ({
      queryKey: ["plan", c.id],
      queryFn: () => getPlan(c.id),
      enabled: isLoggedIn && courses.length > 0,
    })),
  });

  const { data: sessions = [], isLoading: sessionsLoading } = useQuery({
    queryKey: ["all_sessions"],
    queryFn: getAllSessions,
    enabled: isLoggedIn && tab === "sessions",
  });

  const { data: viewMessages = [], isLoading: viewLoading } = useQuery({
    queryKey: ["session_msgs", viewingSession],
    queryFn: () => getSessionMessages(viewingSession!),
    enabled: !!viewingSession,
  });

  const updateMut = useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: Partial<PlanItem> }) =>
      updatePlanItem(itemId, data),
    onSuccess: () => {
      courses.forEach((c: Course) => qc.invalidateQueries({ queryKey: ["plan", c.id] }));
    },
  });

  const deleteMut = useMutation({
    mutationFn: deleteSession,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["all_sessions"] });
      setViewingSession(null);
    },
  });

  if (loading || !isLoggedIn) return null;

  const today = new Date().toISOString().split("T")[0];
  const planQueries = courses.map((c: Course, i: number) => ({
    course: c,
    items: (planResults[i]?.data ?? []) as PlanItem[],
  }));
  const allItems = planQueries.flatMap(({ course, items }) =>
    items.map(i => ({ ...i, courseName: course.name, courseCode: course.code, courseId: course.id }))
  );

  const todayCount = allItems.filter(i => !i.is_completed && i.due_date?.startsWith(today)).length;
  const totalDone  = allItems.filter(i => i.is_completed).length;
  const progress   = allItems.length > 0 ? Math.round((totalDone / allItems.length) * 100) : 0;

  const planItems = allItems.filter(i => {
    if (planFilter === "done") return i.is_completed;
    return !i.is_completed;
  }).sort((a, b) => {
    if (!a.due_date && !b.due_date) return 0;
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return a.due_date.localeCompare(b.due_date);
  });

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">

      {/* Hero */}
      <div className="hero-bg rounded-2xl p-6 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 80% 60% at 50% -10%, rgba(255,255,255,0.35) 0%, transparent 70%)" }} />
        <div className="bubble absolute bottom-3 left-8 w-5 h-5" style={{ "--dur": "5s", "--delay": "0s" } as any} />
        <div className="bubble absolute bottom-2 left-20 w-3 h-3" style={{ "--dur": "4s", "--delay": "1.5s" } as any} />
        <div className="bubble absolute bottom-4 right-12 w-4 h-4" style={{ "--dur": "6s", "--delay": "0.8s" } as any} />

        <div className="relative flex items-center justify-between gap-4 flex-wrap">
          <div>
            <p className="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-widest mb-1">
              {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
            </p>
            <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">
              {name ? `Hey, ${name.split(" ")[0]} 👋` : "Dashboard"}
            </h1>
            <p className="text-sm text-[var(--text-secondary)] mt-1">
              {todayCount > 0
                ? <><span className="font-semibold text-[var(--accent)]">{todayCount} task{todayCount > 1 ? "s" : ""}</span> due today</>
                : "No tasks due today"}
            </p>
          </div>

          {allItems.length > 0 && (
            <div className="flex items-center gap-3 glass-card rounded-xl px-4 py-3">
              <svg width="48" height="48" viewBox="0 0 48 48">
                <circle cx="24" cy="24" r="19" fill="none" stroke="rgba(3,105,161,0.12)" strokeWidth="4.5" />
                <circle cx="24" cy="24" r="19" fill="none" stroke="var(--accent)" strokeWidth="4.5"
                  strokeDasharray={`${2 * Math.PI * 19}`}
                  strokeDashoffset={`${2 * Math.PI * 19 * (1 - progress / 100)}`}
                  strokeLinecap="round"
                  style={{ transform: "rotate(-90deg)", transformOrigin: "50% 50%", transition: "stroke-dashoffset 0.8s ease" }} />
                <text x="24" y="28" textAnchor="middle" fontSize="11" fill="var(--accent)" fontWeight="700">{progress}%</text>
              </svg>
              <div>
                <p className="text-sm font-bold text-[var(--text-primary)]">{totalDone}<span className="text-[var(--text-muted)] font-normal text-xs">/{allItems.length}</span></p>
                <p className="text-[10px] text-[var(--text-muted)]">tasks done</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 2-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6 items-start">

        {/* Left: Courses / Sessions tabs */}
        <div className="space-y-4">
          {/* Tab bar */}
          <div className="flex items-center gap-1 p-1 glass-card rounded-xl w-fit">
            {(["courses", "sessions"] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                  tab === t ? "bg-[var(--accent)] text-white shadow-sm" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}>
                {t === "courses" ? "📚 Courses" : "💬 Sessions"}
              </button>
            ))}
          </div>

          {/* Courses tab */}
          {tab === "courses" && (
            <div>
              <div className="flex items-center justify-between mb-3">
                <h2 className="font-semibold text-[var(--text-primary)]">Your Courses</h2>
                <Link href="/courses" className="text-xs text-[var(--accent)] hover:underline">Manage →</Link>
              </div>

              {coursesLoading ? (
                <div className="h-32 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
              ) : courses.length === 0 ? (
                <div className="glass-card rounded-xl p-10 text-center">
                  <p className="text-4xl mb-3">📚</p>
                  <p className="text-[var(--text-muted)] text-sm mb-4">No courses yet.</p>
                  <Link href="/courses" className="inline-block px-5 py-2.5 btn-water text-white rounded-lg text-sm font-medium">
                    Add Your First Course
                  </Link>
                </div>
              ) : (
                <div className="grid gap-3 sm:grid-cols-2">
                  {courses.map((c: Course) => (
                    <Link key={c.id} href={`/courses/${c.id}`}
                      className="glass-card rounded-xl p-4 hover:border-[var(--accent)]/40 transition-colors group block">
                      <div className="flex items-start justify-between mb-2">
                        <span className="text-xs font-mono font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded">
                          {c.code}
                        </span>
                        <span className="text-[var(--text-muted)] text-sm group-hover:text-[var(--accent)] transition-colors">→</span>
                      </div>
                      <p className="font-semibold text-sm text-[var(--text-primary)] leading-snug">{c.name}</p>
                      {c.description && (
                        <p className="text-xs text-[var(--text-muted)] mt-1 line-clamp-1">{c.description}</p>
                      )}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sessions tab */}
          {tab === "sessions" && (
            <div>
              {viewingSession ? (
                <div>
                  <button onClick={() => setViewingSession(null)}
                    className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] mb-4 block transition-colors">
                    ← Back to sessions
                  </button>
                  <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                    {viewLoading ? (
                      <div className="h-20 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
                    ) : (
                      (viewMessages as TeachMessage[]).map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                          {msg.role === "assistant" && (
                            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-[var(--accent)] to-sky-400 flex items-center justify-center text-white text-[10px] font-bold mr-2 mt-0.5 shrink-0">SC</div>
                          )}
                          <div className={`max-w-[80%] rounded-2xl px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap ${
                            msg.role === "user"
                              ? "bg-[var(--accent)] text-white rounded-tr-sm"
                              : "glass-card border border-[var(--border)] text-[var(--text-primary)] rounded-tl-sm"
                          }`}>
                            {msg.content}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              ) : (
                <div>
                  <h2 className="font-semibold text-[var(--text-primary)] mb-3">Study Sessions</h2>
                  {sessionsLoading ? (
                    <div className="h-32 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
                  ) : sessions.length === 0 ? (
                    <div className="glass-card rounded-xl p-10 text-center">
                      <p className="text-4xl mb-3">💬</p>
                      <p className="text-[var(--text-muted)] text-sm mb-4">No study sessions yet.</p>
                      <Link href="/courses" className="inline-block px-5 py-2.5 btn-water text-white rounded-lg text-sm font-medium">
                        Go to a Course
                      </Link>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {(sessions as TeachSessionWithCourse[]).map((s) => (
                        <div key={s.id} className="glass-card rounded-xl p-4">
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 flex-wrap mb-1">
                                <span className="text-xs font-mono font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded">
                                  {s.course_code}
                                </span>
                                {s.section_title && (
                                  <span className="text-xs text-[var(--text-secondary)] truncate max-w-[160px]">
                                    📍 {s.section_title}
                                  </span>
                                )}
                                <span className="text-xs text-[var(--text-muted)]">
                                  {LEVEL_ICON[s.knowledge_level]} {s.message_count} msgs
                                </span>
                              </div>
                              {s.preview && (
                                <p className="text-xs text-[var(--text-muted)] line-clamp-2">{s.preview}</p>
                              )}
                            </div>
                            <span className="text-[10px] text-[var(--text-muted)] shrink-0">
                              {new Date(s.created_at).toLocaleDateString()}
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button onClick={() => setViewingSession(s.id)}
                              className="px-2.5 py-1 text-xs rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 font-medium transition-colors">
                              View
                            </button>
                            <Link href={`/courses/${s.course_id}/teach`}
                              className="px-2.5 py-1 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">
                              Continue →
                            </Link>
                            <button onClick={() => { if (confirm("Delete?")) deleteMut.mutate(s.id); }}
                              className="px-2.5 py-1 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-red-500 hover:border-red-300 transition-colors ml-auto">
                              Delete
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Study Plan */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <span>📅</span> Study Plan
            </h2>
            <div className="flex gap-1">
              {(["upcoming", "done"] as const).map((f) => (
                <button key={f} onClick={() => setPlanFilter(f)}
                  className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-colors ${
                    planFilter === f
                      ? "bg-[var(--accent)] text-white"
                      : "border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                  }`}>
                  {f === "upcoming" ? "Todo" : "Done"}
                </button>
              ))}
            </div>
          </div>

          {coursesLoading ? (
            <div className="h-24 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
          ) : planItems.length === 0 ? (
            <div className="glass-card rounded-xl p-6 text-center">
              <p className="text-[var(--text-muted)] text-xs">
                {planFilter === "done" ? "Nothing completed yet." : "No upcoming tasks."}
              </p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-0.5">
              {planItems.map((item) => {
                const isToday   = item.due_date?.startsWith(today);
                const isOverdue = item.due_date && item.due_date < today && !item.is_completed;
                return (
                  <div key={item.id}
                    className={`glass-card rounded-xl p-3 flex items-start gap-2.5 ${item.is_completed ? "opacity-60" : ""}`}>
                    <button
                      onClick={() => updateMut.mutate({ itemId: item.id, data: { is_completed: !item.is_completed } })}
                      className={`w-4 h-4 rounded border-2 flex items-center justify-center shrink-0 mt-0.5 transition-colors ${
                        item.is_completed ? "bg-[var(--accent)] border-[var(--accent)]" : "border-[var(--border)] hover:border-[var(--accent)]/60"
                      }`}>
                      {item.is_completed && <span className="text-white text-[8px]">✓</span>}
                    </button>

                    <div className="min-w-0 flex-1">
                      <p className={`text-xs font-medium text-[var(--text-primary)] leading-snug ${item.is_completed ? "line-through" : ""}`}>
                        {item.title}
                      </p>
                      <div className="flex items-center gap-1.5 mt-1 flex-wrap">
                        <span className="text-[9px] font-mono font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-1.5 py-0.5 rounded">
                          {item.courseCode}
                        </span>
                        {item.due_date && (
                          <span className={`text-[10px] ${isOverdue ? "text-red-500 font-medium" : isToday ? "text-[var(--accent)] font-medium" : "text-[var(--text-muted)]"}`}>
                            {isToday ? "Today" : item.due_date.split("T")[0]}
                          </span>
                        )}
                      </div>
                    </div>

                    <Link href={`/courses/${item.courseId}/plan`}
                      className="text-[10px] text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors shrink-0">
                      →
                    </Link>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
