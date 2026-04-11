"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/courses",   label: "Courses",   icon: "📚" },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const { isLoggedIn, name, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg-primary)]/95 backdrop-blur-md border-b border-[var(--border)]">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Logo */}
        <Link href={isLoggedIn ? "/dashboard" : "/"} className="flex items-center gap-2 flex-shrink-0">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--accent)] to-sky-400 flex items-center justify-center shadow-sm">
            <span className="text-white font-black text-[11px] leading-none tracking-tight">SC</span>
          </div>
          <span className="font-display font-bold text-[var(--text-primary)] text-base">
            Study<span className="text-[var(--accent)]">Coach</span>
          </span>
        </Link>

        {/* App nav (logged in) */}
        {isLoggedIn && (
          <nav className="flex items-center gap-1">
            {NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Link key={item.href} href={item.href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    active
                      ? "bg-[var(--accent)]/12 text-[var(--accent)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-secondary)]"
                  }`}>
                  <span className="text-base leading-none">{item.icon}</span>
                  <span className="hidden sm:block">{item.label}</span>
                </Link>
              );
            })}
          </nav>
        )}

        {/* Right: name + sign out */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {isLoggedIn ? (
            <>
              <span className="text-xs text-[var(--text-muted)] hidden md:block truncate max-w-[120px]">{name}</span>
              <button onClick={() => { logout(); router.push("/"); }}
                className="text-xs px-3 py-1.5 rounded-lg border border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors">
                Sign out
              </button>
            </>
          ) : (
            <Link href="/login"
              className="text-sm px-4 py-1.5 rounded-lg bg-[var(--accent)] text-white hover:opacity-90 transition-opacity font-medium">
              Sign in
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
