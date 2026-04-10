"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const TOPICS = [
  { key: "admissions",     name: "Admissions",      desc: "Applications, deadlines & requirements", icon: "🎓" },
  { key: "bursar",         name: "Tuition & Billing",desc: "Costs, payments & refunds",              icon: "💰" },
  { key: "financial_aid",  name: "Financial Aid",    desc: "Scholarships, grants & loans",           icon: "📋" },
  { key: "housing",        name: "Housing",          desc: "Dorms, apartments & residential life",   icon: "🏠" },
  { key: "registrar",      name: "Registrar",        desc: "Registration, transcripts & records",    icon: "📄" },
  { key: "dining",         name: "Dining",           desc: "Meal plans & dining locations",          icon: "🍽️" },
  { key: "academics",      name: "Academics",        desc: "Programs, policies & resources",         icon: "📚" },
  { key: "student_affairs",name: "Student Life",     desc: "Clubs, activities & services",           icon: "👥" },
];

const SAMPLE_QUESTIONS = [
  "What is the application deadline for fall admission?",
  "How much is tuition for NY residents?",
  "What meal plans are available?",
  "How do I apply for financial aid?",
];

// Bubbles: [size, left%, delay, duration]
const BUBBLES: [number, number, number, number][] = [
  [10, 8,  0,   4.2],
  [6,  18, 1.1, 5.8],
  [14, 32, 0.5, 6.5],
  [8,  55, 1.8, 4.8],
  [5,  70, 0.2, 7.1],
  [12, 82, 1.3, 5.3],
  [7,  91, 0.7, 6.0],
];

export default function HomePage() {
  const [query, setQuery] = useState("");
  const router = useRouter();
  const { isLoggedIn, loading } = useAuth();

  const handleAsk = (q?: string) => {
    const question = q || query;
    if (!question.trim()) return;
    if (!isLoggedIn && !loading) {
      router.push(`/login?redirect=${encodeURIComponent(`/chat?q=${encodeURIComponent(question.trim())}`)}`);
      return;
    }
    router.push(`/chat?q=${encodeURIComponent(question.trim())}`);
  };

  return (
    <div>
      {/* ── Hero ───────────────────────────────────────────── */}
      <section className="hero-bg relative overflow-hidden">

        {/* Floating bubbles */}
        {BUBBLES.map(([size, left, delay, dur], i) => (
          <span
            key={i}
            className="bubble"
            style={{
              width: size,
              height: size,
              left: `${left}%`,
              bottom: "12%",
              "--dur":   `${dur}s`,
              "--delay": `${delay}s`,
            } as React.CSSProperties}
          />
        ))}

        {/* Radial light source — like sunlight from above the water */}
        <div className="absolute inset-0 pointer-events-none"
          style={{
            background: "radial-gradient(ellipse 70% 50% at 50% -10%, rgba(255,255,255,0.45) 0%, transparent 70%)",
          }}
        />

        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 pt-16 pb-24 text-center">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/60 dark:bg-water-abyss/60 backdrop-blur-sm border border-water-shallow/60 text-[var(--accent)] text-xs font-semibold mb-6 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-water-current animate-pulse" />
            Powered by Official SBU Sources
          </div>

          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-[var(--text-primary)] mb-5 tracking-tight text-balance">
            Your Guide to{" "}
            <span className="text-[var(--accent)] relative">
              Stony Brook
              {/* underline shimmer */}
              <span className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-water-shallow via-water-current to-water-teal rounded-full opacity-70" />
            </span>
          </h1>

          <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto leading-relaxed">
            Get instant, cited answers about admissions, tuition, housing,
            financial aid, and more — all from official university sources.
          </p>

          {/* Search box */}
          <div className="max-w-2xl mx-auto">
            <div className="glass-card flex items-center rounded-2xl overflow-hidden transition-all focus-within:water-glow">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleAsk()}
                placeholder="Ask anything about Stony Brook University..."
                className="flex-1 px-5 py-4 text-base bg-transparent outline-none text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
              />
              <button
                onClick={() => handleAsk()}
                disabled={!query.trim()}
                className="btn-water m-2 px-6 py-2.5 text-white rounded-xl font-semibold text-sm disabled:opacity-40"
              >
                Ask
              </button>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleAsk(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/50 dark:bg-water-abyss/50 backdrop-blur-sm border border-water-shallow/50 text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-water-current/60 hover:bg-white/70 dark:hover:bg-water-abyss/70 transition-all"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Wave transition to next section */}
        <div className="absolute bottom-0 left-0 right-0 h-8 pointer-events-none"
          style={{
            background: "linear-gradient(to bottom, transparent, var(--bg-primary))",
          }}
        />
      </section>

      {/* ── Topics grid ───────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16">
        <div className="text-center mb-10">
          <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] mb-2">
            Browse by Topic
          </h2>
          <p className="text-sm text-[var(--text-muted)]">Dive into any area of university life</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {TOPICS.map((topic) => (
            <Link
              key={topic.key}
              href={`/chat?q=Tell me about ${topic.name.toLowerCase()} at Stony Brook`}
              className="group glass-card p-5 rounded-xl hover:border-water-current/50 hover:shadow-[0_4px_24px_rgba(14,165,233,0.12)] transition-all duration-300"
            >
              <div className="text-2xl mb-3 group-hover:scale-110 transition-transform duration-200 inline-block">
                {topic.icon}
              </div>
              <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-[var(--accent)] transition-colors mb-1">
                {topic.name}
              </h3>
              <p className="text-sm text-[var(--text-muted)]">{topic.desc}</p>

              {/* Arrow that appears on hover */}
              <div className="mt-3 text-[var(--accent)] opacity-0 group-hover:opacity-100 transition-opacity text-xs font-medium">
                Explore →
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Trust section — "seafloor" aesthetic ─────────── */}
      <section
        className="border-t border-[var(--border)]"
        style={{ background: "linear-gradient(to bottom, var(--bg-secondary), var(--bg-primary))" }}
      >
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] mb-4">
            Grounded in Official Sources
          </h2>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto leading-relaxed mb-10">
            Every answer includes citations from official Stony Brook University
            web pages. Click through to read the original source and verify
            the information yourself.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[var(--text-secondary)]">
            {[
              "Source citations on every answer",
              "Direct links to official pages",
              "Office routing when you need human help",
            ].map((item) => (
              <div key={item} className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-water-current shadow-[0_0_6px_rgba(14,165,233,0.6)]" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
