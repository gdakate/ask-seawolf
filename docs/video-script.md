# Seaport — Video Script (Final)

> **Record: ~3 minutes → export → play at 1.5x → submits as 2 min**
> Narrate clearly at normal pace. At 1.5x it'll sound brisk but intelligible.
> Judges see ONLY this video — every evaluation criterion must appear.

---

## FULL NARRATION + SCREEN GUIDE

---

### [0:00–0:25] PROBLEM + HOOK  *(record ~38 sec)*
**Screen**: Seaport portal hero — wave animation playing, bubbles rising. Slow scroll down to platform cards.

> *"SBU students have three unsolved problems. First — they can't get instant, reliable answers about university policies without digging through outdated web pages. Second — graduates lose their entire campus network the moment they leave. Third — when students turn to AI tools like ChatGPT for studying, they just get the answer handed to them. No real learning happens.*
>
> *We built Seaport. One platform. Four tools. Designed for every stage of the Seawolf journey."*

---

### [0:25–0:45] ARCHITECTURE OVERVIEW  *(record ~30 sec)*
**Screen**: Show a clean architecture diagram. Can be a slide or drawn diagram — not the live app.

```
[ Seaport Portal :3000 ] [ Admin :3001 ] [ SB-lumni :3002 ] [ StudyCoach :3003 ]
                              ↓ all share ↓
                    FastAPI Backend :8000
                    PostgreSQL + pgvector
                    Redis  |  File Storage
```

> *"The backend is a single FastAPI server shared across all four Next.js applications. One PostgreSQL database with pgvector for semantic search. One JWT auth system restricted to stonybrook.edu and alumni.stonybrook.edu domains. One water-themed design system. Four distinct platforms."*

---

### [0:45–1:10] ASK SEAWOLF — TECH + DEMO  *(record ~38 sec)*
**Screen**: Open `/chat`, type the question, watch the answer stream in, point to citations

**Type this question:**
> `"What is the deadline to withdraw from a course without receiving a W grade?"`

> *"Ask Seawolf is a RAG pipeline built on 22,000 chunks crawled from stonybrook.edu. A question comes in — the system classifies intent, retrieves the top chunks using pgvector cosine similarity, reranks them by source authority score, and synthesizes a grounded answer using the LLM.*
>
> *Every answer comes with citations. The system also detects when a question needs a real person — and routes to the appropriate office automatically."*

**Point to**: citation links below the answer.

---

### [1:10–1:30] ADMIN DASHBOARD — TECH + DEMO  *(record ~30 sec)*
**Screen**: `localhost:3001` — Sources tab (5 sec) → Evaluations tab (10 sec, point to scores) → Conversations tab (5 sec)

> *"The admin dashboard gives operators full control over the knowledge base — no code required. They can add or disable sources, trigger crawl and reindex jobs, inspect every chunk in the vector store, and curate FAQ overrides that bypass RAG entirely for guaranteed-accurate answers.*
>
> *Most importantly: the evaluation runner. Admins run structured SBU Q&A test suites and see pass/fail rates and per-case scores. It's a complete LLM quality loop built into the product."*

---

### [1:30–1:48] SB-LUMNI — TECH + DEMO  *(record ~27 sec)*
**Screen**: SB-lumni People tab → hover/click a match card → show "Why you match"

> *"SB-lumni connects Stony Brook graduates through a two-stage AI matching pipeline. Stage one: approximate nearest-neighbor retrieval using pgvector on profile, skills, and interest embeddings. Stage two: multi-signal reranking across major overlap, career path, skills Jaccard similarity, and graduation year proximity — with MMR diversity selection to keep results varied.*
>
> *Every match card shows exactly why you're compatible, in plain English."*

---

### [1:48–2:25] STUDYCOACH — TECH + DEMO  *(record ~55 sec — most time here)*
**Screen**: Course page → per-material learning map (show section titles) → click a section → Teach mode → show 2 chat exchanges

> *"StudyCoach is the most technically distinct platform in Seaport. When a student uploads lecture slides, our parsing pipeline reads the PDF page by page, groups pages into concept clusters, and calls the LLM to generate descriptive section titles — not raw page content. The result is a structured, readable learning map."*

