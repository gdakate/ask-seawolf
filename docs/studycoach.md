# StudyCoach — Design & Technical Specification

## One-Line Positioning

> "Not an answer engine — an AI study coach that teaches you *how* to learn, using your own course materials."

---

## Platform Context

StudyCoach is the third application in the **Ask Seawolves** platform suite, alongside:

| App | Purpose | Port |
|---|---|---|
| Ask Seawolves | RAG-powered SBU Q&A chatbot | :3000 |
| SB-lumni | AI-powered alumni matching & community | :3002 |
| **StudyCoach** | Adaptive AI study coach for SBU students | :3003 |

All three apps share the same FastAPI backend, PostgreSQL database, and visual design system.

---

## Problem Statement

Existing AI tools (ChatGPT, NotebookLM, etc.) give students direct answers. This:
- Bypasses actual learning
- Provides no personalization based on knowledge level
- Is disconnected from course-specific materials

StudyCoach is built on the opposite principle: **teach, don't solve**.

---

## Core Features (MVP)

### 1. Course Management
- Create a course with a course code and name (e.g., `CSE214 — Data Structures`)
- Upload any combination of course materials per course
- Supported file types: PDF, DOCX, PPTX, CSV, TXT, Markdown, and code files (`.py`, `.js`, `.java`, `.cpp`, `.ts`, etc.)
- Each file is parsed and split into **Sections** (chapter/slide/heading-based)

### 2. AI Learning Map
After upload, the AI automatically extracts:
- 5–8 key concepts per course material
- Prerequisite relationships between concepts
- Difficulty rating per concept (1–5)
- Assignment / exam relevance tags
- Suggested study order

### 3. Study Plan
- AI generates an initial weekly plan by parsing the syllabus (deadlines, exam dates, topics)
- Student can freely edit, add, or delete plan items via an interactive calendar UI
- Plan adjusts based on declared knowledge level and remaining time

### 4. Teaching Mode (Core Differentiator)
Each section starts with a **knowledge check**:

```
"How well do you know this concept?"
  [ I have no idea ]  [ I've heard of it ]  [ I know the basics ]
```

Response strategy adapts accordingly:

| Level | AI Response |
|---|---|
| No idea | Full concept explanation from course material → key points → example → mini quiz |
| Heard of it | Quick recap → why it matters → guided practice with hints |
| Know basics | Skip to application → problem-solving strategy → edge cases |

### 5. Problem-Solving Mode (Socratic Method)
When a student pastes in a problem:

1. AI identifies which concept(s) are required
2. Asks if the student knows those concepts
3. Gives **Hint 1** — direction only ("What data structure fits here?")
4. If stuck → **Hint 2** — more specific ("Think about access time: array vs. hashmap")
5. If still stuck → **Hint 3** — near-complete guidance
6. After solving → explains how the same pattern applies elsewhere

**The AI never gives a direct answer.** This is enforced at the system prompt level.

---

## Teaching Policy

The following rules are enforced in the LLM system prompt and cannot be overridden by user messages:

```
TEACHING RULES (non-negotiable):
1. Never provide a direct answer to a homework or exam problem.
2. Always identify the underlying concept before helping.
3. Use hints in stages — never skip to the answer.
4. All explanations must reference the student's own course materials when available.
5. After a student solves something, reinforce with a related concept or follow-up question.
6. If a student asks "just tell me the answer", respond with:
   "I'm here to help you learn it, not give it away. Let's work through it together."
```

### Intent → Response Mapping

| Student says | AI does |
|---|---|
| "What's the answer to this?" | Refuses → identifies concept → Hint 1 |
| "Explain this concept" | Full explanation from course material + example |
| "I'm stuck" | Diagnoses where → staged hints |
| "Check my work" | Points out what's wrong, not what's right |
| "Give me a quiz" | Generates practice questions from course material |
| "What should I study?" | Returns today's recommended focus based on plan + knowledge gaps |

---

## File Parsing Pipeline

