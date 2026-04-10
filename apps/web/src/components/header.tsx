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

          <Link href="/" className="flex items-center gap-3 group">
            {/* Logo mark — SBU red stays for brand identity */}
            <div className="relative w-9 h-9 rounded-xl bg-sbu-red flex items-center justify-center text-white font-bold text-sm overflow-hidden">
              <span className="relative z-10">SB</span>
              {/* subtle shimmer on hover */}
              <div className="absolute inset-0 bg-gradient-to-br from-white/0 via-white/10 to-white/0 group-hover:via-white/20 transition-all duration-500" />
            </div>
            <div className="leading-tight">
              <div className="font-display font-semibold text-[var(--text-primary)] text-base tracking-tight">
                Ask Seawolves
              </div>
              <div className="text-[10px] text-[var(--text-muted)] font-medium tracking-widest uppercase">
                Stony Brook University
              </div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-0.5">
            {[
              { href: "/chat",   label: "Ask a Question" },
              { href: "/topics", label: "Browse Topics" },
              { href: "/search", label: "Search" },
              { href: "/help",   label: "Help" },
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