*(cut to teach mode chat)*

> *"In teach mode, the AI operates under a strict Socratic system prompt. One concept per message. Three to five sentences. One question at the end. It is not allowed to just give the answer.*
>
> *Students can review their session history, resume a past session, or start fresh. The goal isn't answer retrieval — it's building actual understanding."*

**Show this exchange** (pre-set up before recording):
- Type: `"I'm a beginner. Can you teach me the first concept?"`
- AI responds with: short concept explanation + one question
- Type: `"I think it means..."` (any partial answer)
- AI responds: acknowledges + follows up with next idea

---

### [2:25–2:35] CLOSING  *(record ~15 sec)*
**Screen**: Seaport portal — slow scroll from hero to platform cards

> *"Ask. Manage. Connect. Study. One platform for the entire Seawolf lifecycle. This is Seaport."*

---

> **Total recorded: ~3 min 13 sec → at 1.5x = ~2 min 8 sec**
> Trim intro/outro slightly if over 2 min after speed-up.

---

## DEMO QUESTIONS CHEAT SHEET

### Ask Seawolf — Best test questions (these get strong RAG answers)

| Question | Why it's good |
|---|---|
| `"What are the requirements to apply for in-state tuition status?"` | Multi-source, shows citations + office routing |
| `"How do I apply for financial aid as a transfer student?"` | Triggers bursar + financial aid sources |
| `"What is the deadline to withdraw from a course without a W grade?"` | Specific policy, date-based, shows precision |
| `"Where is the Student Health Center and what are its hours?"` | Location + hours = tests structured data retrieval |
| `"What GPA do I need to stay off academic probation?"` | Academic policy — shows confidence score well |

### SB-lumni — What makes a good demo
- Log in as `wolfie@stonybrook.edu` / `12345678`
- Go to **People** tab — show the match cards
- Click any card — point to the **"Why you match"** section
- Optional: show the **Feed** tab with posts + hashtags

### StudyCoach — What makes a good demo
- Have a course pre-created with a real PDF uploaded (lecture slides work best)
- Show the **learning map** tab — sections with AI-generated titles (not "Page 1 content")
- Go to **Teach** mode → select a section
- Type something simple like `"Can you teach me this?"` or `"I'm a beginner, start from the basics"`
- Show the AI's response: short, conversational, ends with a question
- Type a short reply — show the follow-up

### Admin — What makes a good demo
- Go to **Sources** — show the list of SBU URLs with categories and authority scores
- Click **Evaluations** — show the test results table (pass/fail per case, scores)
- Briefly show **Conversations** — click one session to show full message thread

---

## EVALUATION CRITERIA → WHERE THEY APPEAR IN VIDEO

| Criterion | Timestamp | What's shown |
|---|---|---|
| Problem statement | 0:00–0:18 | Narration over hero |
| AI / ML integration | 0:32–0:52, 1:08–1:22, 1:22–1:50 | RAG, matching pipeline, Socratic prompt |
| Design / Water theme | 0:00–0:18, 1:50–2:00 | Wave hero, platform cards |
| Technical complexity | 0:18–0:32 | Architecture diagram |
| Admin / content mgmt | 0:52–1:08 | Sources, eval runner |
| Full-stack impl | 0:18–0:32 | Architecture narration |
| Differentiation | 0:00–0:18, 1:22–1:50 | Problem hook, Socratic teaching explanation |
| Real-world usefulness | throughout | Each platform solves a real SBU problem |

---

## RECORDING TIPS

1. **Record each section separately** — one recording per platform, edit together
2. **Pre-load tabs** before recording — no loading spinners on camera
3. **Browser zoom: 90%** — shows more UI on screen
4. **For StudyCoach teach mode** — pre-type the first message, show mid-conversation (not setup)
5. **Narrate at ~2.5 words/sec** — slower than you think, give visuals room to breathe
6. **Tools**: QuickTime screen recording + mic, iMovie or CapCut to cut and join
7. **Optional**: add a subtle lo-fi background track at ~20% volume
