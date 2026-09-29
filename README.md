# Scioly

A Science Olympiad practice/mock-exam tool for home tutoring students. See `CLAUDE.md` for full product requirements and current build status.

**Architecture:** Next.js (TypeScript) frontend + a separate Python FastAPI backend + Postgres. No authentication — a student/parent/admin picks their section from the home page.

- `frontend/` — Next.js app (`/practice`, `/upload`, `/upload/reports`, `/admin`)
- `backend/` — FastAPI app (see `backend/README.md` for the full API reference)
- `docker-compose.yml` — local Postgres only; the backend and frontend run directly on your machine during dev (this file, below)
- `docker-compose.prod.yml` — the **full containerized stack** (Postgres + backend + frontend) for actually hosting the app somewhere — see **[DEPLOY.md](./DEPLOY.md)** (written for a Raspberry Pi, but the steps generalize to any Linux host)

## Prerequisites

- [Docker](https://www.docker.com/) (for Postgres)
- Python 3.11+
- Node.js 20+

## 1. Database setup

The app needs one Postgres database. The easiest path is the bundled Docker Compose file; if you'd rather point at a database you already have (a different local Postgres, a cloud instance, etc.), skip to **Using your own Postgres** below.

### Option A — Docker Compose (recommended)

From the repo root:

```bash
cp .env.example .env
docker compose up -d
```

This starts a `postgres:16-alpine` container named `scioly-postgres` with a persistent named volume (`scioly_postgres_data`), using the credentials in `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `POSTGRES_USER` | `scioly` | DB role |
| `POSTGRES_PASSWORD` | `scioly_dev_password` | DB role password |
| `POSTGRES_DB` | `scioly` | database name |
| `POSTGRES_PORT` | `5433` | **host** port (mapped to the container's internal 5432) |

**Why port 5433, not 5432:** the default Postgres port is often already taken by a local Postgres.app or another Postgres install. `5433` avoids that collision. If `5433` is free and you'd rather use the standard port, change `POSTGRES_PORT` in `.env` before running `docker compose up -d` — just make sure `backend/.env`'s `DATABASE_URL` (below) uses the same port.

Check it's healthy:

```bash
docker compose ps
```

To stop it (data persists in the volume): `docker compose down`. To wipe the data and start clean: `docker compose down -v`.

### Option B — Using your own Postgres

If you already have a Postgres server (local, Docker, or hosted — e.g. Supabase/Neon/RDS), you don't need `docker-compose.yml` at all. Just:

1. Create a database and a role that can create tables in it.
2. Point `backend/.env`'s `DATABASE_URL` at it (see step 2 below) — the format is:
   ```
   postgresql+psycopg://<user>:<password>@<host>:<port>/<database>
   ```
3. Continue with the backend setup steps (migrations + seed) as normal.

## 2. Backend setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
```

Open `backend/.env` and confirm `DATABASE_URL` matches your database (the default already matches Option A above):

```
DATABASE_URL=postgresql+psycopg://scioly:scioly_dev_password@localhost:5433/scioly
CORS_ORIGINS=http://localhost:3000
ENV=development
```

Then run the migrations and seed some starter data (subjects, a demo student, default LLM provider rows — all disabled until you configure one in Admin):

```bash
alembic upgrade head
python scripts/seed.py
```

Both commands are safe to re-run.

Start the API:

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/api/health → `{"status":"ok","db":"ok"}`

See `backend/README.md` for the full endpoint list and LLM-provider notes.

## 3. Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

`.env.local` just needs to point at the backend:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

App: http://localhost:3000

## Verifying everything is wired up

1. `docker compose ps` — Postgres container healthy.
2. `curl http://localhost:8000/api/health` — `{"status":"ok","db":"ok"}`.
3. Open http://localhost:3000 — pick a section on the home page:
   - **Student** (`/practice`) — subjects load live from the database.
   - **Parent/Teacher** (`/upload`) — upload a question paper; there's also a **Reports** link for student scores/trends.
   - **Admin** (`/admin`) — configure an LLM provider (Anthropic/OpenAI/Ollama/MLX) here before trying "Parse with AI" on an uploaded paper.

## Common issues

- **Backend can't connect to Postgres**: confirm the container is running (`docker compose ps`) and that `backend/.env`'s `DATABASE_URL` port matches `docker-compose.yml`'s `POSTGRES_PORT` (both default to `5433`).
- **Port 5433 also taken**: change `POSTGRES_PORT` in the root `.env`, restart the container (`docker compose up -d`), and update `DATABASE_URL` in `backend/.env` to match.
- **Frontend shows "Could not reach the server"**: the backend isn't running, or `NEXT_PUBLIC_API_BASE_URL` in `frontend/.env.local` doesn't match where it's listening.
