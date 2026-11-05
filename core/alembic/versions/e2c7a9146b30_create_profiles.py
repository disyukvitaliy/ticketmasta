"""create profiles

Revision ID: e2c7a9146b30
Revises: b85a963e4f21
Create Date: 2026-11-04

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2c7a9146b30"
down_revision: Union[str, Sequence[str], None] = "b85a963e4f21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.BigInteger, nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", name="uq_profiles_user_id"),
    )


def downgrade() -> None:
    op.drop_table("profiles")
