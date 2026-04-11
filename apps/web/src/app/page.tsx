"use client";
import Link from "next/link";

const PLATFORMS = [
  {
    href: "/chat",
    label: "Ask Seawolf",
    tagline: "University Q&A",
    desc: "Ask anything about SBU — admissions, tuition, housing, financial aid, courses. Get instant answers grounded in official university sources.",
    features: ["RAG-powered search", "Source citations", "Office routing"],
    icon: (
      <svg viewBox="0 0 48 48" fill="none" className="w-full h-full">
        <circle cx="24" cy="24" r="20" fill="rgba(14,165,233,0.12)" stroke="rgba(14,165,233,0.4)" strokeWidth="1.5"/>
        <path d="M14 18 C14 14 18 11 24 11 C30 11 34 14 34 18 C34 23 29 26 24 26 L24 30" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
        <circle cx="24" cy="35" r="1.8" fill="currentColor"/>
        <path d="M8 38 Q16 32 24 35 Q32 38 40 32" stroke="rgba(14,165,233,0.35)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
      </svg>
    ),
    gradient: "from-sky-400/20 via-blue-400/10 to-cyan-300/20",
    border: "hover:border-sky-400/60",
    badge: "bg-sky-400/15 text-sky-600 dark:text-sky-300",
    cta: "Ask a Question →",
    ctaClass: "bg-sky-500 hover:bg-sky-400",
  },
  {
    href: "http://localhost:3002",
    label: "SB-lumni",
    tagline: "Alumni Network",
    desc: "AI-powered matching for Stony Brook graduates. Find mentors, collaborators, and fellow Seawolves based on major, career path, and shared interests.",
    features: ["Vector similarity matching", "Coffee chat & mentoring", "Alumni feed"],
    icon: (
      <svg viewBox="0 0 48 48" fill="none" className="w-full h-full">
        <circle cx="17" cy="18" r="6" stroke="currentColor" strokeWidth="2" fill="rgba(14,165,233,0.1)"/>
        <circle cx="31" cy="18" r="6" stroke="currentColor" strokeWidth="2" fill="rgba(14,165,233,0.1)"/>
        <path d="M8 38 C8 30 12 27 17 27 C19 27 21 28 22 29" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <path d="M26 29 C27 28 29 27 31 27 C36 27 40 30 40 38" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <path d="M19 33 C19 29 21.5 27 24 27 C26.5 27 29 29 29 33 C29 37 26.5 39 24 39 C21.5 39 19 37 19 33Z" fill="rgba(14,165,233,0.2)" stroke="currentColor" strokeWidth="2"/>
        <path d="M6 42 Q24 36 42 42" stroke="rgba(14,165,233,0.3)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
      </svg>
    ),
    gradient: "from-teal-400/20 via-cyan-400/10 to-blue-300/20",
    border: "hover:border-teal-400/60",
    badge: "bg-teal-400/15 text-teal-600 dark:text-teal-300",
    cta: "Find Your Network →",
    ctaClass: "bg-teal-500 hover:bg-teal-400",
  },
  {
    href: "http://localhost:3003",
    label: "StudyCoach",
    tagline: "AI Tutor",
    desc: "Upload your lecture slides and course notes. Get an auto-generated learning map, a smart study plan, and an AI tutor that never just gives you the answer.",
    features: ["Socratic teaching method", "Auto learning maps", "Study plan generation"],
    icon: (
      <svg viewBox="0 0 48 48" fill="none" className="w-full h-full">
        <rect x="10" y="8" width="28" height="32" rx="4" fill="rgba(14,165,233,0.1)" stroke="currentColor" strokeWidth="2"/>
        <path d="M16 16 L32 16" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <path d="M16 22 L28 22" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <path d="M16 28 L24 28" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        <circle cx="35" cy="35" r="8" fill="rgba(14,165,233,0.15)" stroke="currentColor" strokeWidth="2"/>
        <path d="M32 35 Q35 31 38 35" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" fill="none"/>
        <circle cx="35" cy="38" r="1.2" fill="currentColor"/>
        <path d="M4 44 Q12 40 20 43 Q28 46 36 42 Q40 40 44 42" stroke="rgba(14,165,233,0.3)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
      </svg>
    ),
    gradient: "from-indigo-400/20 via-blue-400/10 to-sky-300/20",
    border: "hover:border-indigo-400/60",
    badge: "bg-indigo-400/15 text-indigo-600 dark:text-indigo-300",
    cta: "Start Studying →",
    ctaClass: "bg-indigo-500 hover:bg-indigo-400",
  },
];

