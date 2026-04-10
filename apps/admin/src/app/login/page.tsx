"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register } from "@/lib/api";

const SBU_DOMAIN = "stonybrook.edu";

function isSbuEmail(email: string) {
  return email.toLowerCase().endsWith(`@${SBU_DOMAIN}`);
}

export default function LoginPage() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

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
        await login(email, password);
      } else {
        await register(email, password, name);
      }
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f0f1f3]">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-sbu-red text-white font-bold text-lg mb-3">SB</div>
          <h1 className="text-xl font-semibold text-gray-900">Admin Portal</h1>
          <p className="text-sm text-gray-500 mt-1">Seawolf Ask</p>
        </div>

        {/* Tabs */}
        <div className="flex mb-4 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => { setTab("login"); setError(""); }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
              tab === "login" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Sign In
          </button>
          <button
            onClick={() => { setTab("register"); setError(""); }}
            className={`flex-1 py-2 text-sm font-medium rounded-md transition-colors ${
              tab === "register" ? "bg-white shadow text-gray-900" : "text-gray-500 hover:text-gray-700"
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
          {error && <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">{error}</div>}

          {tab === "register" && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text" value={name} onChange={(e) => setName(e.target.value)}
                placeholder="Jane Wolf"
                className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-sbu-red/20 focus:border-sbu-red outline-none"
                required
              />
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-gray-400 font-normal">(@stonybrook.edu only)</span>
            </label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              placeholder={`netid@${SBU_DOMAIN}`}
              className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:ring-2 focus:ring-sbu-red/20 focus:border-sbu-red outline-none ${
                emailError ? "border-red-400 bg-red-50" : "border-gray-300"
              }`}
              required
            />
            {emailError && <p className="mt-1 text-xs text-red-600">{emailError}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === "register" ? "Minimum 8 characters" : ""}
              className="w-full px-3 py-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-sbu-red/20 focus:border-sbu-red outline-none"
              minLength={tab === "register" ? 8 : undefined}
              required
            />
          </div>

          <button type="submit" disabled={loading || !!emailError}
            className="w-full py-2.5 bg-sbu-red text-white rounded-lg font-semibold text-sm hover:bg-sbu-red-dark disabled:opacity-50 transition-colors">
            {loading ? (tab === "login" ? "Signing in..." : "Registering...") : (tab === "login" ? "Sign In" : "Create Account")}
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-4">
          Only @stonybrook.edu accounts are permitted.
        </p>
      </div>
    </div>
  );
}
