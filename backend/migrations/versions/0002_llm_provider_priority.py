"""llm_providers: replace single-active flag with enabled + priority

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "llm_providers",
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "llm_providers",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
    )

    # Carry over the old single-active flag before dropping it.
    op.execute("UPDATE llm_providers SET is_enabled = is_active")
    op.execute(
        "UPDATE llm_providers SET priority = 40 WHERE provider_key = 'anthropic'"
    )

    op.drop_index("uq_llm_providers_single_active", table_name="llm_providers")
    op.drop_column("llm_providers", "is_active")


def downgrade() -> None:
    op.add_column(
        "llm_providers",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.execute("UPDATE llm_providers SET is_active = is_enabled")
    op.create_index(
        "uq_llm_providers_single_active",
        "llm_providers",
        ["is_active"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
    op.drop_column("llm_providers", "priority")
    op.drop_column("llm_providers", "is_enabled")