```
Upload
  ↓
File type detection
  ↓
Parser (per type)
  ↓
Section splitting (by heading / slide / page)
  ↓
LLM → concept extraction + difficulty + prerequisites
  ↓
Stored as: CourseMaterial → Section → Concept
```

| Format | Parser | Section Logic |
|---|---|---|
| PDF | `pdfplumber` | Page breaks + heading detection |
| DOCX | `python-docx` | Heading levels (H1/H2) |
| PPTX | `python-pptx` | One section per slide |
| CSV | `pandas` | Column summary + data description |
| Code | Raw text | Function/class boundaries |
| TXT / MD | Raw text | Heading-based (`#`, `##`) |

---

## Data Model

```
StudyCoachUser
  id, email (@stonybrook.edu only), name, created_at

Course
  id, user_id, code, name, description, created_at

CourseMaterial
  id, course_id, filename, file_type, raw_text, parsed_at, status

Section
  id, material_id, title, order, content, difficulty (1–5)

Concept
  id, course_id, name, description, difficulty, prerequisites (concept_id[])

StudyPlanItem
  id, course_id, user_id, title, due_date, type (lecture/assignment/exam/review),
  is_completed, notes

TeachSession
  id, course_id, user_id, section_id, knowledge_level (none/partial/confident)

TeachMessage
  id, session_id, role (user/assistant), content, intent, created_at
```

---

## API Routes (FastAPI)

```
POST   /api/study/auth/register
POST   /api/study/auth/login

POST   /api/study/courses                    # create course
GET    /api/study/courses                    # list my courses
GET    /api/study/courses/{id}               # course detail + concepts

POST   /api/study/courses/{id}/upload        # upload file
GET    /api/study/courses/{id}/materials     # list materials
GET    /api/study/courses/{id}/sections      # all sections with difficulty

GET    /api/study/courses/{id}/plan          # get study plan
POST   /api/study/courses/{id}/plan          # add plan item
PUT    /api/study/plan/{item_id}             # edit plan item
DELETE /api/study/plan/{item_id}             # delete plan item

POST   /api/study/teach                      # start/continue teach session
GET    /api/study/teach/{session_id}/messages
```

---

## Frontend Pages

```
/                  Landing page
/login             SBU email login / register
/dashboard         All courses + today's top 3 tasks
/course/new        Create a course + upload files
/course/[id]       Course home: concept map, materials, difficulty overview
/course/[id]/teach/[sectionId]   Teaching mode (chat interface)
/course/[id]/plan  Study plan calendar (editable)
```

---

## Access Policy

- Registration restricted to `@stonybrook.edu` and `@alumni.stonybrook.edu` emails
- All course materials are private to the creating user
- JWT-based auth (same pattern as SB-lumni)

---

## Design System

Same as Ask Seawolves and SB-lumni:
- Tailwind CSS with SBU water/seawolf color palette (`water-current`, `water-shallow`, `water-abyss`)
- `glass-card` component style
- `btn-water` primary button
- Font: display font for headings, system sans for body
- Dark/light mode support via CSS variables

---

## Future: Brightspace Integration

Designed to support LMS sync as a non-breaking extension:

```
Current:  Student uploads files manually
Future:   NetID login → OAuth/scrape Brightspace
          → auto-ingest lecture slides, assignments, syllabi
          → auto-update study plan when new content is posted
```

The data model is already compatible — `CourseMaterial.source` can be extended to `"upload" | "brightspace"` without schema changes.

---

## What Makes This Different

| Feature | ChatGPT | NotebookLM | StudyCoach |
|---|---|---|---|
| Gives direct answers | Yes | Yes | **Never** |
| Uses your course materials | No | Yes | **Yes** |
| Adapts to knowledge level | No | No | **Yes** |
| Tracks learning progress | No | No | **Yes** |
| Generates study plans | No | No | **Yes** |
| Socratic hint system | No | No | **Yes** |
| SBU / LMS integration path | No | No | **Yes (planned)** |
