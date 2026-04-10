"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";

const TOPICS = [
  { key: "admissions", name: "Admissions", desc: "Applications, deadlines & requirements", icon: "🎓" },
  { key: "bursar", name: "Tuition & Billing", desc: "Costs, payments & refunds", icon: "💰" },
  { key: "financial_aid", name: "Financial Aid", desc: "Scholarships, grants & loans", icon: "📋" },
  { key: "housing", name: "Housing", desc: "Dorms, apartments & residential life", icon: "🏠" },
  { key: "registrar", name: "Registrar", desc: "Registration, transcripts & records", icon: "📄" },
  { key: "dining", name: "Dining", desc: "Meal plans & dining locations", icon: "🍽️" },
  { key: "academics", name: "Academics", desc: "Programs, policies & resources", icon: "📚" },
  { key: "student_affairs", name: "Student Life", desc: "Clubs, activities & services", icon: "👥" },
];

const SAMPLE_QUESTIONS = [
  "What is the application deadline for fall admission?",
  "How much is tuition for NY residents?",
  "What meal plans are available?",
  "How do I apply for financial aid?",
];

export default function HomePage() {
  const [query, setQuery] = useState("");
  const router = useRouter();

  const handleAsk = (q?: string) => {
    const question = q || query;
    if (question.trim()) {
      router.push(`/chat?q=${encodeURIComponent(question.trim())}`);
    }
  };

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-sbu-red/5 via-transparent to-sbu-red/3" />
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 pt-16 pb-20 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sbu-red/10 text-sbu-red text-xs font-semibold mb-6 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-sbu-red animate-pulse" />
            Powered by Official SBU Sources
          </div>

          <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-[var(--text-primary)] mb-5 tracking-tight text-balance">
            Your Guide to{" "}
            <span className="text-sbu-red">Stony Brook</span>
          </h1>

          <p className="text-lg text-[var(--text-secondary)] mb-10 max-w-2xl mx-auto leading-relaxed">
            Get instant, cited answers about admissions, tuition, housing,
            financial aid, and more — all from official university sources.
          </p>

          {/* Search box */}
          <div className="max-w-2xl mx-auto">
            <div className="flex items-center bg-white dark:bg-[var(--bg-secondary)] rounded-2xl shadow-lg border border-[var(--border)] overflow-hidden transition-shadow focus-within:shadow-xl focus-within:ring-2 focus-within:ring-sbu-red/20">
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
                className="m-2 px-6 py-2.5 bg-sbu-red text-white rounded-xl font-semibold text-sm hover:bg-sbu-red-dark disabled:opacity-40 transition-colors"
              >
                Ask
              </button>
            </div>

            <div className="mt-4 flex flex-wrap justify-center gap-2">
              {SAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => handleAsk(q)}
                  className="text-xs px-3 py-1.5 rounded-full border border-[var(--border)] text-[var(--text-muted)] hover:text-sbu-red hover:border-sbu-red/30 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Topics grid */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-20">
        <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] mb-8 text-center">
          Browse by Topic
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {TOPICS.map((topic) => (
            <Link
              key={topic.key}
              href={`/chat?q=Tell me about ${topic.name.toLowerCase()} at Stony Brook`}
              className="group p-5 rounded-xl border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] hover:border-sbu-red/30 hover:shadow-md transition-all"
            >
              <div className="text-2xl mb-3">{topic.icon}</div>
              <h3 className="font-semibold text-[var(--text-primary)] group-hover:text-sbu-red transition-colors mb-1">
                {topic.name}
              </h3>
              <p className="text-sm text-[var(--text-muted)]">{topic.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Trust section */}
      <section className="bg-[var(--bg-secondary)] border-t border-[var(--border)]">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-16 text-center">
          <h2 className="font-display text-2xl font-semibold text-[var(--text-primary)] mb-4">
            Grounded in Official Sources
          </h2>
          <p className="text-[var(--text-secondary)] max-w-2xl mx-auto leading-relaxed mb-8">
            Every answer includes citations from official Stony Brook University
            web pages. You can click through to read the original source and
            verify the information yourself.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[var(--text-muted)]">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              Source citations on every answer
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              Direct links to official pages
            </div>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              Office routing when you need human help
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
