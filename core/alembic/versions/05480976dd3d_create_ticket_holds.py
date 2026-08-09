"""create ticket holds

Revision ID: 05480976dd3d
Revises: 97e023e70862
Create Date: 2026-08-09 14:02:15.370731

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "05480976dd3d"
down_revision: Union[str, Sequence[str], None] = "97e023e70862"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_holds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "ticket_type_id",
            sa.Integer,
            sa.ForeignKey("ticket_types.id"),
            nullable=False,
        ),
        sa.Column("user_id", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
        sa.Column("status", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_holds")
