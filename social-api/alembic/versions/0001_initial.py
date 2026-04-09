"""Initial migration — creates all tables.

Revision ID: 0001
Revises: 
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # platform enum
    platform_enum = sa.Enum("vk", "x", "telegram", "ok", "youtube", name="platform")
    platform_enum.create(op.get_bind(), checkfirst=True)

    # social_accounts
    op.create_table(
        "social_accounts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("platform", platform_enum, nullable=False),
        sa.Column("account_id", sa.String(255), nullable=False),
        sa.Column("account_name", sa.String(255), nullable=True),
        sa.Column("encrypted_token", sa.String(2048), nullable=True),
        sa.Column("token_type", sa.String(64), nullable=True, default="bearer"),
        sa.Column("refresh_token_encrypted", sa.String(2048), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("extra_data", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_social_accounts_user_id", "social_accounts", ["user_id"])

    # post status enum
    post_status_enum = sa.Enum("draft", "scheduled", "published", "failed", name="poststatus")
    post_status_enum.create(op.get_bind(), checkfirst=True)

    # posts
    op.create_table(
        "posts",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("media_urls", sa.JSON, nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", post_status_enum, nullable=False, server_default="draft"),
        sa.Column("platform_post_ids", sa.JSON, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_posts_user_id", "posts", ["user_id"])

    # post target status enum
    post_target_status_enum = sa.Enum("pending", "published", "failed", name="posttargetstatus")
    post_target_status_enum.create(op.get_bind(), checkfirst=True)

    # post_targets
    op.create_table(
        "post_targets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "post_id",
            UUID(as_uuid=True),
            sa.ForeignKey("posts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "social_account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("social_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", post_target_status_enum, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_post_targets_post_id", "post_targets", ["post_id"])

    # campaign status enum
    campaign_status_enum = sa.Enum("active", "paused", "completed", "draft", name="campaignstatus")
    campaign_status_enum.create(op.get_bind(), checkfirst=True)

    # campaigns
    op.create_table(
        "campaigns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("end_date", sa.Date, nullable=True),
        sa.Column("budget", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", campaign_status_enum, nullable=False, server_default="draft"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_campaigns_user_id", "campaigns", ["user_id"])

    # analytics
    op.create_table(
        "analytics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "social_account_id",
            UUID(as_uuid=True),
            sa.ForeignKey("social_accounts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "post_target_id",
            UUID(as_uuid=True),
            sa.ForeignKey("post_targets.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("likes", sa.Integer, nullable=False, server_default="0"),
        sa.Column("views", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("shares", sa.Integer, nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reach", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_analytics_social_account_id", "analytics", ["social_account_id"])
    op.create_index("ix_analytics_post_target_id", "analytics", ["post_target_id"])


def downgrade() -> None:
    op.drop_table("analytics")
    op.drop_table("campaigns")
    op.drop_table("post_targets")
    op.drop_table("posts")
    op.drop_table("social_accounts")
    op.drop_table("users")
    sa.Enum(name="campaignstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="posttargetstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="poststatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="platform").drop(op.get_bind(), checkfirst=True)
