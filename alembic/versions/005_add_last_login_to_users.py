"""Add last_login and login_count to users

Revision ID: 005
Revises: 004
Create Date: 2025-12-04

"""

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa


revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("last_login", sa.DateTime(), nullable=True))
    op.add_column(
        "users",
        sa.Column("login_count", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("users", "login_count")
    op.drop_column("users", "last_login")
