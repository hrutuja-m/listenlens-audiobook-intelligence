from __future__ import annotations

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATABASE_PATH = PROJECT_ROOT / "data" / "listenlens.duckdb"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"
SYNTHETIC_DATA_DIR = PROJECT_ROOT / "data" / "synthetic"


TABLE_LOAD_ORDER = [
    "listener_segments",
    "platform_models",
    "narrators",
    "books",
    "users",
    "subscriptions",
    "book_ownership",
    "listening_sessions",
    "ratings",
    "recommendations",
]


EXPECTED_ROW_COUNTS = {
    "listener_segments": 7,
    "platform_models": 3,
    "narrators": 50,
    "books": 300,
    "users": 1_000,
    "subscriptions": 1_000,
    "listening_sessions": 10_000,
    "ratings": 2_000,
    "recommendations": 3_000,
}


def validate_required_files() -> None:
    """Confirm that schema.sql and all required CSV files exist."""
    missing_files: list[Path] = []

    if not SCHEMA_PATH.exists():
        missing_files.append(SCHEMA_PATH)

    for table_name in TABLE_LOAD_ORDER:
        csv_path = SYNTHETIC_DATA_DIR / f"{table_name}.csv"

        if not csv_path.exists():
            missing_files.append(csv_path)

    if missing_files:
        missing_list = "\n".join(f"- {path}" for path in missing_files)

        raise FileNotFoundError(
            "Required files are missing:\n"
            f"{missing_list}\n\n"
            "Run `python src/generate_data.py` before loading the database."
        )


def create_schema(connection: duckdb.DuckDBPyConnection) -> None:
    """Create database tables using sql/schema.sql."""
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    connection.execute(schema_sql)


def clear_existing_data(connection: duckdb.DuckDBPyConnection) -> None:
    """
    Delete existing rows in reverse dependency order.

    This allows the loader to be rerun without creating duplicate data.
    """
    for table_name in reversed(TABLE_LOAD_ORDER):
        connection.execute(f"DELETE FROM {table_name}")


def load_tables(connection: duckdb.DuckDBPyConnection) -> None:
    """Load every synthetic CSV into its matching DuckDB table."""
    print("Loading synthetic CSV files into DuckDB")
    print("-" * 60)

    for table_name in TABLE_LOAD_ORDER:
        csv_path = SYNTHETIC_DATA_DIR / f"{table_name}.csv"

        connection.execute(
            f"""
            INSERT INTO {table_name}
            SELECT *
            FROM read_csv_auto(
                ?,
                header = true,
                sample_size = -1,
                nullstr = ''
            )
            """,
            [str(csv_path)],
        )

        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        print(f"Loaded {table_name:<20} {row_count:>6} rows")


