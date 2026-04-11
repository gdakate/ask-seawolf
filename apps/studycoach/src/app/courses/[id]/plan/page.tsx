"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { getCourse, getPlan, addPlanItem, updatePlanItem, deletePlanItem, generatePlan } from "@/lib/api";
import type { PlanItem } from "@/lib/api";

const ITEM_TYPES = ["study", "review", "practice", "exam", "assignment", "other"];
const TYPE_ICON: Record<string, string> = {
  study: "📖", review: "🔁", practice: "✏️", exam: "🎯", assignment: "📋", other: "📌",
};

export default function PlanPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [itemType, setItemType] = useState("study");
  const [notes, setNotes] = useState("");

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  const { data: course } = useQuery({
    queryKey: ["course", id],
    queryFn: () => getCourse(id),
    enabled: isLoggedIn,
  });

  const { data: plan = [], isLoading } = useQuery({
    queryKey: ["plan", id],
    queryFn: () => getPlan(id),
    enabled: isLoggedIn,
  });

  const addMut = useMutation({
    mutationFn: (data: Partial<PlanItem>) => addPlanItem(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["plan", id] });
      setShowForm(false); setTitle(""); setDueDate(""); setNotes("");
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ itemId, data }: { itemId: string; data: Partial<PlanItem> }) => updatePlanItem(itemId, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", id] }),
  });

  const deleteMut = useMutation({
    mutationFn: deletePlanItem,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", id] }),
  });

  const generateMut = useMutation({
    mutationFn: () => generatePlan(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["plan", id] }),
  });

  if (loading || !isLoggedIn) return null;

  const incomplete = plan.filter((i: PlanItem) => !i.is_completed);
  const completed = plan.filter((i: PlanItem) => i.is_completed);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <button onClick={() => router.back()} className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">← Back</button>
          <span className="text-[var(--text-muted)]">/</span>
          <Link href={`/courses/${id}`} className="text-xs text-[var(--text-muted)] hover:text-[var(--accent)]">{course?.code ?? "..."}</Link>
          <span className="text-[var(--text-muted)]">/</span>
          <span className="text-xs text-[var(--text-muted)]">Plan</span>
        </div>
        <div className="flex items-center justify-between gap-4">
          <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">Study Plan</h1>
          <div className="flex gap-2">
            <button onClick={() => generateMut.mutate()} disabled={generateMut.isPending}
              className="px-3 py-2 text-sm rounded-lg border border-[var(--border)] text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/40 transition-colors font-medium disabled:opacity-50">
              {generateMut.isPending ? "Generating..." : "✨ Generate"}
            </button>
            <button onClick={() => setShowForm(true)}
              className="px-3 py-2 text-sm btn-water text-white rounded-lg font-medium">
              + Add Item
            </button>
          </div>
        </div>
        {generateMut.isPending && (
          <p className="text-xs text-[var(--text-muted)] mt-1">AI is reading your materials and building a plan...</p>
        )}
      </div>

      {/* Add form */}
      {showForm && (
        <div className="glass-card rounded-xl p-5 space-y-4">
          <h2 className="font-semibold text-[var(--text-primary)]">Add Plan Item</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Title</label>
              <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Study chapter 3..."
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Type</label>
              <select value={itemType} onChange={(e) => setItemType(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60">
                {ITEM_TYPES.map((t) => <option key={t} value={t}>{TYPE_ICON[t]} {t}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Due Date <span className="font-normal text-[var(--text-muted)]">(optional)</span></label>
              <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Notes <span className="font-normal text-[var(--text-muted)]">(optional)</span></label>
              <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Additional notes..."
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={() => {
              if (!title.trim()) return;
              addMut.mutate({ title: title.trim(), item_type: itemType, due_date: dueDate || undefined, notes: notes || undefined });
            }} disabled={addMut.isPending || !title.trim()}
              className="px-4 py-2 btn-water text-white rounded-lg text-sm font-medium disabled:opacity-50">
              {addMut.isPending ? "Adding..." : "Add"}
            </button>
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] text-sm">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Plan items */}
      {isLoading ? (
        <div className="h-32 flex items-center justify-center text-[var(--text-muted)] text-sm">Loading...</div>
      ) : plan.length === 0 ? (
        <div className="glass-card rounded-xl p-12 text-center">
          <p className="text-4xl mb-4">📅</p>
          <p className="text-[var(--text-muted)] text-sm mb-4">No plan items yet.</p>
          <p className="text-xs text-[var(--text-muted)]">
            Use <strong>Generate</strong> to auto-create a plan from your materials, or add items manually.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {incomplete.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-sm font-semibold text-[var(--text-secondary)]">
                Upcoming <span className="font-normal text-[var(--text-muted)]">({incomplete.length})</span>
              </h2>
              {incomplete.map((item: PlanItem) => (
                <PlanItemRow key={item.id} item={item}
                  onToggle={() => updateMut.mutate({ itemId: item.id, data: { is_completed: true } })}
                  onDelete={() => deleteMut.mutate(item.id)} />
              ))}
            </section>
          )}
          {completed.length > 0 && (
            <section className="space-y-2">
              <h2 className="text-sm font-semibold text-[var(--text-secondary)]">
                Completed <span className="font-normal text-[var(--text-muted)]">({completed.length})</span>
              </h2>
              {completed.map((item: PlanItem) => (
                <PlanItemRow key={item.id} item={item}
                  onToggle={() => updateMut.mutate({ itemId: item.id, data: { is_completed: false } })}
                  onDelete={() => deleteMut.mutate(item.id)} />
              ))}
            </section>
          )}
        </div>
      )}
    </div>
  );
}

function PlanItemRow({ item, onToggle, onDelete }: { item: PlanItem; onToggle: () => void; onDelete: () => void }) {
  return (
    <div className={`glass-card rounded-xl p-4 flex items-center gap-3 ${item.is_completed ? "opacity-60" : ""}`}>
      <button onClick={onToggle}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center shrink-0 transition-colors ${
          item.is_completed ? "bg-[var(--accent)] border-[var(--accent)]" : "border-[var(--border)] hover:border-[var(--accent)]/60"
        }`}>
        {item.is_completed && <span className="text-white text-xs">✓</span>}
      </button>
      <span className="text-base shrink-0">{TYPE_ICON[item.item_type] ?? "📌"}</span>
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-medium text-[var(--text-primary)] ${item.is_completed ? "line-through" : ""}`}>{item.title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          {item.due_date && (
            <span className="text-xs text-[var(--text-muted)]">📅 {item.due_date.split("T")[0]}</span>
          )}
          {item.notes && (
            <span className="text-xs text-[var(--text-muted)] truncate">{item.notes}</span>
          )}
        </div>
      </div>
      <button onClick={() => { if (confirm("Delete?")) onDelete(); }}
        className="text-xs text-[var(--text-muted)] hover:text-red-500 transition-colors px-2 py-1 shrink-0">
        ✕
      </button>
    </div>
  );
}
