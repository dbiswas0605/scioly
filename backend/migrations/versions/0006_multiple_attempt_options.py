"""Store every selected option for an exam answer.

Revision ID: 0006
Revises: 0005
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "attempt_answer_options",
        sa.Column("attempt_answer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("option_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["attempt_answer_id"],
            ["attempt_answers.id"],
            name="fk_attempt_answer_options_attempt_answer_id_attempt_answers",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["option_id"],
            ["question_options.id"],
            name="fk_attempt_answer_options_option_id_question_options",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "attempt_answer_id",
            "option_id",
            name="pk_attempt_answer_options",
        ),
    )
    op.create_index(
        "ix_attempt_answer_options_option_id",
        "attempt_answer_options",
        ["option_id"],
    )
    op.execute(
        """
        INSERT INTO attempt_answer_options (attempt_answer_id, option_id)
        SELECT id, selected_option_id
        FROM attempt_answers
        WHERE selected_option_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index(
        "ix_attempt_answer_options_option_id",
        table_name="attempt_answer_options",
    )
    op.drop_table("attempt_answer_options")
