"""create ticket types

Revision ID: 97e023e70862
Revises: 3b98821d43fb
Create Date: 2026-08-09 13:53:55.370667

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "97e023e70862"
down_revision: Union[str, Sequence[str], None] = "3b98821d43fb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ticket_types",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("event_id", sa.Integer, sa.ForeignKey("events.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price_cents", sa.Integer, nullable=False),
        sa.Column("quantity", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ticket_types")


# ticket_holds
# - id
# - ticket_type_id
# - user_id
# - quantity
# - status               # active, completed, expired
# - expires_at
