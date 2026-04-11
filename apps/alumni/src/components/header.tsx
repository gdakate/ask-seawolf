"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const NAV = [
  { href: "/matches", label: "Matches" },
  { href: "/feed",    label: "Community" },
  { href: "/profile", label: "My Profile" },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoggedIn, name, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg-primary)]/90 backdrop-blur-md border-b border-[var(--border)]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[var(--accent)] flex items-center justify-center text-white font-bold text-xs">SB</div>
          <span className="font-display font-semibold text-[var(--text-primary)] text-sm">
            Seawolf <span className="text-[var(--accent)]">Alumni</span>
          </span>
        </Link>

        {isLoggedIn && (
          <nav className="hidden sm:flex items-center gap-1">
            {NAV.map((item) => (
              <Link key={item.href} href={item.href}
                className={`px-3 py-1.5 rounded-lg text-sm transition-colors ${
                  pathname.startsWith(item.href)
                    ? "bg-[var(--accent)]/10 text-[var(--accent)] font-medium"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]"
                }`}>
                {item.label}
              </Link>
            ))}
          </nav>
        )}

        <div className="flex items-center gap-2">
          {isLoggedIn ? (
            <>
              <span className="text-xs text-[var(--text-muted)] hidden sm:block">{name}</span>
              <button onClick={() => { logout(); router.push("/"); }}
                className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                Sign out
              </button>
            </>
          ) : (
            <Link href="/login"
              className="text-sm px-4 py-1.5 rounded-lg bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition-colors font-medium">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
