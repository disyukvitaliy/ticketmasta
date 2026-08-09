"""create events

Revision ID: 3b98821d43fb
Revises: 84d1dca64d18
Create Date: 2026-08-03 14:21:48.121829

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3b98821d43fb"
down_revision: Union[str, Sequence[str], None] = "84d1dca64d18"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("venue_id", sa.Integer, sa.ForeignKey("venues.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("events")
