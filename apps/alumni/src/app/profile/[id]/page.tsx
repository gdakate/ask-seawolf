"use client";
import { useQuery } from "@tanstack/react-query";
import { getProfile } from "@/lib/api";
import { use } from "react";
import Link from "next/link";

const DEGREES: Record<string,string> = { bs:"B.S.",ba:"B.A.",ms:"M.S.",ma:"M.A.",phd:"Ph.D.",mba:"MBA",other:"" };
const OPEN_TO_LABELS: Record<string,string> = {
  coffee_chat: "☕ Coffee Chat", mentoring: "🎓 Mentoring",
  referrals_career_advice: "💼 Referrals / Career Advice",
  research_project_collab: "🔬 Research / Projects",
  community_general_chat: "💬 Community Chat",
  events_networking: "🤝 Events & Networking",
};

export default function ProfilePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: profile, isLoading } = useQuery({ queryKey: ["profile", id], queryFn: () => getProfile(id) });

  if (isLoading) return <div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Loading...</div>;
  if (!profile) return <div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Profile not found</div>;

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10">
      <Link href="/matches" className="text-sm text-[var(--text-muted)] hover:text-[var(--accent)] mb-6 inline-block">
        ← Back to matches
      </Link>

      <div className="space-y-4">
        {/* Header */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-4 mb-4">
            <div className="w-16 h-16 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] font-bold text-2xl">
              {profile.name.charAt(0)}
            </div>
            <div className="flex-1">
              <h1 className="font-display text-xl font-semibold text-[var(--text-primary)]">{profile.name}</h1>
              <p className="text-sm text-[var(--text-muted)]">
                {profile.job_title && profile.current_company
                  ? `${profile.job_title} @ ${profile.current_company}`
                  : `${DEGREES[profile.degree] || ""} ${profile.major} '${String(profile.graduation_year).slice(-2)}`}
              </p>
            </div>
          </div>
          {profile.bio && <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-4">{profile.bio}</p>}

          {/* CTA */}
          <div className="flex gap-2">
            {profile.linkedin_url && (
              <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer"
                className="flex-1 py-2.5 text-center btn-water text-white rounded-xl text-sm font-semibold">
                Connect on LinkedIn ↗
              </a>
            )}
            {profile.email && (
              <a href={`mailto:${profile.email}`}
                className="flex-1 py-2.5 text-center rounded-xl border border-[var(--border)] text-sm font-medium text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors">
                Send Email ✉️
              </a>
            )}
          </div>
        </div>

        {/* Academic & Career */}
        <div className="glass-card rounded-2xl p-6">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">Background</h3>
          <dl className="space-y-2.5">
            {[
              ["Major", `${DEGREES[profile.degree] || profile.degree} ${profile.major}`],
              ["Graduated", `${profile.graduation_year}${profile.is_international ? " · International" : ""}`],
              ["Industry", profile.industry], ["Location", profile.location],
            ].filter(([,v]) => v).map(([k, v]) => (
              <div key={k as string} className="flex gap-3 text-sm">
                <dt className="text-[var(--text-muted)] w-24 flex-shrink-0">{k}</dt>
                <dd className="text-[var(--text-primary)]">{v}</dd>
              </div>
            ))}
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
    </div>
  );
}
