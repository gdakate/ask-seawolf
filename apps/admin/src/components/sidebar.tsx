"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/api";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/sources", label: "Sources", icon: "🌐" },
  { href: "/documents", label: "Documents", icon: "📄" },
  { href: "/chunks", label: "Chunks", icon: "🧩" },
  { href: "/faqs", label: "FAQs", icon: "❓" },
  { href: "/conversations", label: "Conversations", icon: "💬" },
  { href: "/feedback", label: "Feedback", icon: "⭐" },
  { href: "/evaluations", label: "Evaluations", icon: "🧪" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 bg-[#1a1b1e] text-white min-h-screen flex flex-col fixed left-0 top-0 z-40">
      <div className="p-4 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sbu-red flex items-center justify-center text-white font-bold text-xs">SB</div>
          <div>
            <div className="text-sm font-semibold">Seawolf Ask</div>
            <div className="text-[10px] text-gray-400 uppercase tracking-wider">Admin Panel</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                active ? "bg-white/10 text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-white/10">
        <button
          onClick={() => { clearToken(); window.location.href = "/login"; }}
          className="w-full px-3 py-2 text-sm text-gray-400 hover:text-white rounded-lg hover:bg-white/5 text-left transition-colors"
        >
          Sign Out
        </button>
      </div>
    </aside>
  );
}
