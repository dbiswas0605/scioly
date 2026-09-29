# Deploying to a Raspberry Pi (Debian 13 "trixie", arm64)

This runs the **entire app in Docker** — Postgres, the FastAPI backend, and
the Next.js frontend, all as containers — using `docker-compose.prod.yml`.
This is a separate file from the root `docker-compose.yml`, which is
Postgres-only and meant for local development.

Tested end-to-end on this repo (build, migrate, seed, SSR-to-backend over
the internal Docker network, and Postgres data surviving a full
`down`/`up` cycle) before writing these steps.

## 0. What you'll need

- A Raspberry Pi 5 running Debian 13 (trixie), on your network, with a way to SSH in.
- An external/USB drive mounted on the Pi for the database (recommended — the
  SD card is not a great place for a database that gets written to
  constantly; it wears out faster and is slower).
- The Pi's LAN IP address (or a hostname you can resolve on your network).

## 1. Install Docker on the Pi

SSH into the Pi, then install Docker Engine + the Compose plugin from
Docker's own apt repository (Debian's own `docker.io` package is often an
older version without everything Compose v2 needs):

```bash
# Remove any old/partial installs first
sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

If trixie isn't recognized yet in Docker's repo (`$VERSION_CODENAME` = `trixie`),
substitute `bookworm` in the `echo` line above — Debian 12's packages work
fine on trixie for Docker.

Let your user run Docker without `sudo`, then re-login (or reboot) for it to take effect:

```bash
sudo usermod -aG docker $USER
exit   # log back in, or reboot: sudo reboot
```

Verify:

```bash
docker --version
docker compose version
```

Docker's systemd service is enabled by default after this install, so containers
with `restart: unless-stopped` (which every service in this stack uses) will
come back up automatically after a reboot or power loss.

## 2. Prepare the database's persistent storage

Confirm your external drive is mounted, then create a directory for Postgres's data on it:

```bash
lsblk   # confirm your drive and its mount point, e.g. /mnt/ssd
mkdir -p /mnt/ssd/scioly-postgres-data
```

Use this exact path for `POSTGRES_DATA_DIR` in step 4. This is a **bind
mount** (a real directory, not a Docker-managed named volume) specifically
so the database survives container recreation and `docker compose down -v`,
and so you can back it up by just copying the directory (or, better, with
`pg_dump` — see **Backups** below).

## 3. Get the code onto the Pi

```bash
git clone <your-repo-url> scioly
cd scioly
```

(Or `scp -r` the repo from your dev machine if it isn't in git yet.)

## 4. Configure environment variables

```bash
cp .env.prod.example .env
```

Find the Pi's LAN IP:

```bash
hostname -I
```

Edit `.env` and fill in the values marked `REQUIRED`/example in
`.env.prod.example` — at minimum:

```bash
nano .env
```

- `POSTGRES_PASSWORD` — set this to something real, not the placeholder.
- `POSTGRES_DATA_DIR` — the path you created in step 2.
- `CORS_ORIGINS` — `http://<pi-ip>:3000` (or a hostname, if you've set one up).
- `NEXT_PUBLIC_API_BASE_URL` — `http://<pi-ip>:8000`.

**Why this matters:** `NEXT_PUBLIC_API_BASE_URL` is baked into the
frontend's browser-side code at *build* time — it's what your browser will
call directly from your laptop/phone. Get the IP wrong here and you'll need
to rebuild (`docker compose -f docker-compose.prod.yml build frontend`) to
fix it, restarting alone won't pick up a change to this value.

## 5. Build and start everything

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First run takes a few minutes (installing Python/Node dependencies and
compiling the frontend). Watch it:

```bash
docker compose -f docker-compose.prod.yml logs -f
```

You should see the backend wait for Postgres, run migrations, seed
baseline data (subjects, a demo student, disabled LLM provider rows), then
start `uvicorn`.

## 6. Verify

```bash
docker compose -f docker-compose.prod.yml ps          # all three should be "healthy" / "Up"
curl http://localhost:8000/api/health                   # {"status":"ok","db":"ok"}
```

