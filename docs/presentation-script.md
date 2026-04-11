# Seaport — 2-Minute Presentation Script

## Slide Structure (2 min total)

---

### SLIDE 1 — Hook (0:00–0:12)
**Visual**: Seaport portal at localhost:3000 — hero section with wave animation

**Script**:
> "What if every Seawolf — student, graduate, or admin — had one platform built for them? That's Seaport."

---

### SLIDE 2 — The Problem (0:12–0:25)
**Visual**: Fragmented landscape — SBU website, LinkedIn, ChatGPT, spreadsheets

**Script**:
> "Students Google SBU policies and get outdated pages. Graduates lose touch after graduation. When students use AI to study, they get the answer — not the learning. And admins have no way to monitor or control what the AI is saying. Seaport solves all four."

---

### SLIDE 3 — Ask Seawolf (0:25–0:42)
**Visual**: `/chat` — type "How do I apply for financial aid?" → answer with citations

**Script**:
> "Ask Seawolf is a RAG-powered chatbot grounded in 22,000 chunks of official SBU data. Every answer comes with source citations. It detects when a question needs a real person and routes you to the right office."

**Key tech**: RAG pipeline, pgvector, citation bundling, office routing

---

### SLIDE 4 — Admin Dashboard (0:42–0:57)
**Visual**: `localhost:3001` — show Sources list, then Evaluations page with pass/fail scores

**Script**:
> "Admins have full control through the dashboard. They can manage which sources the AI learns from, run crawl and reindex jobs, review every conversation, curate FAQ overrides that take priority over RAG, and run quality evaluations — so they always know if the AI is answering accurately."

**Key features**: source management, crawl/reindex jobs, FAQ overrides, conversation review, evaluation runner

---

### SLIDE 5 — SB-lumni (0:57–1:10)
**Visual**: SB-lumni People tab — match cards with "Why you match" reasons

**Script**:
> "SB-lumni connects SBU graduates through a two-stage AI matching pipeline — vector similarity via pgvector, then multi-signal reranking across major, career path, skills, and graduation year. Every card explains exactly why you're a match."

**Key tech**: pgvector ANN → Jaccard reranking → MMR diversity

---

### SLIDE 6 — StudyCoach (1:10–1:32)
**Visual**: StudyCoach teach mode — AI message with one concept, one question. Student types answer.

**Script**:
> "StudyCoach flips the AI tutoring model. Upload your lecture slides — the AI parses them and generates a learning map with real section titles, not raw text. In teach mode, it gives you one idea at a time and ends every message with one question. It never just gives you the answer. That's the Socratic method, automated."

**Key tech**: PDF → page grouping → AI title enrichment → Socratic TEACH_SYSTEM prompt

---

### SLIDE 7 — Architecture & Design (1:32–1:47)
**Visual**: Architecture diagram — 4 apps + 1 shared backend, then a shot of the water theme across all apps

**Script**:
> "Four apps, one shared FastAPI backend, one PostgreSQL database with pgvector. The water theme runs through everything — wave animations, tidal gradients, glass cards. One design system binding four platforms together."

**Highlight**: shared JWT auth, SBU domain restriction, Docker Compose one-command setup

---

### SLIDE 8 — Closing (1:47–2:00)
**Visual**: Seaport portal — all four platform cards visible

**Script**:
> "Ask. Connect. Study. Manage. One platform for every Seawolf. That's Seaport."

---

## Demo Flow (live demo order)

1. `localhost:3000` — Seaport landing, wave hero, hover platform cards
2. `/chat` — ask a real SBU question, show citation in response
3. `localhost:3001` — Sources tab → Evaluations tab (show pass/fail score)
4. `localhost:3002` — People tab, click a match card, show "Why you match"
5. `localhost:3003` — course → learning map → teach mode (one exchange)

---

## Key Numbers to Mention

| Stat | Value |
|---|---|
| SBU data chunks | 22,000+ |
| Seeded alumni profiles | 50+ |
| Supported study file types | PDF, DOCX, PPTX, TXT, code files |
| AI providers supported | 4 (mock, local Ollama, OpenAI, AWS Bedrock) |
| Total platforms | 4 (portal + 3 apps) |
| Shared backend | 1 FastAPI + PostgreSQL + pgvector |

---

## Judging Criteria Checklist

- [x] **AI/ML integration** — RAG (pgvector + LLM), alumni matching (embedding + reranking), Socratic teaching (prompt engineering), AI title generation
- [x] **Design / Water Theme** — hero-bg wave CSS animation, bubbles, wave SVG dividers, teal/cyan/sky color system across all 4 apps
- [x] **Technical complexity** — multi-stage RAG, two-stage alumni matching, PDF parsing pipeline, evaluation framework
- [x] **Real-world usefulness** — each app solves a real SBU user problem (student / graduate / admin)
- [x] **Full-stack implementation** — Next.js App Router + FastAPI + PostgreSQL, Docker Compose, JWT auth, Alembic migrations
- [x] **Admin / content management** — source CRUD, crawl/reindex jobs, FAQ overrides, conversation review, evaluation runner
- [x] **Presentation clarity** — 4 platforms shown in 2 minutes with live demo flow
