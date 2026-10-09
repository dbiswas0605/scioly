"""Idempotent seed script — safe to re-run.

Seeds:
- Subjects: Thermodynamics, Food Science, Crime Busters
- One demo student: "Demo Student"
- app_settings: default_exam_duration_minutes = 30 (integer)
- llm_providers: ollama, lm_studio, mlx, openai, anthropic — all disabled by
  default, with priorities that try local models before cloud ones.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.app_setting import AppSetting
from app.models.llm_provider import LlmProvider
from app.models.student import Student
from app.models.subject import Subject

SUBJECT_NAMES = ["Thermodynamics", "Food Science", "Crime Busters"]
DEMO_STUDENT_NAME = "Demo Student"


def seed_subjects(db) -> None:
    for name in SUBJECT_NAMES:
        existing = db.scalars(select(Subject).where(Subject.name.ilike(name))).first()
        if existing is None:
            db.add(Subject(name=name))
            print(f"  + created subject: {name}")
        else:
            print(f"  = subject already exists: {name}")


def seed_demo_student(db) -> None:
    existing = db.scalars(
        select(Student).where(Student.display_name.ilike(DEMO_STUDENT_NAME))
    ).first()
    if existing is None:
        db.add(Student(display_name=DEMO_STUDENT_NAME))
        print(f"  + created student: {DEMO_STUDENT_NAME}")
    else:
        print(f"  = student already exists: {DEMO_STUDENT_NAME}")


def seed_app_settings(db) -> None:
    key = "default_exam_duration_minutes"
    existing = db.get(AppSetting, key)
    if existing is None:
        db.add(
            AppSetting(
                key=key,
                value="30",
                value_type="integer",
                description="Default exam duration (minutes) for new question papers.",
            )
        )
        print(f"  + created app_setting: {key}")
    else:
        print(f"  = app_setting already exists: {key}")


LLM_PROVIDERS = [
    # Local providers get a lower priority number so they're tried before
    # cloud ones once enabled — dispatcher.py tries priority ascending.
    {
        "provider_key": "ollama",
        "display_name": "Ollama (local)",
        "model_name": "llama3.1",
        "base_url": "http://localhost:11434/v1",
        "priority": 10,
    },
    {
        "provider_key": "lm_studio",
        "display_name": "LM Studio (local)",
        "model_name": "",
        "base_url": "http://lm-studio:1234/v1",
        "priority": 15,
    },
    {
        "provider_key": "mlx",
        "display_name": "MLX (local)",
        "model_name": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
        "base_url": "http://localhost:8080/v1",
        "priority": 20,
    },
    {
        "provider_key": "openai",
        "display_name": "OpenAI",
        "model_name": "gpt-4o-mini",
        "base_url": None,
        "priority": 30,
    },
    {
        "provider_key": "anthropic",
        "display_name": "Anthropic Claude",
        "model_name": "claude-sonnet-5",
        "base_url": None,
        "priority": 40,
    },
]


def seed_llm_providers(db) -> None:
    for spec in LLM_PROVIDERS:
        provider_key = spec["provider_key"]
        existing = db.scalars(
            select(LlmProvider).where(LlmProvider.provider_key == provider_key)
        ).first()
        if existing is None:
            db.add(
                LlmProvider(
                    provider_key=provider_key,
                    display_name=spec["display_name"],
                    model_name=spec["model_name"],
                    base_url=spec["base_url"],
                    priority=spec["priority"],
                    is_enabled=False,
                    api_key=None,
                )
            )
            print(f"  + created llm_provider: {provider_key}")
        else:
            print(f"  = llm_provider already exists: {provider_key}")


def main() -> None:
    db = SessionLocal()
    try:
        print("Seeding subjects...")
        seed_subjects(db)
        print("Seeding demo student...")
        seed_demo_student(db)
        print("Seeding app settings...")
        seed_app_settings(db)
        print("Seeding LLM providers...")
        seed_llm_providers(db)
        db.commit()
        print("Seed complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
