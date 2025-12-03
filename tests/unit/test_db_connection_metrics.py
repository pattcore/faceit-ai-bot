"""Tests for DB metrics helpers in database.connection.

We keep tests focused on _classify_sql_operation so that DB
instrumentation logic remains covered without depending on
real database connections.
"""

import pytest

from src.server.database.connection import _classify_sql_operation


@pytest.mark.parametrize(
    "statement,expected",
    [
        ("SELECT * FROM users", "select"),
        ("  select 1", "select"),
        ("insert into table values (1)", "insert"),
        ("UPDATE users SET name='x'", "update"),
        (" delete from users", "delete"),
        ("WITH cte AS (SELECT 1) SELECT * FROM cte", "other"),
        ("", "other"),
        (None, "other"),  # type: ignore[arg-type]
    ],
)
def test_classify_sql_operation(statement, expected):
    assert _classify_sql_operation(statement) == expected
