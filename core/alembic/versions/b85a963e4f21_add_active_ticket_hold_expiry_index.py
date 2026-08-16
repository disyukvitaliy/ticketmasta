"""add active ticket hold expiry index

Revision ID: b85a963e4f21
Revises: 05480976dd3d
Create Date: 2026-08-16 18:20:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b85a963e4f21"
down_revision: Union[str, Sequence[str], None] = "05480976dd3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_ticket_holds_active_expires_at_id",
        "ticket_holds",
        ["expires_at", "id"],
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("ix_ticket_holds_active_expires_at_id", table_name="ticket_holds")
