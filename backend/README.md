# scioly backend

FastAPI backend for the scioly Science Olympiad practice-exam app.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Make sure Postgres is running (from the repo root):

```bash
docker compose up -d
```

Postgres listens on `localhost:5433` (not 5432) to avoid clashing with Postgres.app or other local installs — `.env.example` is already set up for this.

## Database migrations

```bash
alembic upgrade head
```

## Seed data

```bash
python scripts/seed.py
```

Safe to re-run — it only inserts rows that don't already exist.

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

- `GET /api/health` — DB connectivity check
- `GET /api/subjects`, `POST /api/subjects`
- `GET /api/papers`, `GET /api/papers/{id}`, `POST /api/papers/upload`
- `POST /api/papers/{paper_id}/parse` — sends the uploaded file to the active LLM provider and (re)creates the paper's questions/options, unreviewed
- `POST /api/papers/{paper_id}/publish` — marks a paper published once every question is reviewed
- `DELETE /api/papers/{paper_id}` — deletes a paper (any status) along with its questions/options and any student exam_attempts/attempt_answers (all cascade)
- `GET /api/papers/{paper_id}/questions`
- `PATCH /api/papers/{paper_id}/questions/{question_id}` — save a parent's edits and mark a question reviewed
- `POST /api/papers/{paper_id}/questions/confirm-all` — bulk-accept every question's current server-side state as reviewed ("Save & Confirm All" on the review screen); 400s listing which question numbers still need a correct answer marked, same check as `/publish`
- `PATCH /api/papers/{paper_id}/duration` — per-paper timer override, independent of the global default below
- `GET /api/students`, `POST /api/students`
- `GET /api/students/{student_id}/attempts` — all of one student's attempts across every paper (used to decorate Practice tiles with "already taken" + score)
- `POST /api/papers/{paper_id}/attempts` — start a timed attempt (get-or-creates the student by name)
- `GET /api/papers/{paper_id}/attempts?student_id=...` — attempt history for retake comparison
- `GET /api/attempts/{id}` — sanitized session (no correct answers) for taking/resuming an exam
- `POST /api/attempts/{id}/submit` — score it (mcq auto-graded; short_answer recorded ungraded) and reveal everything
- `GET /api/attempts/{id}/review` — re-fetch a finished attempt's full review
- `GET /api/admin/llm-providers`, `PUT /api/admin/llm-providers/{id}`
- `POST /api/admin/llm-providers/{id}/test` — connectivity/auth check, no completion spent
- `GET /api/admin/settings`, `PUT /api/admin/settings/{key}` — includes `default_exam_duration_minutes` (Admin → Timers), applied to newly uploaded papers via `admin_settings_crud.get_default_exam_duration_minutes`
- `GET /api/reports/students` — per-student overview (attempts, papers attempted, average score, last activity)
- `GET /api/reports/attempts` — per (student, paper) attempt history (`started_at`/`submitted_at` on each point — the frontend derives "time taken"), for the Parent/Teacher trend dashboard

## LLM parsing notes

`app/services/llm/dispatcher.py` is the entry point `/parse` calls. It tries every **enabled** `llm_providers` row in ascending `priority` order (lower number = tried first) and falls back to the next one if a provider fails — so e.g. a local Ollama/MLX provider can be preferred over a cloud one, with automatic fallback if it's unreachable. Any number of providers can be enabled at once; there's no single exclusive "active" provider anymore.

Four provider types are implemented:
- **`anthropic`** (`anthropic_parser.py`) — native PDF/image document support via the Anthropic SDK's tool-use.
- **`openai`**, **`ollama`**, **`mlx`** (`openai_compatible.py`) — all go through the OpenAI Python SDK's chat-completions + function-calling, pointed at either the real OpenAI API or a local `base_url`. We don't load Ollama/MLX models in-process — "local LLM support" means talking to whatever OpenAI-compatible server you already have running (Ollama exposes one natively at `/v1`; MLX needs a bridge like `mlx_lm.server`). PDFs go through text-only extraction (`pypdf`) on this path, since embedded images/diagrams are lost — Anthropic's native PDF support doesn't have that limitation.

Supported source file types for all providers: PDF, images, `.txt`, and `.docx` (via `python-docx`). Legacy `.doc` is rejected with a clear error — re-save as PDF or `.docx`.

Each provider row has `is_enabled`, `priority`, `model_name`, `base_url` (optional — defaults to `http://localhost:11434/v1` for Ollama and `http://localhost:8080/v1` for MLX if unset), and `api_key` (optional for Ollama/MLX, required for OpenAI/Anthropic). `POST /api/admin/llm-providers/{id}/test` does a cheap connectivity/auth check (`models.list()`) without spending tokens on a real completion.

## Tests

```bash
pytest
```
