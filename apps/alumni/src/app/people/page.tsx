"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getMatches, getConnections, getConnectionIds, toggleConnect, type Match, type Profile } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import Link from "next/link";

const DEGREE_LABEL: Record<string, string> = {
  bs:"B.S.", ba:"B.A.", ms:"M.S.", ma:"M.A.", phd:"Ph.D.", mba:"MBA", other:""
};

function ConnectButton({ targetUserId, initialConnected }: { targetUserId: string; initialConnected: boolean }) {
  const qc = useQueryClient();
  const [connected, setConnected] = useState(initialConnected);
  const mut = useMutation({
    mutationFn: () => toggleConnect(targetUserId),
    onSuccess: (data) => {
      setConnected(data.connected);
      qc.invalidateQueries({ queryKey: ["connections"] });
      qc.invalidateQueries({ queryKey: ["connection-ids"] });
      qc.invalidateQueries({ queryKey: ["matches"] });
    },
  });

  return (
    <button
      onClick={() => mut.mutate()}
      disabled={mut.isPending}
      className={`flex-1 py-2 text-center rounded-lg text-xs font-semibold transition-all disabled:opacity-50 ${
        connected
          ? "bg-[var(--accent)]/10 border border-[var(--accent)]/40 text-[var(--accent)]"
          : "btn-water text-white"
      }`}
    >
      {mut.isPending ? "..." : connected ? "✓ Connected" : "+ Connect"}
    </button>
  );
}

function DiscoverCard({ match, connectedIds }: { match: Match; connectedIds: Set<string> }) {
  const { profile, match_score, reasons } = match;
  const scoreColor = match_score >= 70 ? "text-emerald-500" : match_score >= 50 ? "text-amber-500" : "text-[var(--text-muted)]";
  const scoreRing  = match_score >= 70 ? "border-emerald-300" : match_score >= 50 ? "border-amber-300" : "border-[var(--border)]";

  return (
    <div className="glass-card rounded-2xl p-5 flex flex-col gap-3 hover:shadow-[0_4px_24px_rgba(14,165,233,0.10)] transition-all duration-200">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-full bg-[var(--accent)]/15 flex items-center justify-center text-[var(--accent)] font-bold text-lg flex-shrink-0">
            {profile.name.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-[var(--text-primary)] text-sm">{profile.name}</p>
            <p className="text-xs text-[var(--text-muted)]">
              {profile.job_title && profile.current_company
                ? `${profile.job_title} @ ${profile.current_company}`
                : profile.job_title || profile.current_company || "Alumni"}
            </p>
          </div>
        </div>
        <div className={`flex-shrink-0 w-11 h-11 rounded-full border-2 ${scoreRing} flex flex-col items-center justify-center`}>
          <span className={`text-sm font-bold leading-none ${scoreColor}`}>{match_score}</span>
          <span className="text-[9px] text-[var(--text-muted)]">%</span>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 text-[10px]">
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
      </div>

      {/* Match reasons */}
      {reasons.length > 0 && (
        <div className="space-y-0.5">
          {reasons.slice(0, 2).map((r, i) => (
            <div key={i} className="flex items-start gap-1.5 text-xs text-[var(--text-secondary)]">
              <span className="text-[var(--accent)] flex-shrink-0 mt-0.5">✓</span>
              <span>{r}</span>
            </div>
          ))}
        </div>
      )}

      {/* Skills */}
      {profile.skills.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {profile.skills.slice(0, 3).map((s) => (
            <span key={s} className="px-2 py-0.5 rounded-full bg-[var(--accent)]/8 text-[var(--accent)] text-[10px] font-medium border border-[var(--accent)]/20">{s}</span>
          ))}
          {profile.skills.length > 3 && (
            <span className="text-[10px] text-[var(--text-muted)] px-1">+{profile.skills.length - 3}</span>
          )}
        </div>
      )}

      {/* CTA */}
      <div className="flex gap-2 pt-1">
        <Link href={`/profile/${profile.id}`}
          className="flex-1 py-2 text-center rounded-lg border border-[var(--border)] text-xs font-medium text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors">
          View Profile
        </Link>
        <ConnectButton targetUserId={profile.user_id} initialConnected={connectedIds.has(profile.user_id)} />
        {profile.linkedin_url && (
          <a href={profile.linkedin_url} target="_blank" rel="noopener noreferrer"
            className="px-3 py-2 rounded-lg border border-[var(--border)] text-xs text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors">
            in
          </a>
        )}
      </div>
    </div>
  );
}

