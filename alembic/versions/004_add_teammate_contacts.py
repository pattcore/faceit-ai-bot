"""Add contact fields to teammate_profiles

Revision ID: 004
Revises: 003
Create Date: 2025-12-01

"""

from alembic import op
import sqlalchemy as sa


revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add optional contact fields to teammate_profiles
    op.add_column(
        "teammate_profiles",
        sa.Column("discord_contact", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "teammate_profiles",
        sa.Column("telegram_contact", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "teammate_profiles",
        sa.Column("contact_url", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("teammate_profiles", "contact_url")
    op.drop_column("teammate_profiles", "telegram_contact")
    op.drop_column("teammate_profiles", "discord_contact")
