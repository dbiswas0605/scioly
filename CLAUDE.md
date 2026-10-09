# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this app is

A web based practice/mock-exam tool for Science Olympiad-style questions for home tutoring students.

The appliction will have 3 sections:

# 1. Student Section:
- Take practice exams built from questions stored in Postgres (MCQ and short-answer), via `/practice`.
- Students should be able to select a new test paper or redo a previously attempted question set.
- Once the test starts ( The student must click a button calles Take Exam) a countdown timer starts.
- Finally when the exam finishes (If there is a time out or student hits Submit Exam) the final score will be displayed.
- If this is a new test, Student should be able to review their answers against what they choose as correct answer in GREEN. If they choose a wrong answer Their choice should be displayed as RED and a GREEN checkbox should appear against the correct answer. There should be a section for explaining the correct answer in all the cases.
- If a student retakes an exam it should show the comparison from previous score and new score.

# 2. Parent/Teacher Section:
- Upload a new question paper as a PDF, doc, docx, text file or images via `/upload`, which is parsed and inserted into the database.
- The upload workflow will ask the parent on Question Paper Subject. Show a dropdown list of previously uploaded subject or have a add new Subject.
- The appliction will parse the PDF and would break down the questions and answer options for review before writing to the database.
- The application would need LLM to read and understand the questions. It may also suggest the correct answer to be stored in the DB for evaluation.
- The questions may contain the images, graphs and diagrams, keep then as is.
- The Parent's section should have a dashboard to see the student exam trends and historical score and number of test attempts. The dashboard should show each attemps and the score.


# 3. Admin Section:
  - The Admin section will show reports for previously imported questions. It should maintain the original question document uploaded in pdf, word etc for reference.
  - Admin section should let update the question, entire test paper or update the option choices and mark correct answers.
  - The Admin section will let user select the LLM model (claude or local llm     details in OLLAMA or OMLX). The LLM model would be used while uploading the PDF.
  - The Admin can setup a timer for each test.


## Architecture and UI Consideration
  - Make the UI very modern.
  - The application should be maintainable.
  - You decide the best database schema and structure.
  - The API Key for Anthropic will be stored in Database.
  - All the admin settings should be database driven.

## Confirmed Architecture Decisions

- **Frontend**: Next.js (TypeScript, App Router) in `frontend/`, talking to the backend over HTTP/JSON.
- **Backend**: separate Python FastAPI service in `backend/`, not part of the Next.js app.
- **Database**: Postgres, run locally via Docker Compose. **Listens on host port `5433`, not the default 5432** (5432 was already taken by a local Postgres.app install on the dev machine). `.env.example` files already reflect this — don't change it back to 5432 without checking the target machine first.
- **File/image storage**: original uploaded documents (PDF/doc/docx/images) and any question/option images are stored as **binary directly in Postgres** (`BYTEA` columns with a sibling `*_content_type` column) — no filesystem or S3 store.
- **Auth**: none yet. Role (student / parent-teacher / admin) is chosen client-side via a role switcher (persisted to `localStorage`, no cookies/sessions/login). A lightweight `students` table exists (no passwords) purely so exam attempts can be grouped per student for the parent dashboard.
- **LLM integration**: five provider types — `anthropic`, `openai`, `ollama`, `lm_studio`, `mlx` — are configured as rows in the `llm_providers` table (DB-driven, admin-editable via Admin → LLM Settings): model name, API key (optional for local providers), base URL, `is_enabled`, and `priority`. **Any number of providers can be enabled at once** — `backend/app/services/llm/dispatcher.py` tries enabled providers in ascending priority order (lower number tried first) and falls back to the next on failure, so e.g. a local Ollama/LM Studio/MLX provider can be preferred over cloud ones with automatic fallback if it's unreachable. Anthropic gets native PDF/image document support; OpenAI and local providers all go through one OpenAI-compatible chat-completions + function-calling path (`openai_compatible.py`) — for those, PDFs are text-extracted (`pypdf`), losing embedded images/diagrams. LM Studio runs in a LinuxServer Docker container (x86-64 image; ARM64 hosts require emulation) and is reached from the backend at `http://lm-studio:1234/v1`; Ollama and MLX can also run as separate local services.

## Repository Layout

```
scioly/
├── CLAUDE.md
├── README.md               # quickstart for both services
├── docker-compose.yml      # Postgres only; backend/frontend run locally during dev
├── .env.example            # Postgres creds/port for docker-compose
├── backend/                # FastAPI app — see backend/README.md
└── frontend/               # Next.js app
```

## Database Schema Summary

