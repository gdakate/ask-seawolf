"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { isLoggedIn, email, loading, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--border)] bg-white/90 dark:bg-[var(--bg-primary)]/90 backdrop-blur-md supports-[backdrop-filter]:bg-white/80">
      {/* SBU brand strip → water gradient */}
      <div className="h-[3px] bg-gradient-to-r from-sbu-red via-water-deep to-water-teal" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">

          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-cyan-400 flex items-center justify-center shadow-sm">
              <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5">
                <path d="M2 16 Q6 10 12 13 Q18 16 22 10" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none"/>
                <path d="M2 20 Q8 15 12 17 Q16 19 22 15" stroke="white" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity="0.6"/>
                <circle cx="12" cy="6" r="2.5" fill="white" opacity="0.9"/>
              </svg>
            </div>
            <div className="leading-tight">
              <div className="font-display font-bold text-[var(--text-primary)] text-base tracking-tight">
                SeaWolves
              </div>
              <div className="text-[9px] text-[var(--text-muted)] font-medium tracking-widest uppercase">
                SBU Digital Campus
              </div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5">
            {[
              { href: "/chat",              label: "Ask Seawolf" },
              { href: "http://localhost:3002", label: "SB-Alumni" },
              { href: "http://localhost:3003", label: "StudyCoach" },
              { href: "/topics",            label: "Topics" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] rounded-lg hover:bg-water-sky/60 dark:hover:bg-water-abyss/40 transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Auth buttons */}
          <div className="hidden md:flex items-center gap-2">
            {!loading && (
              isLoggedIn ? (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-[var(--text-muted)] max-w-[160px] truncate">
                    {email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] border border-[var(--border)] rounded-lg hover:border-water-current/50 transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className="px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/login?tab=register"
                    className="btn-water px-4 py-1.5 text-sm font-semibold text-white rounded-lg"
                  >
                    Sign Up
                  </Link>
                </div>
              )
            )}
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-[var(--text-secondary)] hover:text-[var(--accent)] transition-colors"
            aria-label="Toggle menu"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <path d="M3 12h18M3 6h18M3 18h18" />
              )}
            </svg>
          </button>
        </div>

        {mobileOpen && (
          <nav className="md:hidden pb-4 border-t border-[var(--border)] pt-3 space-y-1">
            {[
              { href: "/chat",   label: "Ask a Question" },
              { href: "/topics", label: "Browse Topics" },
              { href: "/search", label: "Search" },
              { href: "/help",   label: "Help" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] rounded-lg hover:bg-water-sky/60 dark:hover:bg-water-abyss/40 transition-colors"
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-2 border-t border-[var(--border)]">
              {isLoggedIn ? (
                <button
                  onClick={() => { setMobileOpen(false); handleLogout(); }}
                  className="block w-full text-left px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)]"
                >
                  Sign Out
                </button>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)]">
                    Sign In
                  </Link>
                  <Link href="/login?tab=register" onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2 text-sm font-semibold text-[var(--accent)]">
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
