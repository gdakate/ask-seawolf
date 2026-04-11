"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMyProfile, updateProfile, type Profile } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const DEGREES: Record<string,string> = { bs:"B.S.",ba:"B.A.",ms:"M.S.",ma:"M.A.",phd:"Ph.D.",mba:"MBA",other:"" };
const OPEN_TO_LABELS: Record<string,string> = {
  coffee_chat: "☕ Coffee Chat",
  mentoring: "🎓 Mentoring",
  referrals_career_advice: "💼 Referrals / Career Advice",
  research_project_collab: "🔬 Research / Projects",
  community_general_chat: "💬 Community Chat",
  events_networking: "🤝 Events & Networking",
};

export default function MyProfilePage() {
  const { isLoggedIn, loading, name } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<Partial<Profile>>({});

  const { data: profile, isLoading } = useQuery({
    queryKey: ["my-profile"],
    queryFn: getMyProfile,
    enabled: isLoggedIn,
  });

  useEffect(() => { if (!loading && !isLoggedIn) router.replace("/login"); }, [isLoggedIn, loading, router]);

  const mut = useMutation({
    mutationFn: () => updateProfile(form),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["my-profile"] }); setEditing(false); },
  });

  const startEdit = () => { setForm(profile || {}); setEditing(true); };
  const set = (k: keyof Profile, v: any) => setForm((f) => ({ ...f, [k]: v }));

  if (loading || !isLoggedIn || isLoading) return (
    <div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Loading...</div>
  );

  if (!profile) return (
    <div className="max-w-xl mx-auto px-4 py-16 text-center">
      <p className="text-[var(--text-muted)] mb-4">No profile yet.</p>
      <button onClick={() => router.push("/onboarding")} className="btn-water px-6 py-2.5 text-white rounded-xl font-semibold">
        Set Up Profile
      </button>
    </div>
  );

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">My Profile</h1>
        {!editing && (
          <button onClick={startEdit}
            className="px-4 py-2 rounded-xl border border-[var(--border)] text-sm text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors">
            Edit Profile
          </button>
        )}
      </div>

      {editing ? (
        <div className="glass-card rounded-2xl p-6 space-y-4">
          <h2 className="font-semibold text-[var(--text-primary)]">Edit Profile</h2>

          <div className="grid grid-cols-2 gap-4">
            {[["major","Major"],["job_title","Job Title"],["current_company","Company"],["industry","Industry"],["location","Location"],["linkedin_url","LinkedIn URL"]].map(([k,l]) => (
              <div key={k}>
                <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">{l}</label>
                <input value={(form as any)[k] || ""}
                  onChange={(e) => set(k as keyof Profile, e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60" />
              </div>
            ))}
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Bio</label>
            <textarea value={form.bio || ""} onChange={(e) => set("bio", e.target.value)} rows={3}
              className="w-full px-3 py-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none resize-none" />
          </div>

          <div>
            <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
              <input type="checkbox" checked={form.is_visible ?? true}
                onChange={(e) => set("is_visible", e.target.checked)}
                className="accent-[var(--accent)]" />
              Visible to other alumni
            </label>
          </div>

          <div className="flex gap-2">
            <button onClick={() => mut.mutate()} disabled={mut.isPending}
              className="px-5 py-2 btn-water text-white rounded-lg text-sm font-semibold disabled:opacity-50">
              {mut.isPending ? "Saving..." : "Save Changes"}
            </button>
            <button onClick={() => setEditing(false)}
              className="px-4 py-2 rounded-lg border border-[var(--border)] text-sm text-[var(--text-muted)]">
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Header card */}
          <div className="glass-card rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-16 h-16 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] font-bold text-2xl">
                {profile.name.charAt(0)}
              </div>
              <div>
                <h2 className="font-display text-xl font-semibold text-[var(--text-primary)]">{profile.name}</h2>
                <p className="text-sm text-[var(--text-muted)]">
                  {profile.job_title && profile.current_company
                    ? `${profile.job_title} @ ${profile.current_company}`
                    : profile.email}
                </p>
              </div>
            </div>
            {profile.bio && <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{profile.bio}</p>}
          </div>

          {/* Details */}
          <div className="glass-card rounded-2xl p-6">
            <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Academic & Career</h3>
            <dl className="space-y-2.5">
              {[
                ["Major", `${DEGREES[profile.degree] || profile.degree} ${profile.major}`],
                ["Graduated", `${profile.graduation_year}${profile.is_international ? " · International" : ""}`],
                ["Industry", profile.industry],
                ["Location", profile.location],
              ].filter(([,v]) => v).map(([k, v]) => (
                <div key={k as string} className="flex gap-3 text-sm">
                  <dt className="text-[var(--text-muted)] w-24 flex-shrink-0">{k}</dt>
                  <dd className="text-[var(--text-primary)]">{v}</dd>
                </div>
              ))}
              {profile.linkedin_url && (
                <div className="flex gap-3 text-sm">
                  <dt className="text-[var(--text-muted)] w-24 flex-shrink-0">LinkedIn</dt>
                  <dd><a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">View Profile ↗</a></dd>
                </div>
              )}
            </dl>
          </div>

          {/* Skills */}
          {profile.skills.length > 0 && (
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((s) => (
                  <span key={s} className="px-3 py-1 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] text-xs font-medium border border-[var(--accent)]/20">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Interests */}
          {profile.interests.length > 0 && (
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Interests</h3>
              <div className="flex flex-wrap gap-2">
                {profile.interests.map((s) => (
                  <span key={s} className="px-3 py-1 rounded-full bg-water-shallow/30 text-[var(--text-secondary)] text-xs border border-[var(--border)]">{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Open to */}
          {profile.open_to.length > 0 && (
            <div className="glass-card rounded-2xl p-6">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">Open To</h3>
              <div className="flex flex-wrap gap-2">
                {profile.open_to.map((k) => (
                  <span key={k} className="px-3 py-1.5 rounded-full border border-[var(--accent)]/30 text-[var(--accent)] text-xs font-medium">
                    {OPEN_TO_LABELS[k] || k}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
