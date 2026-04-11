"use client";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function HomePage() {
  const { isLoggedIn, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isLoggedIn) router.replace("/dashboard");
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
            AI Study Coach · SBU Students
          </div>

          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-[var(--text-primary)] mb-5 tracking-tight">
            Learn Deeper,{" "}
            <span className="text-[var(--accent)] relative">
              Not Just Faster
              <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-water-shallow via-water-current to-water-teal rounded-full opacity-70" />
            </span>
          </h1>

          <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto leading-relaxed">
            Upload your course materials and let StudyCoach guide you through
            concepts with Socratic questions — building real understanding, not just answers.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-16">
            <Link href="/login?tab=register"
              className="btn-water px-8 py-3 text-white rounded-xl font-semibold text-base">
              Get Started Free
            </Link>
            <Link href="/login"
              className="px-8 py-3 rounded-xl border border-[var(--border)] text-[var(--text-secondary)] hover:border-water-current/40 hover:text-[var(--accent)] transition-colors text-base font-medium">
              Sign In
            </Link>
          </div>

          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-2">
            {["📄 PDF & DOCX upload", "🗺️ AI learning maps", "📅 Smart study plans", "🧠 Socratic teaching", "📊 Difficulty tracking", "🎯 Concept mastery"].map((label) => (
              <span key={label}
                className="px-3 py-1.5 rounded-full text-xs bg-white/50 dark:bg-water-abyss/50 backdrop-blur-sm border border-water-shallow/50 text-[var(--text-secondary)]">
                {label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Wave divider */}
      <div className="wave-divider" />

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-16">
        <div className="text-center mb-12">
          <span className="inline-block text-xs font-semibold uppercase tracking-widest text-[var(--accent)] bg-[var(--accent)]/10 px-3 py-1 rounded-full mb-3">
            How it works
          </span>
          <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)]">
            From Upload to Understanding
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            { step: "01", icon: "📄", title: "Upload Materials", desc: "Add your syllabus, lecture slides, notes, or any course document. StudyCoach extracts a structured learning map automatically.", color: "from-sky-400/20 to-blue-500/10" },
            { step: "02", icon: "📅", title: "Plan Your Study", desc: "Get an AI-generated study plan based on your syllabus. Adjust deadlines, priorities, and completion status as you go.", color: "from-teal-400/20 to-cyan-500/10" },
            { step: "03", icon: "🧠", title: "Learn by Teaching", desc: "Ask StudyCoach anything. It won't give you the answer — it'll ask you questions that lead you to discover it yourself.", color: "from-[var(--accent)]/20 to-sky-500/10" },
          ].map((item) => (
            <div key={item.step} className={`glass-card rounded-2xl p-6 bg-gradient-to-br ${item.color} text-center`}>
              <div className="w-12 h-12 rounded-xl bg-white/60 dark:bg-water-abyss/60 flex items-center justify-center text-2xl mx-auto mb-4 shadow-sm">
                {item.icon}
              </div>
              <div className="text-xs font-bold text-[var(--accent)]/50 mb-2 tracking-widest">{item.step}</div>
              <h3 className="font-semibold text-[var(--text-primary)] mb-2">{item.title}</h3>
              <p className="text-sm text-[var(--text-muted)] leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats bar */}
      <section className="bg-gradient-to-r from-[var(--accent)]/5 via-sky-400/10 to-teal-400/5 border-y border-[var(--border)] py-10">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 grid grid-cols-3 gap-4 text-center">
          {[
            { value: "Socratic", label: "Teaching method" },
            { value: "PDF · DOCX · PPTX", label: "Supported formats" },
            { value: "SBU only", label: "Exclusive access" },
          ].map((s) => (
            <div key={s.label}>
              <p className="font-display font-bold text-lg text-[var(--accent)]">{s.value}</p>
              <p className="text-xs text-[var(--text-muted)] mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <section className="py-10 text-center">
        <p className="text-xs text-[var(--text-muted)]">
          Exclusively for <span className="font-medium text-[var(--accent)]">@stonybrook.edu</span> and{" "}
          <span className="font-medium text-[var(--accent)]">@alumni.stonybrook.edu</span> members
        </p>
      </section>
    </div>
  );
}
