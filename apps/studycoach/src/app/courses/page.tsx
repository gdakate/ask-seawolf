"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getCourses, createCourse, deleteCourse } from "@/lib/api";

export default function CoursesPage() {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [code, setCode] = useState("");
  const [courseName, setCourseName] = useState("");
  const [description, setDescription] = useState("");
  const [formError, setFormError] = useState("");

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  const { data: courses = [], isLoading } = useQuery({
    queryKey: ["courses"],
    queryFn: getCourses,
    enabled: isLoggedIn,
  });

  const createMut = useMutation({
    mutationFn: createCourse,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["courses"] });
      setShowForm(false); setCode(""); setCourseName(""); setDescription(""); setFormError("");
    },
    onError: (e: any) => setFormError(e.message),
  });

  const deleteMut = useMutation({
    mutationFn: deleteCourse,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["courses"] }),
  });

  if (loading || !isLoggedIn) return null;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">Courses</h1>
        <button onClick={() => setShowForm(true)}
          className="px-4 py-2 btn-water text-white rounded-lg text-sm font-medium">
          + New Course
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="glass-card rounded-xl p-5 space-y-4">
          <h2 className="font-semibold text-[var(--text-primary)]">Add Course</h2>
          {formError && (
            <p className="text-sm text-red-500">{formError}</p>
          )}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Course Code</label>
              <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="CSE 214"
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Course Name</label>
              <input value={courseName} onChange={(e) => setCourseName(e.target.value)} placeholder="Data Structures"
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Description <span className="font-normal text-[var(--text-muted)]">(optional)</span></label>
            <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Brief overview..."
              className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                if (!code.trim() || !courseName.trim()) { setFormError("Code and name are required"); return; }
                createMut.mutate({ code: code.trim(), name: courseName.trim(), description: description.trim() || undefined });
              }}
              disabled={createMut.isPending}
              className="px-4 py-2 btn-water text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {createMut.isPending ? "Creating..." : "Create"}
            </button>
            <button onClick={() => { setShowForm(false); setFormError(""); }}
              className="px-4 py-2 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Course list */}
      {isLoading ? (
        <div className="h-32 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
      ) : courses.length === 0 ? (
        <div className="glass-card rounded-xl p-12 text-center">
          <p className="text-4xl mb-4">📚</p>
          <p className="text-[var(--text-muted)] text-sm mb-4">No courses yet. Add your first course to get started.</p>
          <button onClick={() => setShowForm(true)}
            className="px-5 py-2.5 btn-water text-white rounded-lg text-sm font-medium">
            Add Course
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {courses.map((c) => (
            <div key={c.id} className="glass-card rounded-xl p-4 flex items-center gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded">
                    {c.code}
                  </span>
                </div>
                <p className="font-medium text-[var(--text-primary)] truncate">{c.name}</p>
                {c.description && <p className="text-xs text-[var(--text-muted)] truncate mt-0.5">{c.description}</p>}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <Link href={`/courses/${c.id}`}
                  className="px-3 py-1.5 text-xs rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 font-medium transition-colors">
                  Open
                </Link>
                <button onClick={() => { if (confirm("Delete this course?")) deleteMut.mutate(c.id); }}
                  className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-red-500 hover:border-red-300 transition-colors">
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
