"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { getTopics } from "@/lib/api";

export default function TopicsPage() {
  const { data: topics } = useQuery({ queryKey: ["topics"], queryFn: getTopics });

  const iconMap: Record<string, string> = {
    admissions: "🎓", registrar: "📄", bursar: "💰", financial_aid: "📋",
    housing: "🏠", dining: "🍽️", academics: "📚", student_affairs: "👥",
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="font-display text-3xl font-bold text-[var(--text-primary)] mb-2">Browse Topics</h1>
      <p className="text-[var(--text-secondary)] mb-10">
        Select a topic to explore or ask specific questions.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {(topics || []).map((t) => (
          <Link
            key={t.key}
            href={`/chat?q=Tell me about ${t.name.toLowerCase()} at Stony Brook University`}
            className="group p-6 rounded-xl border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] hover:border-sbu-red/30 hover:shadow-lg transition-all"
          >
            <div className="text-3xl mb-3">{iconMap[t.key] || "📌"}</div>
            <h2 className="font-semibold text-lg text-[var(--text-primary)] group-hover:text-sbu-red transition-colors mb-2">
              {t.name}
            </h2>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">{t.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
