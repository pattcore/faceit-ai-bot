"""Add steam_id column to users

Revision ID: 003
Revises: 002
Create Date: 2025-11-27

"""

from alembic import op
import sqlalchemy as sa


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add steam_id column to users table (nullable, unique, indexed)
    op.add_column(
        "users",
        sa.Column("steam_id", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_users_steam_id", "users", ["steam_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_steam_id", table_name="users")
    op.drop_column("users", "steam_id")
