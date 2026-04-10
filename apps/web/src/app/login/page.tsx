"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { publicLogin, publicRegister, isSbuEmail } from "@/lib/api";
import { Suspense } from "react";

const SBU_DOMAIN = "stonybrook.edu";

function LoginForm() {
  const searchParams = useSearchParams();
  const [tab, setTab] = useState<"login" | "register">(
    searchParams.get("tab") === "register" ? "register" : "login"
  );
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [name, setName]         = useState("");
  const [error, setError]       = useState("");
  const [loading, setLoading]   = useState(false);
  const router   = useRouter();
  const redirect = searchParams.get("redirect") || "/chat";

  const emailError = email && !isSbuEmail(email)
    ? `Must be a @${SBU_DOMAIN} address`
    : "";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isSbuEmail(email)) {
      setError(`Only @${SBU_DOMAIN} email addresses are allowed.`);
      return;
    }
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await publicLogin(email, password);
      } else {
        await publicRegister(email, password, name);
      }
      router.push(redirect);
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="hero-bg min-h-screen flex items-center justify-center px-4 relative overflow-hidden">

      {/* Radial light from above */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: "radial-gradient(ellipse 60% 40% at 50% 0%, rgba(255,255,255,0.35) 0%, transparent 65%)",
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-sbu-red text-white font-bold text-xl mb-4 shadow-lg">
            SW
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Seawolf Ask</h1>
          <p className="text-sm text-[var(--text-muted)] mt-1">
            Sign in with your SBU account
          </p>
        </div>

        {/* Tabs */}
        <div className="flex mb-4 glass-card rounded-xl p-1">
          {(["login", "register"] as const).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(""); }}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === t
                  ? "bg-[var(--accent)] text-white shadow"
                  : "text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
              }`}
            >
              {t === "login" ? "Sign In" : "Register"}
            </button>
          ))}
        </div>

        <form
          onSubmit={handleSubmit}
          className="glass-card rounded-2xl p-6 space-y-4"
        >
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {tab === "register" && (
            <div>
              <label className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Jane Wolf"
                className="w-full px-3.5 py-2.5 border border-[var(--border)] rounded-xl text-sm bg-white/70 dark:bg-water-abyss/70 text-[var(--text-primary)] focus:outline-none focus:water-ring transition-shadow"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
              Email{" "}
              <span className="text-[var(--text-muted)] font-normal">(@stonybrook.edu only)</span>
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={`netid@${SBU_DOMAIN}`}
              className={`w-full px-3.5 py-2.5 border rounded-xl text-sm bg-white/70 dark:bg-water-abyss/70 text-[var(--text-primary)] focus:outline-none focus:water-ring transition-shadow ${
                emailError ? "border-red-400" : "border-[var(--border)]"
              }`}
              required
            />
            {emailError && <p className="mt-1 text-xs text-red-600">{emailError}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-[var(--text-primary)] mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === "register" ? "Minimum 8 characters" : ""}
              className="w-full px-3.5 py-2.5 border border-[var(--border)] rounded-xl text-sm bg-white/70 dark:bg-water-abyss/70 text-[var(--text-primary)] focus:outline-none focus:water-ring transition-shadow"
              minLength={tab === "register" ? 8 : undefined}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !!emailError}
            className="btn-water w-full py-2.5 text-white rounded-xl font-semibold text-sm disabled:opacity-50"
          >
            {loading
              ? tab === "login" ? "Signing in..." : "Creating account..."
              : tab === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>

        <p className="text-xs text-[var(--text-muted)] text-center mt-4">
          Only current Stony Brook University students, faculty, and staff may access this service.
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