def validate_row_counts(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Compare database row counts with expected dataset sizes."""
    failures: list[str] = []

    print("\nRow-count validation")
    print("-" * 70)

    for table_name in TABLE_LOAD_ORDER:
        actual_count = connection.execute(
            f"SELECT COUNT(*) FROM {table_name}"
        ).fetchone()[0]

        expected_count = EXPECTED_ROW_COUNTS.get(table_name)

        if expected_count is None:
            status = "INFO"
            expected_display = "variable"
        elif actual_count == expected_count:
            status = "PASS"
            expected_display = str(expected_count)
        else:
            status = "FAIL"
            expected_display = str(expected_count)

            failures.append(
                f"{table_name}: expected {expected_count}, "
                f"found {actual_count}"
            )

        print(
            f"{status:<4} | "
            f"{table_name:<20} | "
            f"actual={actual_count:<6} | "
            f"expected={expected_display}"
        )

    if failures:
        failure_details = "\n".join(f"- {item}" for item in failures)

        raise ValueError(
            "Row-count validation failed:\n"
            f"{failure_details}"
        )


def validate_foreign_keys(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Check for records that reference missing parent records."""
    checks = {
        "books.narrator_id": """
            SELECT COUNT(*)
            FROM books AS b
            LEFT JOIN narrators AS n
                ON b.narrator_id = n.narrator_id
            WHERE n.narrator_id IS NULL
        """,
        "users.segment_id": """
            SELECT COUNT(*)
            FROM users AS u
            LEFT JOIN listener_segments AS ls
                ON u.segment_id = ls.segment_id
            WHERE ls.segment_id IS NULL
        """,
        "subscriptions.user_id": """
            SELECT COUNT(*)
            FROM subscriptions AS s
            LEFT JOIN users AS u
                ON s.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        "subscriptions.model_id": """
            SELECT COUNT(*)
            FROM subscriptions AS s
            LEFT JOIN platform_models AS pm
                ON s.model_id = pm.model_id
            WHERE pm.model_id IS NULL
        """,
        "book_ownership.user_id": """
            SELECT COUNT(*)
            FROM book_ownership AS bo
            LEFT JOIN users AS u
                ON bo.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        "book_ownership.book_id": """
            SELECT COUNT(*)
            FROM book_ownership AS bo
            LEFT JOIN books AS b
                ON bo.book_id = b.book_id
            WHERE b.book_id IS NULL
        """,
        "listening_sessions.user_id": """
            SELECT COUNT(*)
            FROM listening_sessions AS ls
            LEFT JOIN users AS u
                ON ls.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        "listening_sessions.book_id": """
            SELECT COUNT(*)
            FROM listening_sessions AS ls
            LEFT JOIN books AS b
                ON ls.book_id = b.book_id
            WHERE b.book_id IS NULL
        """,
        "ratings.user_id": """
            SELECT COUNT(*)
            FROM ratings AS r
            LEFT JOIN users AS u
                ON r.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        "ratings.book_id": """
            SELECT COUNT(*)
            FROM ratings AS r
            LEFT JOIN books AS b
                ON r.book_id = b.book_id
            WHERE b.book_id IS NULL
        """,
        "recommendations.user_id": """
            SELECT COUNT(*)
            FROM recommendations AS r
            LEFT JOIN users AS u
                ON r.user_id = u.user_id
            WHERE u.user_id IS NULL
        """,
        "recommendations.book_id": """
            SELECT COUNT(*)
            FROM recommendations AS r
            LEFT JOIN books AS b
                ON r.book_id = b.book_id
            WHERE b.book_id IS NULL
        """,
    }

    failures: list[str] = []

    print("\nForeign-key validation")
    print("-" * 70)

    for relationship, query in checks.items():
        orphan_count = connection.execute(query).fetchone()[0]
        status = "PASS" if orphan_count == 0 else "FAIL"

        print(
            f"{status:<4} | "
            f"{relationship:<32} | "
            f"orphans={orphan_count}"
        )

        if orphan_count > 0:
            failures.append(
                f"{relationship}: {orphan_count} orphaned records"
            )

    if failures:
        failure_details = "\n".join(f"- {item}" for item in failures)

        raise ValueError(
            "Foreign-key validation failed:\n"
            f"{failure_details}"
        )


def show_database_summary(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Print a small analytics summary to confirm the database is queryable."""
    summary = connection.execute(
        """
        SELECT
            COUNT(*) AS total_sessions,
            COUNT(DISTINCT user_id) AS active_listeners,
            COUNT(DISTINCT book_id) AS books_streamed,
            ROUND(SUM(minutes_listened) / 60.0, 2) AS total_hours
        FROM listening_sessions
        """
    ).fetchone()

    print("\nDatabase summary")
    print("-" * 70)
    print(f"Total sessions:   {summary[0]}")
    print(f"Active listeners: {summary[1]}")
    print(f"Books streamed:   {summary[2]}")
    print(f"Total hours:      {summary[3]}")


def main() -> None:
    validate_required_files()

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect(str(DATABASE_PATH))

    try:
        connection.execute("BEGIN TRANSACTION")

        create_schema(connection)
        clear_existing_data(connection)
        load_tables(connection)
        validate_row_counts(connection)
        validate_foreign_keys(connection)
        show_database_summary(connection)

        connection.execute("COMMIT")

        print("\nDuckDB database created and validated successfully.")
        print(f"Database path: {DATABASE_PATH}")

    except Exception:
        connection.execute("ROLLBACK")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()