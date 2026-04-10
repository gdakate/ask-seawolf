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
    <header className="sticky top-0 z-50 border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/80 dark:bg-[var(--bg-primary)]/95 dark:border-[var(--border)]">
      {/* SBU branding strip */}
      <div className="bg-sbu-red h-1" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-lg bg-sbu-red flex items-center justify-center text-white font-bold text-sm">
              SB
            </div>
            <div className="leading-tight">
              <div className="font-display font-semibold text-[var(--text-primary)] text-base tracking-tight">
                Seawolf Ask
              </div>
              <div className="text-xs text-[var(--text-muted)] font-medium tracking-wide uppercase">
                Stony Brook University
              </div>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {[
              { href: "/chat", label: "Ask a Question" },
              { href: "/topics", label: "Browse Topics" },
              { href: "/search", label: "Search" },
              { href: "/help", label: "Help" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red rounded-lg hover:bg-sbu-gray-50 dark:hover:bg-[var(--bg-secondary)] transition-colors"
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
                    className="px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red border border-[var(--border)] rounded-lg hover:border-sbu-red/30 transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <Link
                    href="/login"
                    className="px-3 py-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/login?tab=register"
                    className="px-4 py-1.5 text-sm font-semibold bg-sbu-red text-white rounded-lg hover:bg-sbu-red-dark transition-colors"
                  >
                    Sign Up
                  </Link>
                </div>
              )
            )}
          </div>

          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="md:hidden p-2 text-[var(--text-secondary)]"
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
              { href: "/chat", label: "Ask a Question" },
              { href: "/topics", label: "Browse Topics" },
              { href: "/search", label: "Search" },
              { href: "/help", label: "Help" },
            ].map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red rounded-lg"
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-2 border-t border-[var(--border)]">
              {isLoggedIn ? (
                <button
                  onClick={() => { setMobileOpen(false); handleLogout(); }}
                  className="block w-full text-left px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red"
                >
                  Sign Out
                </button>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2 text-sm font-medium text-[var(--text-secondary)] hover:text-sbu-red">
                    Sign In
                  </Link>
                  <Link href="/login?tab=register" onClick={() => setMobileOpen(false)}
                    className="block px-3 py-2 text-sm font-semibold text-sbu-red">
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
