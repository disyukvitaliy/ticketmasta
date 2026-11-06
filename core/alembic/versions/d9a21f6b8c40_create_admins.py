"""create admins

Revision ID: d9a21f6b8c40
Revises: e2c7a9146b30
"""

import sqlalchemy as sa

from alembic import op

revision = "d9a21f6b8c40"
down_revision = "e2c7a9146b30"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admins",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password", sa.String(255)),
        sa.Column("active", sa.Boolean, nullable=False),
        sa.Column("fs_uniquifier", sa.String(64), nullable=False, unique=True),
    )
    op.create_table(
        "admin_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.String(255)),
    )
    op.create_table(
        "admins_roles",
        sa.Column("admin_id", sa.Integer, sa.ForeignKey("admins.id"), primary_key=True),
        sa.Column(
            "role_id", sa.Integer, sa.ForeignKey("admin_roles.id"), primary_key=True
        ),
    )


def downgrade():
    op.drop_table("admins_roles")
    op.drop_table("admin_roles")
    op.drop_table("admins")
