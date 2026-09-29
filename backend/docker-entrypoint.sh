#!/usr/bin/env bash
# Waits for Postgres, applies migrations, seeds baseline data (idempotent —
# safe on every restart), then runs whatever CMD was passed (uvicorn).
set -euo pipefail

echo "Waiting for Postgres..."
python -c "
import sys
import time

from sqlalchemy import create_engine, text

from app.config import get_settings

engine = create_engine(get_settings().database_url)
for attempt in range(30):
    try:
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        break
    except Exception as exc:
        print(f'  ...not ready yet ({exc.__class__.__name__}), retrying', file=sys.stderr)
        time.sleep(2)
else:
    print('Postgres did not become ready in time', file=sys.stderr)
    sys.exit(1)
"
echo "Postgres is up."

echo "Running database migrations..."
alembic upgrade head

echo "Seeding baseline data (subjects/settings/LLM provider rows — safe to re-run)..."
python scripts/seed.py

echo "Starting application..."
exec "$@"
