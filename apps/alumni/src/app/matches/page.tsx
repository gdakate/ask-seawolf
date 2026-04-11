"use client";
import { useQuery } from "@tanstack/react-query";
import { getMatches, type Match } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";

const DEGREE_LABEL: Record<string, string> = {
  bs:"B.S.", ba:"B.A.", ms:"M.S.", ma:"M.A.", phd:"Ph.D.", mba:"MBA", other:""
};

function MatchCard({ match }: { match: Match }) {
  const { profile, match_score, reasons } = match;
  const scoreColor = match_score >= 70 ? "text-green-600" : match_score >= 50 ? "text-yellow-600" : "text-[var(--text-muted)]";
  const scoreRing  = match_score >= 70 ? "border-green-300" : match_score >= 50 ? "border-yellow-300" : "border-[var(--border)]";

  return (
    <div className="glass-card rounded-2xl p-5 flex flex-col gap-4 hover:shadow-[0_4px_24px_rgba(14,165,233,0.12)] transition-all duration-300">
      {/* Top: avatar + name + match % */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-[var(--accent)]/20 flex items-center justify-center text-[var(--accent)] font-bold text-lg flex-shrink-0">
            {profile.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-[var(--text-primary)] text-sm leading-tight">{profile.name}</p>
            <p className="text-xs text-[var(--text-muted)]">
              {profile.job_title && profile.current_company
                ? `${profile.job_title} @ ${profile.current_company}`
                : profile.job_title || profile.current_company || "Alumni"}
            </p>
          </div>
        </div>
        {/* Match score ring */}
        <div className={`flex-shrink-0 w-12 h-12 rounded-full border-2 ${scoreRing} flex flex-col items-center justify-center`}>
          <span className={`text-sm font-bold leading-none ${scoreColor}`}>{match_score}</span>
          <span className="text-[9px] text-[var(--text-muted)] leading-none">%</span>
        </div>
      </div>

      {/* Info row */}
      <div className="flex flex-wrap gap-1.5 text-[10px]">
        <span className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)]">
          {DEGREE_LABEL[profile.degree] || profile.degree} {profile.major}
        </span>
        <span className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)]">
          '{String(profile.graduation_year).slice(-2)}
        </span>
        {profile.location && (
          <span className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)]">
            📍 {profile.location}
          </span>
        )}
        {profile.industry && (
          <span className="px-2 py-0.5 rounded-full bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-secondary)]">
            {profile.industry}
          </span>
        )}
      </div>

      {/* Match reasons */}
      {reasons.length > 0 && (
        <div className="space-y-1">
          {reasons.map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-[var(--text-secondary)]">
              <span className="text-[var(--accent)] mt-0.5 flex-shrink-0">✓</span>
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      {/* Skills preview */}
      {profile.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {profile.skills.slice(0, 4).map((s) => (
            <span key={s} className="px-2 py-0.5 rounded-full bg-[var(--accent)]/8 text-[var(--accent)] text-[10px] font-medium border border-[var(--accent)]/20">
              {s}
            </span>
          ))}
          {profile.skills.length > 4 && (
            <span className="px-2 py-0.5 rounded-full text-[var(--text-muted)] text-[10px]">
              +{profile.skills.length - 4} more
            </span>
          )}
        </div>
      )}

      {/* CTA */}
      <div className="flex gap-2 pt-1">
        <Link href={`/profile/${profile.id}`}
          className="flex-1 py-2 text-center rounded-lg border border-[var(--border)] text-xs font-medium text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors">
          View Profile
        </Link>
        {profile.linkedin_url && (
          <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer"
            className="flex-1 py-2 text-center btn-water text-white rounded-lg text-xs font-medium">
            LinkedIn ↗
          </a>
        )}
        {profile.email && !profile.linkedin_url && (
          <a href={`mailto:${profile.email}`}
            className="flex-1 py-2 text-center btn-water text-white rounded-lg text-xs font-medium">
            Email ↗
          </a>
        )}
      </div>
    </div>
  );
}

export default function MatchesPage() {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const { data: matches, isLoading, error } = useQuery({
    queryKey: ["matches"],
    queryFn: getMatches,
    enabled: isLoggedIn,
  });

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  if (loading || (!isLoggedIn && !loading)) return null;

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10">
      <div className="mb-8">
        <h1 className="font-display text-3xl font-bold text-[var(--text-primary)] mb-2">Your Matches</h1>
        <p className="text-[var(--text-muted)] text-sm">
          AI-powered alumni recommendations based on your major, career path, skills, and interests.
        </p>
      </div>

      {isLoading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="glass-card rounded-2xl p-5 animate-pulse h-64 bg-[var(--bg-secondary)]" />
          ))}
        </div>
      )}

      {error && (error as any).message?.includes("Complete your profile") && (
        <div className="glass-card rounded-2xl p-10 text-center">
          <div className="text-4xl mb-4">👋</div>
          <h2 className="font-display text-xl font-semibold text-[var(--text-primary)] mb-2">
            Set up your profile first
          </h2>
          <p className="text-[var(--text-muted)] text-sm mb-6">
            Tell us about your background so we can find the best alumni matches for you.
          </p>
          <Link href="/onboarding"
            className="inline-block px-8 py-3 btn-water text-white rounded-xl font-semibold">
            Build My Profile →
          </Link>
        </div>
      )}

      {matches && matches.length === 0 && (
        <div className="glass-card rounded-2xl p-10 text-center">
          <div className="text-4xl mb-4">🔍</div>
          <p className="text-[var(--text-muted)]">No matches yet — more alumni needed.</p>
        </div>
      )}

      {matches && matches.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {matches.map((m) => <MatchCard key={m.profile.id} match={m} />)}
          </div>
          <p className="mt-6 text-xs text-center text-[var(--text-muted)]">
            Matches ranked by 2-stage embedding similarity + multi-signal reranking with MMR diversity
          </p>
        </>
      )}
    </div>
  );
}
