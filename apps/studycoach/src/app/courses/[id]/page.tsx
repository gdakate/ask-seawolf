"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getCourse, uploadMaterial, deleteMaterial, deleteSection } from "@/lib/api";
import type { Material, Section } from "@/lib/api";

const DIFF_LABELS = ["", "Intro", "Basic", "Intermediate", "Advanced", "Expert"];
const DIFF_COLORS = ["", "text-green-500", "text-blue-400", "text-yellow-500", "text-orange-500", "text-red-500"];
const DIFF_BG    = ["", "bg-green-500/10", "bg-blue-400/10", "bg-yellow-500/10", "bg-orange-500/10", "bg-red-500/10"];

export default function CoursePage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const [activeTab, setActiveTab] = useState<string | null>(null);

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  const { data: course, isLoading } = useQuery({
    queryKey: ["course", id],
    queryFn: () => getCourse(id),
    enabled: isLoggedIn,
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasParsing = data?.materials?.some((m: Material) => m.status === "processing");
      return hasParsing ? 3000 : false;
    },
  });

  // Set first material as default active tab when data loads
  useEffect(() => {
    if (course?.materials?.length && !activeTab) {
      setActiveTab(course.materials[0].id);
    }
  }, [course?.materials, activeTab]);

  const deleteMat = useMutation({
    mutationFn: (matId: string) => deleteMaterial(id, matId),
    onSuccess: (_, matId) => {
      qc.invalidateQueries({ queryKey: ["course", id] });
      if (activeTab === matId) setActiveTab(null);
    },
  });

  const deleteSec = useMutation({
    mutationFn: (secId: string) => deleteSection(secId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["course", id] }),
  });

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    setUploading(true); setUploadError("");
    try {
      // Upload sequentially
      for (const file of files) {
        await uploadMaterial(id, file);
      }
      qc.invalidateQueries({ queryKey: ["course", id] });
    } catch (err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  if (loading || !isLoggedIn) return null;
  if (isLoading) return (
    <div className="flex items-center justify-center h-64 text-[var(--text-muted)] text-sm">Loading...</div>
  );
  if (!course) return (
    <div className="flex items-center justify-center h-64 text-[var(--text-muted)] text-sm">Course not found.</div>
  );

  const activeSections: Section[] = activeTab
    ? (course.sections_by_material?.[activeTab] ?? [])
    : course.sections;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <button onClick={() => router.back()}
            className="flex items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">
            ← Back
          </button>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="text-xs text-[var(--text-muted)]">{course.code}</span>
        </div>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">{course.name}</h1>
            <span className="text-xs font-mono font-bold text-[var(--accent)] bg-[var(--accent)]/10 px-2 py-0.5 rounded mt-1 inline-block">
              {course.code}
            </span>
          </div>
          <div className="flex gap-2 shrink-0">
            <Link href={`/courses/${id}/plan`}
              className="px-3 py-2 text-sm rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/40 transition-colors font-medium">
              📅 Plan
            </Link>
            <Link href={`/courses/${id}/teach`}
              className="px-3 py-2 text-sm btn-water text-white rounded-lg font-medium">
              🧠 Study
            </Link>
          </div>
        </div>
      </div>

      {/* Materials */}
      <section className="glass-card rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
            <span>📄</span> Materials
            {course.materials.length > 0 && (
              <span className="text-xs font-normal text-[var(--text-muted)]">({course.materials.length})</span>
            )}
          </h2>
          <label className={`px-3 py-1.5 text-xs rounded-lg btn-water text-white font-medium cursor-pointer ${uploading ? "opacity-50 pointer-events-none" : ""}`}>
            {uploading ? "Uploading..." : "+ Upload"}
            <input
              ref={fileRef}
              type="file"
              multiple
              accept=".pdf,.docx,.pptx,.csv,.txt,.md,.py,.js,.ts,.java,.c,.cpp"
              className="hidden"
              onChange={handleUpload}
            />
          </label>
        </div>
        {uploadError && <p className="text-xs text-red-500">{uploadError}</p>}
        <p className="text-xs text-[var(--text-muted)]">Supported: PDF, DOCX, PPTX, CSV, TXT, MD, code files · Select multiple files at once</p>

        {course.materials.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)] py-2">No materials yet. Upload a file to get started.</p>
        ) : (
          <ul className="space-y-2">
            {course.materials.map((m: Material) => (
              <li key={m.id}
                onClick={() => setActiveTab(m.id)}
                className={`flex items-center gap-3 p-3 rounded-lg border transition-colors cursor-pointer ${
                  activeTab === m.id
                    ? "border-[var(--accent)]/60 bg-[var(--accent)]/5"
                    : "border-[var(--border)] bg-[var(--bg-secondary)] hover:border-[var(--accent)]/30"
                }`}>
                <span className="text-lg shrink-0">
                  {m.file_type === "pdf" ? "📕" : m.file_type === "docx" ? "📝" : m.file_type === "pptx" ? "📊" : "📄"}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-[var(--text-primary)] truncate">{m.filename}</p>
                  <p className="text-xs text-[var(--text-muted)]">
                    {m.status === "processing" ? "⏳ Analyzing..." : m.status === "ready" ? (
                      `✅ ${(course.sections_by_material?.[m.id] ?? []).length} sections`
                    ) : m.status}
                  </p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); if (confirm("Delete this material?")) deleteMat.mutate(m.id); }}
                  className="text-xs text-[var(--text-muted)] hover:text-red-500 transition-colors px-2 py-1 shrink-0">
                  ✕
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      {/* Learning Map with per-material tabs */}
      {course.materials.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <h2 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <span>🗺️</span> Learning Map
            </h2>
            <div className="flex items-center gap-1 flex-wrap">
              <button
                onClick={() => setActiveTab(null)}
                className={`px-3 py-1.5 text-xs rounded-lg border transition-colors font-medium ${
                  activeTab === null
                    ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                    : "border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                }`}>
                All ({course.sections.length})
              </button>
              {course.materials.map((m: Material) => {
                const count = (course.sections_by_material?.[m.id] ?? []).length;
                const label = m.filename.replace(/\.[^/.]+$/, "").slice(0, 20);
                return (
                  <button key={m.id}
                    onClick={() => setActiveTab(m.id)}
                    className={`px-3 py-1.5 text-xs rounded-lg border transition-colors font-medium ${
                      activeTab === m.id
                        ? "border-[var(--accent)] bg-[var(--accent)]/10 text-[var(--accent)]"
                        : "border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                    }`}>
                    {label} ({count})
                  </button>
                );
              })}
            </div>
          </div>

          {activeSections.length === 0 ? (
            <div className="glass-card rounded-xl p-8 text-center">
              <p className="text-sm text-[var(--text-muted)]">
                {course.materials.some((m: Material) => m.status === "processing")
                  ? "⏳ Analyzing material... Sections will appear here shortly."
                  : "No sections yet. Upload a material to generate the learning map."}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {activeSections.map((s: Section, i: number) => (
                <div key={s.id} className="glass-card rounded-xl p-4">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-xs font-mono text-[var(--text-muted)] shrink-0">#{i + 1}</span>
                      <p className="font-medium text-sm text-[var(--text-primary)]">{s.title}</p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${DIFF_COLORS[s.difficulty] || ""} ${DIFF_BG[s.difficulty] || ""}`}>
                        {DIFF_LABELS[s.difficulty] || s.difficulty}
                      </span>
                      <Link
                        href={`/courses/${id}/teach?section=${s.id}&title=${encodeURIComponent(s.title)}`}
                        className="px-2.5 py-1 text-xs rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 font-medium transition-colors">
                        Study →
                      </Link>
                      <button
                        onClick={() => { if (confirm("Delete this section?")) deleteSec.mutate(s.id); }}
                        className="px-1.5 py-1 text-xs rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-red-500 hover:border-red-300 transition-colors">
                        ✕
                      </button>
                    </div>
                  </div>
                  {s.concepts.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {s.concepts.map((c: string) => (
                        <span key={c} className="text-xs px-2 py-0.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                  {s.prerequisites.length > 0 && (
                    <p className="text-xs text-[var(--text-muted)] mt-1.5">
                      Prereqs: {s.prerequisites.join(", ")}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
