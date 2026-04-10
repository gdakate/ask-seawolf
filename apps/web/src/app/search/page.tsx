"use client";

import { useState } from "react";
import { searchDocuments } from "@/lib/api";

interface SearchDoc {
  id: string;
  title: string;
  source_url: string;
  content_type: string;
  status: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchDoc[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const doSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchDocuments(query);
      setResults(data.items || []);
      setTotal(data.total || 0);
      setSearched(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12">
      <h1 className="font-display text-3xl font-bold text-[var(--text-primary)] mb-6">Search Sources</h1>

      <div className="flex gap-2 mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && doSearch()}
          placeholder="Search documents and sources..."
          className="flex-1 px-4 py-3 rounded-xl border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] text-sm outline-none focus:ring-2 focus:ring-sbu-red/20"
        />
        <button onClick={doSearch} disabled={loading} className="px-6 py-3 bg-sbu-red text-white rounded-xl text-sm font-semibold hover:bg-sbu-red-dark disabled:opacity-50 transition-colors">
          {loading ? "..." : "Search"}
        </button>
      </div>

      {searched && (
        <div>
          <p className="text-sm text-[var(--text-muted)] mb-4">{total} result{total !== 1 ? "s" : ""} found</p>
          <div className="space-y-3">
            {results.map((doc) => (
              <a
                key={doc.id}
                href={doc.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="block p-4 rounded-xl border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] hover:border-sbu-red/30 hover:shadow transition-all"
              >
                <h3 className="font-semibold text-[var(--text-primary)] text-sm">{doc.title}</h3>
                <p className="text-xs text-sbu-red mt-1 truncate">{doc.source_url}</p>
              </a>
            ))}
            {results.length === 0 && <p className="text-[var(--text-muted)] text-sm">No documents found.</p>}
          </div>
        </div>
      )}
    </div>
  );
}
