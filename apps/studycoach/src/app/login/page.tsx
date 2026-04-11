"use client";
import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login, register } from "@/lib/api";

function LoginContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<"login" | "register">(
    searchParams.get("tab") === "register" ? "register" : "login"
  );
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [name, setName]         = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);

  const emailOk = email.toLowerCase().endsWith("@stonybrook.edu") ||
                  email.toLowerCase().endsWith("@alumni.stonybrook.edu");
  const emailErr = email && !emailOk ? "Must be @stonybrook.edu or @alumni.stonybrook.edu" : "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailOk) { setError("SBU email required"); return; }
    setError(""); setLoading(true);
    try {
      await (tab === "login" ? login(email, password) : register(email, password, name));
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-[var(--accent)] to-sky-400 text-white font-bold text-lg mb-3">SC</div>
          <h1 className="font-display text-xl font-semibold text-[var(--text-primary)]">StudyCoach</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">SBU students &amp; alumni only</p>
        </div>

        {/* Tabs */}
        <div className="flex mb-5 glass-card rounded-xl p-1">
          {(["login", "register"] as const).map((t) => (
            <button key={t} onClick={() => { setTab(t); setError(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-colors ${
                tab === t ? "bg-[var(--accent)] text-white shadow" : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
              }`}>
              {t === "login" ? "Sign In" : "Sign Up"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="glass-card rounded-xl p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-sm text-red-700 dark:text-red-300">
              {error}
            </div>
          )}

          {tab === "register" && (
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Full Name</label>
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Wolf" required
                className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60 transition-colors" />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              Email <span className="text-[var(--text-muted)] font-normal">(@stonybrook.edu)</span>
            </label>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder="netid@stonybrook.edu" required
              className={`w-full px-3 py-2.5 rounded-lg border text-sm text-[var(--text-primary)] outline-none transition-colors bg-[var(--bg-secondary)] ${
                emailErr ? "border-red-400" : "border-[var(--border)] focus:border-water-current/60"
              }`} />
            {emailErr && <p className="mt-1 text-xs text-red-500">{emailErr}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === "register" ? "Min. 8 characters" : ""}
              minLength={tab === "register" ? 8 : undefined} required
              className="w-full px-3 py-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] text-sm text-[var(--text-primary)] outline-none focus:border-water-current/60 transition-colors" />
          </div>

          <button type="submit" disabled={loading || !!emailErr}
            className="w-full py-2.5 btn-water text-white rounded-lg font-semibold text-sm disabled:opacity-50">
            {loading ? "..." : tab === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return <Suspense fallback={<div className="flex items-center justify-center h-64 text-[var(--text-muted)]">Loading...</div>}>
    <LoginContent />
  </Suspense>;
}
