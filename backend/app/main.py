"""FastAPI application entrypoint for the scioly backend."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    admin,
    attempts,
    health,
    papers,
    questions,
    reports,
    students,
    subjects,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("scioly")

settings = get_settings()

app = FastAPI(title="Scioly API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_disallowed_origins(request: Request, call_next):
    """A request whose Origin isn't in CORS_ORIGINS still gets processed
    normally server-side (CORSMiddleware just omits the
    Access-Control-Allow-Origin header on the response) — the browser is
    what blocks it, silently, with no server-visible error. That makes CORS
    misconfiguration invisible in the logs unless we say so explicitly here.
    This is the most likely cause of a frontend action failing with "could
    not reach the server" right after a fresh deploy (wrong CORS_ORIGINS,
    or the site being loaded from a different host/port than configured).
    """
    origin = request.headers.get("origin")
    if origin and origin not in settings.cors_origins:
        logger.warning(
            "CORS: request from Origin '%s' is NOT in CORS_ORIGINS %s — the "
            "browser will block this response even though the request "
            "below succeeds server-side. Add this origin to CORS_ORIGINS "
            "and restart the backend if this is unexpected.",
            origin,
            settings.cors_origins,
        )
    return await call_next(request)

app.include_router(health.router, prefix="/api")
app.include_router(subjects.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(attempts.router, prefix="/api")
app.include_router(attempts.paper_router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