// Bubbles: [size, left%, delay, duration]
const BUBBLES: [number, number, number, number][] = [
  [10, 5,   0,   4.2], [6,  15, 1.1, 5.8], [14, 28, 0.5, 6.5],
  [8,  45, 1.8, 4.8], [5,  62, 0.2, 7.1], [12, 75, 1.3, 5.3],
  [7,  88, 0.7, 6.0], [9,  95, 1.5, 4.5],
];

export default function SeaportHome() {
  return (
    <div className="min-h-screen">

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="hero-bg relative overflow-hidden min-h-[92vh] flex items-center">
        {BUBBLES.map(([size, left, delay, dur], i) => (
          <span key={i} className="bubble" style={{
            width: size, height: size, left: `${left}%`, bottom: "8%",
            "--dur": `${dur}s`, "--delay": `${delay}s`,
          } as React.CSSProperties} />
        ))}

        {/* Light refraction */}
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 70% 60% at 50% -5%, rgba(255,255,255,0.5) 0%, transparent 65%)" }} />

        {/* Diagonal refraction lines */}
        <div className="absolute inset-0 pointer-events-none opacity-30"
          style={{
            backgroundImage: "repeating-linear-gradient(-48deg, transparent 0px, transparent 60px, rgba(186,230,253,0.08) 60px, rgba(186,230,253,0.08) 75px)"
          }} />

        <div className="relative max-w-5xl mx-auto px-6 sm:px-8 py-24 text-center w-full">

          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/50 dark:bg-[var(--bg-secondary)]/60 backdrop-blur-sm border border-[var(--border)] text-[var(--accent)] text-xs font-semibold mb-8 tracking-widest uppercase shadow-sm">
            <span className="w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
            Stony Brook University · 2026
          </div>

          {/* Logo mark */}
          <div className="flex items-center justify-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--accent)] to-cyan-400 flex items-center justify-center shadow-lg">
              <svg viewBox="0 0 40 40" fill="none" className="w-9 h-9">
                <path d="M4 28 Q10 18 20 22 Q30 26 36 16" stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"/>
                <path d="M4 34 Q12 26 20 28 Q28 30 36 22" stroke="white" strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.6"/>
                <circle cx="20" cy="12" r="4" fill="white" opacity="0.9"/>
                <path d="M20 16 L20 22" stroke="white" strokeWidth="2.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="text-left">
              <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-bold text-[var(--text-primary)] tracking-tight leading-none">
                Seaport
              </h1>
              <p className="text-sm text-[var(--text-muted)] tracking-widest mt-1">SBU DIGITAL CAMPUS</p>
            </div>
          </div>

          <p className="text-xl sm:text-2xl text-[var(--text-secondary)] mb-4 max-w-2xl mx-auto leading-relaxed font-light">
            One platform. Three tools built for every Seawolf.
          </p>
          <p className="text-base text-[var(--text-muted)] max-w-xl mx-auto mb-12">
            Get answers about SBU, connect with alumni, and master your coursework — all in one place.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link href="#platforms"
              className="px-8 py-3.5 btn-water text-white rounded-xl font-semibold text-base shadow-md">
              Explore Platforms
            </Link>
            <Link href="/chat"
              className="px-8 py-3.5 rounded-xl border border-[var(--border)] bg-white/50 dark:bg-[var(--bg-secondary)]/50 backdrop-blur-sm text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/50 transition-colors text-base font-medium">
              Ask Seawolf →
            </Link>
          </div>
        </div>

        {/* Wave bottom */}
        <div className="absolute bottom-0 left-0 right-0">
          <svg viewBox="0 0 1440 80" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
            <path d="M0,40 C240,80 480,0 720,40 C960,80 1200,0 1440,40 L1440,80 L0,80 Z"
              fill="rgba(186,230,253,0.25)" />
            <path d="M0,55 C300,20 600,70 900,45 C1100,30 1300,60 1440,50 L1440,80 L0,80 Z"
              fill="rgba(125,211,252,0.15)" />
          </svg>
        </div>
      </section>

      {/* ── Platform cards ────────────────────────────────────── */}
      <section id="platforms" className="max-w-6xl mx-auto px-4 sm:px-6 py-24 space-y-8">
        <div className="text-center mb-16">
          <span className="inline-block text-xs font-semibold uppercase tracking-widest text-[var(--accent)] bg-[var(--accent)]/10 px-3 py-1 rounded-full mb-4">
            Three Platforms
          </span>
          <h2 className="font-display text-3xl sm:text-4xl font-bold text-[var(--text-primary)] mb-4">
            Everything a Seawolf needs
          </h2>
        </div>

        {/* Card 1 — Ask Seawolf */}
        <Link href="/chat" className="group block">
          <div className="rounded-3xl overflow-hidden border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5">
            <div className="flex flex-col sm:flex-row">
              {/* Color panel */}
              <div className="relative sm:w-56 shrink-0 min-h-[160px] sm:min-h-0 flex flex-col items-center justify-center gap-3 p-8 overflow-hidden"
                style={{ background: "linear-gradient(145deg, #38bdf8 0%, #0ea5e9 50%, #0284c7 100%)" }}>
                <div className="absolute bottom-0 left-0 right-0 opacity-20">
                  <svg viewBox="0 0 280 60" fill="none"><path d="M0,30 C70,10 140,50 280,20 L280,60 L0,60 Z" fill="white"/></svg>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300 relative">
                  <svg viewBox="0 0 40 40" fill="none" className="w-9 h-9">
                    <path d="M12 16 C12 11 15.5 8 20 8 C24.5 8 28 11 28 16 C28 20 24.5 22.5 20 22.5 L20 26" stroke="white" strokeWidth="2.2" strokeLinecap="round"/>
                    <circle cx="20" cy="30" r="1.8" fill="white"/>
                    <path d="M4 36 Q12 30 20 33 Q28 36 36 30" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" strokeLinecap="round" fill="none"/>
                  </svg>
                </div>
                <p className="text-white font-black text-xl tracking-tight leading-none">Ask Seawolf</p>
              </div>
              {/* White content panel */}
              <div className="flex-1 flex flex-col sm:flex-row items-start sm:items-center gap-4 p-6 sm:p-8">
                <div className="flex-1">
                  <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-sky-500 bg-sky-50 dark:bg-sky-900/30 dark:text-sky-400 px-2.5 py-1 rounded-full mb-3">University Q&A</span>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
                    Instant answers to anything SBU — admissions, tuition, housing, financial aid. Grounded in official sources, with citations.
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {["RAG search", "Source citations", "Office routing"].map(f => (
                      <span key={f} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-[var(--border)]">{f}</span>
                    ))}
                  </div>
                </div>
                <div className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-500 text-white text-sm font-bold shadow group-hover:bg-sky-400 transition-colors">
                  Ask now <svg className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" d="M5 12h14M12 5l7 7-7 7"/></svg>
                </div>
              </div>
            </div>
          </div>
        </Link>

        {/* Card 2 — SB-lumni */}
        <Link href="http://localhost:3002" className="group block">
          <div className="rounded-3xl overflow-hidden border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5">
            <div className="flex flex-col sm:flex-row">
              <div className="relative sm:w-56 shrink-0 min-h-[160px] sm:min-h-0 flex flex-col items-center justify-center gap-3 p-8 overflow-hidden"
                style={{ background: "linear-gradient(145deg, #34d399 0%, #10b981 50%, #059669 100%)" }}>
                <div className="absolute bottom-0 left-0 right-0 opacity-20">
                  <svg viewBox="0 0 280 60" fill="none"><path d="M0,20 C80,50 160,10 280,35 L280,60 L0,60 Z" fill="white"/></svg>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300 relative">
                  <svg viewBox="0 0 40 40" fill="none" className="w-9 h-9">
                    <circle cx="14" cy="14" r="5" stroke="white" strokeWidth="2" fill="rgba(255,255,255,0.15)"/>
                    <circle cx="26" cy="14" r="5" stroke="white" strokeWidth="2" fill="rgba(255,255,255,0.15)"/>
                    <path d="M7 32 C7 26 10 24 14 24 C15.5 24 17 24.5 18 25.5" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M22 25.5 C23 24.5 24.5 24 26 24 C30 24 33 26 33 32" stroke="white" strokeWidth="2" strokeLinecap="round"/>
                    <ellipse cx="20" cy="29" rx="4.5" ry="4" stroke="white" strokeWidth="2" fill="rgba(255,255,255,0.2)"/>
                  </svg>
                </div>
                <p className="text-white font-black text-xl tracking-tight leading-none">SB-lumni</p>
              </div>
              <div className="flex-1 flex flex-col sm:flex-row items-start sm:items-center gap-4 p-6 sm:p-8">
                <div className="flex-1">
                  <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-emerald-600 bg-emerald-50 dark:bg-emerald-900/30 dark:text-emerald-400 px-2.5 py-1 rounded-full mb-3">Alumni Network</span>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
                    AI-powered matching for Stony Brook graduates. Coffee chats, mentoring, referrals — find the Seawolves who share your path.
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {["Vector matching", "Coffee chats", "Alumni feed"].map(f => (
                      <span key={f} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-[var(--border)]">{f}</span>
                    ))}
                  </div>
                </div>
                <div className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-500 text-white text-sm font-bold shadow group-hover:bg-emerald-400 transition-colors">
                  Connect <svg className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" d="M5 12h14M12 5l7 7-7 7"/></svg>
                </div>
              </div>
            </div>
          </div>
        </Link>

        {/* Card 3 — StudyCoach */}
        <Link href="http://localhost:3003" className="group block">
          <div className="rounded-3xl overflow-hidden border border-[var(--border)] bg-white dark:bg-[var(--bg-secondary)] shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-0.5">
            <div className="flex flex-col sm:flex-row">
              <div className="relative sm:w-56 shrink-0 min-h-[160px] sm:min-h-0 flex flex-col items-center justify-center gap-3 p-8 overflow-hidden"
                style={{ background: "linear-gradient(145deg, #a78bfa 0%, #7c3aed 50%, #5b21b6 100%)" }}>
                <div className="absolute bottom-0 left-0 right-0 opacity-20">
                  <svg viewBox="0 0 280 60" fill="none"><path d="M0,40 C60,10 160,55 280,25 L280,60 L0,60 Z" fill="white"/></svg>
                </div>
                <div className="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300 relative">
                  <svg viewBox="0 0 40 40" fill="none" className="w-9 h-9">
                    <rect x="8" y="6" width="17" height="22" rx="2.5" stroke="white" strokeWidth="2" fill="rgba(255,255,255,0.1)"/>
                    <path d="M12 12 L21 12" stroke="white" strokeWidth="1.6" strokeLinecap="round"/>
                    <path d="M12 16 L19 16" stroke="white" strokeWidth="1.6" strokeLinecap="round"/>
                    <path d="M12 20 L16 20" stroke="white" strokeWidth="1.6" strokeLinecap="round"/>
                    <circle cx="28" cy="28" r="7" fill="rgba(139,92,246,0.5)" stroke="white" strokeWidth="2"/>
                    <path d="M25.5 28 Q28 25 30.5 28" stroke="white" strokeWidth="1.6" strokeLinecap="round" fill="none"/>
                    <circle cx="28" cy="30.5" r="1" fill="white"/>
                  </svg>
                </div>
                <p className="text-white font-black text-xl tracking-tight leading-none">StudyCoach</p>
              </div>
              <div className="flex-1 flex flex-col sm:flex-row items-start sm:items-center gap-4 p-6 sm:p-8">
                <div className="flex-1">
                  <span className="inline-block text-[10px] font-bold uppercase tracking-widest text-violet-600 bg-violet-50 dark:bg-violet-900/30 dark:text-violet-400 px-2.5 py-1 rounded-full mb-3">AI Tutor</span>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">
                    Upload your lecture slides and get an AI tutor that never just gives you the answer — it guides you to figure it out yourself.
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {["Socratic method", "Auto learning maps", "Study plans"].map(f => (
                      <span key={f} className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--bg-tertiary)] text-[var(--text-muted)] border border-[var(--border)]">{f}</span>
                    ))}
                  </div>
                </div>
                <div className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white text-sm font-bold shadow group-hover:bg-violet-500 transition-colors">
                  Study now <svg className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5"><path strokeLinecap="round" d="M5 12h14M12 5l7 7-7 7"/></svg>
                </div>
              </div>
            </div>
          </div>
        </Link>
      </section>

      {/* ── Wave divider ─────────────────────────────────────── */}
      <div className="relative overflow-hidden h-20 -mt-8">
        <svg viewBox="0 0 1440 80" fill="none" className="w-full absolute bottom-0">
          <path d="M0,20 C360,60 720,-10 1080,30 C1260,50 1380,20 1440,30 L1440,80 L0,80 Z"
            fill="rgba(186,230,253,0.2)" />
        </svg>
      </div>

      {/* ── Stats bar ────────────────────────────────────────── */}
      <section className="bg-gradient-to-r from-[var(--accent)]/5 via-cyan-400/8 to-teal-400/5 border-y border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-6 py-12 grid grid-cols-2 sm:grid-cols-4 gap-8 text-center">
          {[
            { value: "3",         label: "Integrated Platforms" },
            { value: "RAG + AI",  label: "Powered By" },
            { value: "SBU Only",  label: "Exclusive Access" },
            { value: "24/7",      label: "Always Available" },
          ].map((s) => (
            <div key={s.label}>
              <p className="font-display text-2xl font-bold text-[var(--accent)] mb-1">{s.value}</p>
              <p className="text-xs text-[var(--text-muted)] uppercase tracking-wide">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── How it flows ─────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-[var(--text-primary)] mb-3">
            Your journey through Seaport
          </h2>
          <p className="text-[var(--text-muted)] text-sm max-w-md mx-auto">
            From prospective student to active alumnus — each platform supports a different chapter.
          </p>
        </div>

        <div className="relative">
          {/* Connector line */}
          <div className="hidden sm:block absolute top-8 left-[calc(16.67%)] right-[calc(16.67%)] h-0.5 bg-gradient-to-r from-sky-400/40 via-teal-400/40 to-indigo-400/40" />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 relative">
            {[
              { num: "1", icon: "🔍", title: "Get Answers", sub: "Ask Seawolf", desc: "Before you even apply — find answers to every SBU question instantly.", color: "bg-sky-400" },
              { num: "2", icon: "🤝", title: "Build Connections", sub: "SB-lumni", desc: "Graduate and stay connected. Mentor students, find collaborators, grow your network.", color: "bg-teal-400" },
              { num: "3", icon: "🧠", title: "Master Your Courses", sub: "StudyCoach", desc: "While you're a student — upload materials and learn through AI-guided Socratic dialogue.", color: "bg-indigo-400" },
            ].map((step) => (
              <div key={step.num} className="text-center">
                <div className={`w-16 h-16 rounded-2xl ${step.color} flex items-center justify-center text-white text-2xl mx-auto mb-4 shadow-lg`}>
                  {step.icon}
                </div>
                <p className="font-display font-bold text-[var(--text-primary)] mb-0.5">{step.title}</p>
                <p className="text-xs text-[var(--accent)] font-semibold mb-2 uppercase tracking-wide">{step.sub}</p>
                <p className="text-sm text-[var(--text-muted)] leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer CTA ───────────────────────────────────────── */}
      <section className="hero-bg relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none"
          style={{ background: "radial-gradient(ellipse 60% 50% at 50% 0%, rgba(255,255,255,0.4) 0%, transparent 70%)" }} />
        <div className="relative max-w-2xl mx-auto px-6 py-20 text-center">
          <div className="text-4xl mb-4">🌊</div>
          <h2 className="font-display text-2xl font-bold text-[var(--text-primary)] mb-3">
            Ready to dive in?
          </h2>
          <p className="text-[var(--text-muted)] mb-8 text-sm">
            Exclusively for <span className="font-semibold text-[var(--accent)]">@stonybrook.edu</span> and{" "}
            <span className="font-semibold text-[var(--accent)]">@alumni.stonybrook.edu</span>
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link href="/chat" className="px-7 py-3 btn-water text-white rounded-xl font-semibold">Ask Seawolf</Link>
            <Link href="http://localhost:3002" className="px-7 py-3 rounded-xl border border-[var(--border)] bg-white/50 dark:bg-[var(--bg-secondary)]/50 backdrop-blur-sm text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/50 transition-colors font-medium">SB-lumni</Link>
            <Link href="http://localhost:3003" className="px-7 py-3 rounded-xl border border-[var(--border)] bg-white/50 dark:bg-[var(--bg-secondary)]/50 backdrop-blur-sm text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/50 transition-colors font-medium">StudyCoach</Link>
          </div>
        </div>
      </section>

    </div>
  );
}
