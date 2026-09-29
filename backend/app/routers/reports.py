"""Parent/Teacher reports dashboard: a per-student overview, and per
(student, paper) attempt trends for retake comparison."""
from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.crud import reports as reports_crud
from app.deps import get_db
from app.models.exam_attempt import ExamAttempt
from app.schemas.report import AttemptPoint, StudentOverview, StudentPaperReport

router = APIRouter(prefix="/reports", tags=["reports"])


def _percent(score: Decimal | None, max_score: Decimal | None) -> float | None:
    if score is None or max_score is None or max_score == 0:
        return None
    return round(float(score) / float(max_score) * 100, 1)


@router.get("/attempts", response_model=list[StudentPaperReport])
def get_attempt_reports(db: Session = Depends(get_db)) -> list[StudentPaperReport]:
    attempts = reports_crud.list_all_attempts(db)

    grouped: dict[tuple, list[ExamAttempt]] = defaultdict(list)
    for attempt in attempts:
        grouped[(attempt.student_id, attempt.paper_id)].append(attempt)

    reports = [
        StudentPaperReport(
            student_id=student_id,
            student_name=group[0].student.display_name,
            paper_id=paper_id,
            paper_title=group[0].paper.title,
            subject_name=group[0].paper.subject.name,
            attempts=[
                AttemptPoint(
                    attempt_id=a.id,
                    attempt_number=a.attempt_number,
                    status=a.status,
                    score=a.score,
                    max_score=a.max_score,
                    percent=_percent(a.score, a.max_score),
                    started_at=a.started_at,
                    submitted_at=a.submitted_at,
                )
                for a in group
            ],
        )
        for (student_id, paper_id), group in grouped.items()
    ]
    reports.sort(key=lambda r: (r.student_name.lower(), r.paper_title.lower()))
    return reports


@router.get("/students", response_model=list[StudentOverview])
def get_student_overviews(db: Session = Depends(get_db)) -> list[StudentOverview]:
    attempts = reports_crud.list_all_attempts(db)

    by_student: dict = defaultdict(list)
    for attempt in attempts:
        by_student[attempt.student_id].append(attempt)

    overviews = []
    for student_id, group in by_student.items():
        percents = [
            p for p in (_percent(a.score, a.max_score) for a in group) if p is not None
        ]
        overviews.append(
            StudentOverview(
                student_id=student_id,
                student_name=group[0].student.display_name,
                total_attempts=len(group),
                papers_attempted=len({a.paper_id for a in group}),
                average_percent=round(sum(percents) / len(percents), 1)
                if percents
                else None,
                last_activity=max((a.submitted_at or a.started_at) for a in group),
            )
        )
    overviews.sort(key=lambda o: o.student_name.lower())
    return overviews
