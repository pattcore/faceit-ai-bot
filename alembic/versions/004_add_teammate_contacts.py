"""Create teammate_profiles table with contact fields

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
    # Create teammate_profiles table for teammate search / party finder
    op.create_table(
        "teammate_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("faceit_nickname", sa.String(length=100), nullable=True),
        sa.Column("elo", sa.Integer(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=True),
        sa.Column("roles", sa.String(length=255), nullable=True),
        sa.Column("languages", sa.String(length=50), nullable=True),
        sa.Column("preferred_maps", sa.String(length=255), nullable=True),
        sa.Column("play_style", sa.String(length=50), nullable=True),
        sa.Column("voice_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("about", sa.String(length=500), nullable=True),
        sa.Column("availability", sa.String(length=255), nullable=True),
        sa.Column("discord_contact", sa.String(length=100), nullable=True),
        sa.Column("telegram_contact", sa.String(length=100), nullable=True),
        sa.Column("contact_url", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_teammate_profiles_id", "teammate_profiles", ["id"])
    op.create_index("ix_teammate_profiles_user_id", "teammate_profiles", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_teammate_profiles_user_id", table_name="teammate_profiles")
    op.drop_index("ix_teammate_profiles_id", table_name="teammate_profiles")
    op.drop_table("teammate_profiles")
