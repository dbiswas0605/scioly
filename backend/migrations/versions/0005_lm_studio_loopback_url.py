"""Use the LM Studio Compose service for saved loopback defaults.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-07
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LOOPBACK_URLS = (
    "http://localhost:1234",
    "http://localhost:1234/",
    "http://localhost:1234/v1",
    "http://localhost:1234/v1/",
    "http://127.0.0.1:1234",
    "http://127.0.0.1:1234/",
    "http://127.0.0.1:1234/v1",
    "http://127.0.0.1:1234/v1/",
)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            UPDATE llm_providers
            SET base_url = 'http://lm-studio:1234/v1'
            WHERE provider_key = 'lm_studio'
              AND base_url = ANY(:loopback_urls)
            """
        ).bindparams(loopback_urls=list(_LOOPBACK_URLS))
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
