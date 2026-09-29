"""Read-only aggregation query for the Parent/Teacher reports dashboard."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.exam_attempt import ExamAttempt
from app.models.question_paper import QuestionPaper


def list_all_attempts(db: Session) -> list[ExamAttempt]:
    """All exam attempts with student/paper/subject eagerly loaded, ordered
    so callers can group consecutively by (student, paper). This is
    home-tutoring scale (dozens of attempts, not millions) so grouping in
    Python is simpler and fine — no need for SQL-side aggregation."""
    return list(
        db.scalars(
            select(ExamAttempt)
            .options(
                joinedload(ExamAttempt.student),
                joinedload(ExamAttempt.paper).joinedload(QuestionPaper.subject),
            )
            .order_by(
                ExamAttempt.student_id,
                ExamAttempt.paper_id,
                ExamAttempt.attempt_number,
            )
        ).unique()
    )
