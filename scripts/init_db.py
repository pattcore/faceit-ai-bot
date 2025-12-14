"""Initialize database with tables"""
import sys
import time
from pathlib import Path

from sqlalchemy.exc import OperationalError

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.server.database.models import Base  # noqa: E402
from src.server.database.connection import engine  # noqa: E402


def _wait_for_db(max_attempts: int = 10, delay_seconds: int = 3) -> None:
    """Wait until the database is available or give up after several attempts."""
    for attempt in range(1, max_attempts + 1):
        try:
            # This will try to open a real connection using the configured engine.
            with engine.connect():
                print("Database is available.")
                return
        except OperationalError as exc:  # pragma: no cover - startup only
            print(
                f"Database not ready (attempt {attempt}/{max_attempts}): {exc}"
            )
            if attempt == max_attempts:
                print("Giving up waiting for the database.")
                raise
            time.sleep(delay_seconds)


def init_db() -> None:
    """Create all database tables."""
    print("Waiting for database...")
    _wait_for_db()
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
