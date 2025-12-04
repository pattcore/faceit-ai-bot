"""Database migration utilities for performance optimization."""

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_performance_indexes(db: Session) -> None:
    """Create additional indexes for performance optimization."""

    indexes = [
        # User indexes
        (
            "CREATE INDEX IF NOT EXISTS idx_users_created_at "
            "ON users(created_at)",
            "User creation date index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_users_is_active "
            "ON users(is_active)",
            "User active status index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_users_email_active "
            "ON users(email, is_active)",
            "User email and active status composite index",
        ),

        # Subscription indexes
        (
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id_active "
            "ON subscriptions(user_id, is_active)",
            "Subscription user and active status composite index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_tier "
            "ON subscriptions(tier)",
            "Subscription tier index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_subscriptions_expires_at "
            "ON subscriptions(expires_at)",
            "Subscription expiration date index",
        ),

        # Payment indexes
        (
            "CREATE INDEX IF NOT EXISTS idx_payments_user_id_created_at "
            "ON payments(user_id, created_at)",
            "Payment user and creation date composite index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_payments_status "
            "ON payments(status)",
            "Payment status index",
        ),
        (
            "CREATE INDEX IF NOT EXISTS idx_payments_provider "
            "ON payments(provider)",
            "Payment provider index",
        ),
    ]

    for index_sql, description in indexes:
        try:
            db.execute(text(index_sql))
            logger.info(f"Created index: {description}")
        except Exception as e:
            logger.warning(f"Index creation failed ({description}): {str(e)}")

    db.commit()


def analyze_tables(db: Session) -> None:
    """Analyze tables for query optimization."""

    tables = ["users", "subscriptions", "payments"]

    for table in tables:
        try:
            db.execute(text(f"ANALYZE {table}"))
            logger.info(f"Analyzed table: {table}")
        except Exception as e:
            logger.warning(f"Table analysis failed ({table}): {str(e)}")

    db.commit()


def get_table_stats(db: Session, table_name: str) -> dict:
    """Get statistics for a table."""

    try:
        stmt = text(
            """
            SELECT
                table_name,
                row_count,
                avg_row_length,
                data_length,
                index_length
            FROM information_schema.TABLES
            WHERE table_name = :table_name
            """
        )
        result = db.execute(stmt, {"table_name": table_name}).fetchone()

        if result:
            return {
                "table_name": result[0],
                "row_count": result[1],
                "avg_row_length": result[2],
                "data_length": result[3],
                "index_length": result[4],
            }
    except Exception as e:
        logger.error(f"Failed to get table stats: {str(e)}")

    return {}
