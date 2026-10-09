"""Add the LM Studio OpenAI-compatible provider.

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-06
"""
from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            INSERT INTO llm_providers (
                id, provider_key, display_name, base_url, model_name,
                is_enabled, priority, created_at, updated_at
            )
            VALUES (
                :id, 'lm_studio', 'LM Studio (local)',
                'http://localhost:1234/v1', '', false, 15, now(), now()
            )
            ON CONFLICT (provider_key) DO NOTHING
            """
        ).bindparams(id=uuid.uuid4())
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM llm_providers WHERE provider_key = 'lm_studio'")
    )
