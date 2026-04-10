"use client";

import { useQuery } from "@tanstack/react-query";
import { getOffices } from "@/lib/api";

export default function HelpPage() {
  const { data: offices } = useQuery({ queryKey: ["offices"], queryFn: getOffices });

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="font-display text-3xl font-bold text-[var(--text-primary)] mb-2">Help & Contact</h1>
      <p className="text-[var(--text-secondary)] mb-10">
        Can&apos;t find what you need? Reach out to the appropriate Stony Brook office directly.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {(offices || []).map((office) => (
          <div
            key={office.id}
            className="p-5 rounded-xl border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)]"
          >
            <h3 className="font-semibold text-[var(--text-primary)] mb-1">{office.name}</h3>
            {office.description && <p className="text-sm text-[var(--text-muted)] mb-3">{office.description}</p>}
            <div className="space-y-1.5 text-sm">
              {office.phone && (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <span className="text-xs">📞</span>
                  <a href={`tel:${office.phone}`} className="hover:text-sbu-red">{office.phone}</a>
                </div>
              )}
              {office.email && (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <span className="text-xs">✉️</span>
                  <a href={`mailto:${office.email}`} className="hover:text-sbu-red">{office.email}</a>
                </div>
              )}
              {office.location && (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <span className="text-xs">📍</span>
                  <span>{office.location}</span>
                </div>
              )}
              {office.hours && (
                <div className="flex items-center gap-2 text-[var(--text-secondary)]">
                  <span className="text-xs">🕐</span>
                  <span>{office.hours}</span>
                </div>
              )}
              {office.url && (
                <a href={office.url} target="_blank" rel="noopener noreferrer" className="inline-block mt-2 text-xs text-sbu-red hover:underline">
                  Visit website →
                </a>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
