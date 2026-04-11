"use client";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

const OPEN_TO_LABELS: Record<string, string> = {
  coffee_chat: "☕ Coffee Chat",
  mentoring: "🎓 Mentoring",
  referrals_career_advice: "💼 Referrals & Career Advice",
  research_project_collab: "🔬 Research & Projects",
  community_general_chat: "💬 Community Chat",
  events_networking: "🤝 Events & Networking",
};

export default function HomePage() {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isLoggedIn) router.replace("/matches");
  }, [isLoggedIn, loading, router]);

  return (
    <div>
      {/* Hero */}
      <section className="hero-bg relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 70% 50% at 50% -10%, rgba(255,255,255,0.45) 0%, transparent 70%)" }} />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 pt-16 pb-24 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/60 dark:bg-water-abyss/60 backdrop-blur-sm border border-water-shallow/60 text-[var(--accent)] text-xs font-semibold mb-6 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-water-current animate-pulse" />
            SBU Alumni Network · {new Date().getFullYear()}
          </div>

          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-[var(--text-primary)] mb-5 tracking-tight">
            Find Your{" "}
            <span className="text-[var(--accent)] relative">
              Seawolf Network
              <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-water-shallow via-water-current to-water-teal rounded-full opacity-70" />
            </span>
          </h1>

          <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto leading-relaxed">
            AI-powered alumni matching for Stony Brook graduates.
            Find mentors, collaborators, and friends who share your path.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16">
            <Link href="/login?tab=register"
              className="btn-water px-8 py-3 text-white rounded-xl font-semibold text-base">
              Join the Network
            </Link>
            <Link href="/login"
              className="px-8 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors text-base font-medium">
              Sign In
            </Link>
          </div>

          {/* Open-to pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {Object.values(OPEN_TO_LABELS).map((label) => (
              <span key={label}
                className="px-3 py-1.5 rounded-full text-xs bg-white/50 dark:bg-water-abyss/50 backdrop-blur-sm border border-water-shallow/50 text-[var(--text-secondary)]">
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-20">
        <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] text-center mb-12">
          How It Works
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
          {[
            { step: "01", title: "Build Your Profile", desc: "Add your major, career, skills, and what you're open to. Upload your resume for auto-fill." },
            { step: "02", title: "Get Matched", desc: "Our 2-stage AI finds the most compatible alumni using embedding similarity + multi-signal reranking." },
            { step: "03", title: "Connect & Grow", desc: "Reach out for coffee chats, mentoring, collaborations, or just to connect with fellow Seawolves." },
          ].map((item) => (
            <div key={item.step} className="glass-card rounded-xl p-6 text-center">
              <div className="text-3xl font-display font-bold text-[var(--accent)]/30 mb-3">{item.step}</div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-2">{item.title}</h3>
              <p className="text-sm text-[var(--text-muted)] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer trust */}
      <section className="border-t border-[var(--border)] py-10 text-center">
        <p className="text-xs text-[var(--text-muted)]">
          Exclusively for <span className="font-medium text-[var(--accent)]">@stonybrook.edu</span> and{" "}
          <span className="font-medium text-[var(--accent)]">@alumni.stonybrook.edu</span> members
        </p>
      </section>
    </div>
  );
}
