"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- subjects -----------------------------------------------------
    op.create_table(
        "subjects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subjects")),
    )
    op.create_index(
        "ix_subjects_lower_name",
        "subjects",
        [sa.text("lower(name)")],
        unique=True,
    )

    # --- question_papers -----------------------------------------------
    op.create_table(
        "question_papers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_content_type", sa.String(length=100), nullable=False),
        sa.Column("source_file", postgresql.BYTEA(), nullable=False),
        sa.Column("source_file_size_bytes", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "default_duration_minutes",
            sa.Integer(),
            nullable=False,
            server_default="30",
        ),
        sa.Column(
            "total_questions", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_papers")),
        sa.ForeignKeyConstraint(
            ["subject_id"],
            ["subjects.id"],
            name=op.f("fk_question_papers_subject_id_subjects"),
            ondelete="RESTRICT",
        ),
        sa.CheckConstraint(
            "status IN ('draft','pending_review','published','archived')",
            name=op.f("ck_question_papers_status_valid"),
        ),
    )
    op.create_index(
        "ix_question_papers_subject_id", "question_papers", ["subject_id"]
    )
    op.create_index("ix_question_papers_status", "question_papers", ["status"])

    # --- questions -------------------------------------------------------
    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_number", sa.Integer(), nullable=False),
        sa.Column("question_type", sa.String(length=20), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("prompt_image", postgresql.BYTEA(), nullable=True),
        sa.Column(
            "prompt_image_content_type", sa.String(length=100), nullable=True
        ),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("short_answer_expected", sa.Text(), nullable=True),
        sa.Column(
            "points",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            server_default="1.0",
        ),
        sa.Column("llm_suggested_answer", sa.Text(), nullable=True),
        sa.Column(
            "is_reviewed", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["question_papers.id"],
            name=op.f("fk_questions_paper_id_question_papers"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "question_type IN ('mcq','short_answer')",
            name=op.f("ck_questions_question_type_valid"),
        ),
        sa.UniqueConstraint(
            "paper_id",
            "question_number",
            name="uq_questions_paper_question_number",
        ),
    )
    op.create_index("ix_questions_paper_id", "questions", ["paper_id"])

    # --- question_options -------------------------------------------------
    op.create_table(
        "question_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_label", sa.String(length=10), nullable=False),
        sa.Column("option_text", sa.Text(), nullable=True),
        sa.Column("option_image", postgresql.BYTEA(), nullable=True),
        sa.Column(
            "option_image_content_type", sa.String(length=100), nullable=True
        ),
        sa.Column(
            "is_correct", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column(
            "display_order", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_options")),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name=op.f("fk_question_options_question_id_questions"),
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "question_id",
            "option_label",
            name="uq_question_options_question_option_label",
        ),
    )
    op.create_index(
        "ix_question_options_question_id", "question_options", ["question_id"]
    )

    # --- students ----------------------------------------------------------
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
    )
    op.create_index(
        "ix_students_lower_display_name",
        "students",
        [sa.text("lower(display_name)")],
        unique=True,
    )

    # --- exam_attempts -------------------------------------------------------
    op.create_table(
        "exam_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("paper_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="in_progress",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_minutes_snapshot", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("correct_count", sa.Integer(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_exam_attempts")),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["students.id"],
            name=op.f("fk_exam_attempts_student_id_students"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["paper_id"],
            ["question_papers.id"],
            name=op.f("fk_exam_attempts_paper_id_question_papers"),
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "status IN ('in_progress','submitted','timed_out','abandoned')",
            name=op.f("ck_exam_attempts_status_valid"),
        ),
        sa.UniqueConstraint(
            "student_id",
            "paper_id",
            "attempt_number",
            name="uq_exam_attempts_student_paper_attempt_number",
        ),
    )
    op.create_index("ix_exam_attempts_student_id", "exam_attempts", ["student_id"])
    op.create_index("ix_exam_attempts_paper_id", "exam_attempts", ["paper_id"])
    op.create_index(
        "ix_exam_attempts_student_id_paper_id",
        "exam_attempts",
        ["student_id", "paper_id"],
    )

    # --- attempt_answers -------------------------------------------------------
    op.create_table(
        "attempt_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("attempt_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "selected_option_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("short_answer_text", sa.Text(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_attempt_answers")),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["exam_attempts.id"],
            name=op.f("fk_attempt_answers_attempt_id_exam_attempts"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["questions.id"],
            name=op.f("fk_attempt_answers_question_id_questions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["selected_option_id"],
            ["question_options.id"],
            name=op.f("fk_attempt_answers_selected_option_id_question_options"),
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "attempt_id",
            "question_id",
            name="uq_attempt_answers_attempt_question",
        ),
    )
    op.create_index(
        "ix_attempt_answers_attempt_id", "attempt_answers", ["attempt_id"]
    )
    op.create_index(
        "ix_attempt_answers_question_id", "attempt_answers", ["question_id"]
    )

    # --- llm_providers -------------------------------------------------------
    op.create_table(
        "llm_providers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider_key", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("api_key", sa.Text(), nullable=True),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default="false"
        ),
        sa.Column("extra_config", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_providers")),
        sa.UniqueConstraint(
            "provider_key", name=op.f("uq_llm_providers_provider_key")
        ),
    )
    op.create_index(
        "uq_llm_providers_single_active",
        "llm_providers",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    # --- app_settings -------------------------------------------------------
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column(
            "value_type",
            sa.String(length=20),
            nullable=False,
            server_default="string",
        ),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("key", name=op.f("pk_app_settings")),
        sa.CheckConstraint(
            "value_type IN ('string','integer','boolean','json')",
            name=op.f("ck_app_settings_value_type_valid"),
        ),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
    op.drop_index("uq_llm_providers_single_active", table_name="llm_providers")
    op.drop_table("llm_providers")
    op.drop_index("ix_attempt_answers_question_id", table_name="attempt_answers")
    op.drop_index("ix_attempt_answers_attempt_id", table_name="attempt_answers")
    op.drop_table("attempt_answers")
    op.drop_index(
        "ix_exam_attempts_student_id_paper_id", table_name="exam_attempts"
    )
    op.drop_index("ix_exam_attempts_paper_id", table_name="exam_attempts")
    op.drop_index("ix_exam_attempts_student_id", table_name="exam_attempts")
    op.drop_table("exam_attempts")
    op.drop_index(
        "ix_students_lower_display_name", table_name="students"
    )
    op.drop_table("students")
    op.drop_index(
        "ix_question_options_question_id", table_name="question_options"
    )
    op.drop_table("question_options")
    op.drop_index("ix_questions_paper_id", table_name="questions")
    op.drop_table("questions")
    op.drop_index("ix_question_papers_status", table_name="question_papers")
    op.drop_index("ix_question_papers_subject_id", table_name="question_papers")
    op.drop_table("question_papers")
    op.drop_index("ix_subjects_lower_name", table_name="subjects")
    op.drop_table("subjects")
