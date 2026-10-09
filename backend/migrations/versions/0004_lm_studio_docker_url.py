"""Point the LM Studio provider at its Compose service.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE llm_providers
            SET base_url = 'http://lm-studio:1234/v1'
            WHERE provider_key = 'lm_studio'
              AND (base_url IS NULL OR base_url = 'http://localhost:1234/v1')
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE llm_providers
            SET base_url = 'http://localhost:1234/v1'
            WHERE provider_key = 'lm_studio'
              AND base_url = 'http://lm-studio:1234/v1'
            """
        )
    )