function ConnectionCard({ profile, connectedIds }: { profile: Profile; connectedIds: Set<string> }) {
  return (
    <div className="glass-card rounded-2xl p-4 flex items-center gap-4">
      <div className="w-12 h-12 rounded-full bg-[var(--accent)]/15 flex items-center justify-center text-[var(--accent)] font-bold text-xl flex-shrink-0">
        {profile.name.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-[var(--text-primary)] text-sm">{profile.name}</p>
        <p className="text-xs text-[var(--text-muted)] truncate">
          {profile.job_title && profile.current_company
            ? `${profile.job_title} @ ${profile.current_company}`
            : `${DEGREE_LABEL[profile.degree] || profile.degree} ${profile.major} '${String(profile.graduation_year).slice(-2)}`}
        </p>
        {profile.location && <p className="text-[10px] text-[var(--text-muted)]">📍 {profile.location}</p>}
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <Link href={`/profile/${profile.id}`}
          className="px-3 py-1.5 rounded-lg border border-[var(--border)] text-xs text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors">
          View
        </Link>
        <ConnectButton targetUserId={profile.user_id} initialConnected={connectedIds.has(profile.user_id)} />
      </div>
    </div>
  );
}

export default function PeoplePage() {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState<"discover" | "connected">("discover");

  const { data: matches, isLoading: loadingMatches, error } = useQuery({
    queryKey: ["matches"],
    queryFn: getMatches,
    enabled: isLoggedIn,
  });

  const { data: connections, isLoading: loadingConn } = useQuery({
    queryKey: ["connections"],
    queryFn: getConnections,
    enabled: isLoggedIn && tab === "connected",
  });

  const { data: connIdsData } = useQuery({
    queryKey: ["connection-ids"],
    queryFn: getConnectionIds,
    enabled: isLoggedIn,
  });

  useEffect(() => {
    if (!loading && !isLoggedIn) router.replace("/login");
  }, [isLoggedIn, loading, router]);

  if (loading || (!isLoggedIn && !loading)) return null;

  const connectedIds = new Set(connIdsData?.ids ?? []);

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="font-display text-2xl font-bold text-[var(--text-primary)]">People</h1>
        <p className="text-sm text-[var(--text-muted)] mt-0.5">AI-matched Seawolves based on your profile</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 p-1 bg-[var(--bg-secondary)] rounded-xl w-fit">
        {(["discover", "connected"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
              tab === t
                ? "bg-[var(--bg-primary)] text-[var(--text-primary)] shadow-sm"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            }`}>
            {t === "discover" ? "Discover" : `Connected${connectedIds.size > 0 ? ` (${connectedIds.size})` : ""}`}
          </button>
        ))}
      </div>

      {/* Discover tab */}
      {tab === "discover" && (
        <>
          {loadingMatches && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="glass-card rounded-2xl h-52 animate-pulse bg-[var(--bg-secondary)]" />
              ))}
            </div>
          )}

          {error && (error as any).message?.includes("Complete your profile") && (
            <div className="glass-card rounded-2xl p-10 text-center">
              <div className="text-4xl mb-4">👋</div>
              <h2 className="font-display text-xl font-semibold text-[var(--text-primary)] mb-2">
                Complete your profile first
              </h2>
              <p className="text-[var(--text-muted)] text-sm mb-6">
                Tell us about your background so we can find the best Seawolves for you.
              </p>
              <Link href="/onboarding"
                className="inline-block px-8 py-3 btn-water text-white rounded-xl font-semibold">
                Build My Profile →
              </Link>
            </div>
          )}

          {matches?.length === 0 && (
            <div className="glass-card rounded-2xl p-10 text-center">
              <div className="text-4xl mb-3">🔍</div>
              <p className="text-[var(--text-muted)] text-sm">No matches yet — more alumni needed.</p>
            </div>
          )}

          {matches && matches.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {matches.filter((m) => !connectedIds.has(m.profile.user_id)).map((m) => (
                  <DiscoverCard key={m.profile.id} match={m} connectedIds={connectedIds} />
                ))}
              </div>
              <p className="mt-5 text-xs text-center text-[var(--text-muted)]">
                Ranked by profile similarity · skills · career path · MMR diversity
              </p>
            </>
          )}
        </>
      )}

      {/* Connected tab */}
      {tab === "connected" && (
        <>
          {loadingConn && (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="glass-card rounded-2xl h-20 animate-pulse bg-[var(--bg-secondary)]" />
              ))}
            </div>
          )}

          {!loadingConn && (!connections || connections.length === 0) && (
            <div className="glass-card rounded-2xl p-10 text-center">
              <div className="text-4xl mb-3">🤝</div>
              <p className="text-[var(--text-muted)] text-sm">No connections yet.</p>
              <button onClick={() => setTab("discover")}
                className="mt-4 text-sm text-[var(--accent)] hover:underline">
                Discover people →
              </button>
            </div>
          )}

          {connections && connections.length > 0 && (
            <div className="space-y-3">
              {connections.map((p) => (
                <ConnectionCard key={p.id} profile={p} connectedIds={connectedIds} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