9 tables (UUID PKs, `snake_case`, Alembic-managed via `backend/migrations/`):
`subjects`, `question_papers` (holds the original uploaded file as `BYTEA` + status lifecycle `draft → pending_review → published → archived`), `questions` (mcq/short_answer, optional prompt image, explanation text), `question_options` (mcq choices, `is_correct` flag, optional image), `students`, `exam_attempts` (score/duration snapshots so later edits don't retroactively change past attempts), `attempt_answers`, `llm_providers` (partial unique index ensures at most one `is_active` provider at a time), `app_settings` (generic key/value config, e.g. default exam duration).

Full column-level detail lives in `backend/app/models/` (source of truth) and `backend/migrations/versions/0001_initial_schema.py`.

## Current Implementation Status

**Done:**
- Full DB schema + migrations + idempotent seed script (`backend/scripts/seed.py`).
- FastAPI CRUD for subjects, papers (incl. binary upload), students, and DB-driven admin settings/LLM provider config.
- Next.js shells for `/practice`, `/upload`, `/admin` with a shared typed API client (`frontend/src/lib/api/`), styled with Tailwind + shadcn/ui. No role-switcher UI (removed per user request) — the landing page's role cards just deep-link into each section.
- **Upload → LLM parsing → review → publish workflow**: `/upload` has a working upload form; `/papers/[paperId]` lets a parent trigger AI parsing (Anthropic Claude via tool-use), edit/confirm each parsed question (prompt, options, correct answer, explanation), and publish the paper once every question is reviewed. Backend: `POST /api/papers/{id}/parse`, `PATCH /api/papers/{id}/questions/{qid}`, `POST /api/papers/{id}/publish`.
- **Admin → LLM Settings**: real UI (`frontend/src/app/admin/LlmSettings.tsx`) to configure all five provider rows — model name, base URL, API key (write-only — never echoed back, only a `has_api_key` boolean is), an `Enabled` checkbox, and a numeric `priority` — plus a "Test connection" button (`POST .../test`) that checks auth/connectivity without spending a completion.

- **Practice exam-taking flow**: `/practice` → subject → published papers → paper detail (name entry, past attempts, Take/Retake Exam) → `/practice/attempts/[id]` which is a timed exam while `status='in_progress'` (countdown from `duration_minutes_snapshot`, auto-submits as `timed_out` at zero) and becomes the review screen once submitted — correct options highlighted green with a checkmark, the student's wrong pick highlighted red, an explanation section on every question (with a fallback message if none was written), and a "Compared to your last attempt" card on retakes. Only `mcq` questions are auto-scored; `short_answer` is recorded but ungraded (shown side-by-side with the model answer). Backend: `app/routers/attempts.py`, `app/crud/exam_attempts.py`.
- Saving a question now requires exactly one correct option marked for `mcq` (both on the PATCH endpoint and, as defense-in-depth, on `publish`) — added after a real published paper slipped through with 3 of 4 questions missing a correct answer under the old validation.
- **Admin → Question Papers**: lists every uploaded paper (any status) with a delete button (confirm dialog first) — `DELETE /api/papers/{id}`. Deleting cascades to that paper's questions/options and any student exam_attempts/attempt_answers. Fixed a real bug here: `QuestionPaper.attempts` and `Question.attempt_answers` relationships were missing `passive_deletes=True`, so the ORM tried to null out `NOT NULL` FKs before delete instead of trusting the DB's `ON DELETE CASCADE` — deleting a paper with any attempt history used to 500.
- `frontend/src/app/admin/AdminPapers.tsx` uses **one shared, explicitly-controlled** `AlertDialog` (state: `pendingDelete`), not one per row. The first version used an uncontrolled dialog per row whose "Delete" button never closed the dialog or showed success feedback — real-world result: repeated clicks looked like nothing was happening, but each one was silently succeeding, and all 4 real papers in the dev DB got deleted with no backup to recover from. Don't regress to per-row uncontrolled dialogs for destructive actions in a list.
- **No backup strategy exists for the local Postgres** (`archive_mode` is off, no `pg_dump` snapshots). Worth setting up a simple periodic dump before this DB holds anything not easily re-creatable.

- **Parent/Teacher → Reports** (`/upload/reports`, linked from `/upload`): student overview (attempts, papers attempted, average score, last activity) plus, per (student, paper), a trend line chart across attempts when there are 2+ (single-hue SVG line chart, endpoint-labeled, native `<title>` hover — see `frontend/src/app/upload/reports/TrendChart.tsx`) with a same-pattern-as-review delta indicator ("+12% since first attempt"). Backend: `GET /api/reports/students`, `GET /api/reports/attempts` (`app/routers/reports.py`) — read-only aggregation over `exam_attempts`, grouped in Python (fine at this scale, no new tables).
- **Full Docker deployment** now exists (`docker-compose.prod.yml`, `backend/Dockerfile`, `frontend/Dockerfile`) — separate from the root `docker-compose.yml` (Postgres-only, for local dev). Postgres persists to a **bind-mounted** host directory (`POSTGRES_DATA_DIR`), not a named volume, on purpose (see the earlier data-loss incident above — this makes the DB trivially backup-able by just copying/`pg_dump`ing that directory). `frontend/src/lib/api/client.ts` uses two different base URLs on purpose: `NEXT_PUBLIC_API_BASE_URL` (baked in at build time, used by browser code) vs `BACKEND_INTERNAL_URL` (runtime-only, used by Server Component SSR fetches to reach the `backend` container directly instead of hairpinning through the host's public address). Full step-by-step (Raspberry Pi 5 / Debian 13, but generalizes) in `DEPLOY.md`. All of this was built AND tested end-to-end (build, migrate, seed, SSR-to-backend over the internal network, bind-mount persistence across a full `down`/`up`) in real containers before being documented — don't assume it's untested boilerplate.
- **Error surfacing overhaul**: every client-side action (save question, delete paper, upload, submit exam, LLM settings, etc. — ~13 files) used to fall back to a generic string like "Could not save this question." whenever the failure wasn't a clean API error response, which is exactly what a CORS block or unreachable backend looks like (browsers report these as an opaque `TypeError`, no detail). `frontend/src/lib/api/client.ts` now has a `NetworkError` class (thrown when `fetch` itself rejects, with a context-aware message — CORS hint in the browser, Docker-networking hint during SSR) and a shared `getErrorMessage(err, fallback)` helper used everywhere instead of ad-hoc `err instanceof ApiError ? ... : "..."` checks. Backend: `app/main.py` has a small middleware that logs a clear `WARNING` when a request's `Origin` isn't in `CORS_ORIGINS` — this case otherwise produces a normal `200` in the logs (CORS is enforced by the *browser*, not the server), making it look like nothing is wrong server-side while the UI silently fails. This was built specifically after a real Pi deployment hit exactly this failure mode.

- **Admin → Timers**: editable global default exam duration (`app_settings.default_exam_duration_minutes`, 30 by default), applied when a paper is uploaded. Each paper's timer can also be overridden individually in Admin → Question Papers (`PATCH /api/papers/{id}/duration`) — independent of the global default, which only affects *new* uploads.
- **Upload review → "Save & Confirm All"**: bulk-accepts every parsed question's current state as reviewed in one action (`POST /api/papers/{id}/questions/confirm-all`), instead of clicking "Save & confirm" on each `QuestionCard` individually. Same validation as `/publish` (every mcq needs exactly one correct option) — 400s with the specific question numbers if any aren't ready, rather than silently confirming broken ones.
- **Reports → time taken**: derived client-side from `started_at`/`submitted_at` (`frontend/src/lib/utils.ts`'s `formatDuration`) — no backend schema change needed, those fields already existed. Shown in the single-attempt text line, next to the trend chart's delta indicator, and in each trend-chart point's hover tooltip.
- **Practice tiles → attempted indicator**: `frontend/src/app/practice/subjects/[subjectId]/SubjectPapersGrid.tsx` (client component, since "have *I* taken this" depends on the localStorage-only student name) fetches `GET /api/students/{id}/attempts`, picks each paper's most recent scored attempt, and shows a green checkmark + score badge colored by threshold — emerald ≥95%, blue 90–95%, amber <90%.

**Not yet built (do not assume these exist):**
- A dedicated admin question-paper browser (the review screen at `/papers/[paperId]` currently doubles as editing UI).
- Any real authentication.
- Extracting images/diagrams out of uploaded papers into `prompt_image`/`option_image` — parsing is text-only for now (and PDFs specifically lose images entirely on the OpenAI/Ollama/MLX path, since that path text-extracts PDFs rather than sending native document blocks).
- Free-text grading/AI-scoring for `short_answer` questions.

## Running Locally

```bash
# 1. Database (from repo root)
cp .env.example .env
docker compose up -d

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
alembic upgrade head
python scripts/seed.py
uvicorn app.main:app --reload --port 8000

# 3. Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Frontend: http://localhost:3000 · Backend docs: http://localhost:8000/docs · Health check: `GET /api/health`.