From another device on your network, open `http://<pi-ip>:3000` in a browser.

## 7. Configure an LLM provider

API keys are **not** environment variables — they're stored in the
database and set through the UI (per the app's design). Go to
`http://<pi-ip>:3000/admin`, add your Anthropic/OpenAI key (or point at a
local Ollama/MLX server reachable from the Pi) under LLM Settings, enable
it, and hit "Test connection" before relying on it.

## Updating after a code change

```bash
cd scioly
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

This rebuilds only what changed and recreates those containers; Postgres
and its data are untouched.

## Backups

The app currently has **no automatic backup** — the earlier dev history of
this project includes a real incident where a UI bug led to deleted data
with no way to recover it, precisely because nothing was being backed up.
Don't skip this.

A simple daily `pg_dump` cron job:

```bash
mkdir -p ~/scioly-backups
crontab -e
```

Add a line (adjust the container name if you changed the compose project name):

```cron
0 3 * * * docker exec $(docker compose -f /home/pi/scioly/docker-compose.prod.yml -p scioly ps -q postgres) pg_dump -U scioly scioly | gzip > /home/pi/scioly-backups/scioly-$(date +%Y%m%d).sql.gz
```

Restore from one of these with:

```bash
gunzip -c scioly-YYYYMMDD.sql.gz | docker exec -i <postgres-container> psql -U scioly -d scioly
```

## Security notes

This setup has **no authentication** (by design, per the app's current
scope) and exposes the backend and frontend on your LAN. Don't port-forward
these to the public internet as-is. If you need remote access, put it
behind a VPN (e.g. Tailscale/WireGuard) rather than opening ports on your
router.

## Troubleshooting

- **`docker compose` command not found**: you likely installed the old
  `docker-compose` (v1, hyphenated). This project uses v2 syntax
  (`docker compose`, no hyphen) — reinstall via step 1.
- **Backend container keeps restarting**: `docker compose -f docker-compose.prod.yml logs backend` —
  most likely Postgres isn't healthy yet (check `docker compose -f docker-compose.prod.yml ps`) or
  `DATABASE_URL`/`.env` values don't match.
- **A page or action fails with "Could not reach the server..." or a specific
  action (e.g. saving a question, deleting a paper) fails with a generic
  error**: this is the app's own error message for a failed network
  request — it now tells you *why* (see below), instead of a bare "Could
  not save this question." style message from earlier versions.
  1. First check `docker compose -f docker-compose.prod.yml logs backend` for a line starting
     `WARNING scioly: CORS: request from Origin '...' is NOT in CORS_ORIGINS ...`.
     **This is the single most common cause after a fresh deploy**: you're
     browsing to an address (an IP, a `.local` hostname, etc.) that doesn't
     exactly match what's in `CORS_ORIGINS`. The request actually succeeds
     server-side (you'll see a `200 OK` right after the warning) — the
     *browser* silently blocks the response because of the mismatch, which
     is why it looks like nothing happened. Fix: set `CORS_ORIGINS` in
     `.env` to the exact address shown in your browser's address bar, then
     `docker compose -f docker-compose.prod.yml up -d backend` (no rebuild needed, it's just an env var).
  2. If there's no CORS warning, check `BACKEND_INTERNAL_URL` resolves from
     inside the frontend container — `docker compose -f docker-compose.prod.yml exec frontend wget -qO- http://backend:8000/api/health`.
     If that works but the browser still fails, `NEXT_PUBLIC_API_BASE_URL` was
     probably wrong at *build* time — fix `.env` and rebuild:
     `docker compose -f docker-compose.prod.yml build frontend && docker compose -f docker-compose.prod.yml up -d frontend`.
  3. If backend logs show a Python traceback instead, that's a real
     server-side bug — the traceback (not just the last line) is what to
     share/investigate; the error message in the UI is deliberately generic
     for a genuine 500 (avoids leaking internals), but the container log has
     the full detail.
- **"Set POSTGRES_DATA_DIR in .env to a real host path"**: that directory
  doesn't exist yet, or `.env` wasn't found — `docker compose` reads `.env`
  from the current directory, so run these commands from the repo root.
