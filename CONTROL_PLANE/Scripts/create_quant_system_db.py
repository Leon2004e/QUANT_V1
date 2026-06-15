"""
# ============================================================
# CODE_REGISTRY
# ============================================================
# script_id: create_quant_system_db
# script_name: QUANT_SYSTEM DB Creator
# owner: Leon Everts
# status: active
# layer: Control_Plane
# domain: System
# asset_type: Database Builder
# purpose: Creates QUANT_SYSTEM.db inside CONTROL_PLANE/Database
# inputs:
#   - CONTROL_PLANE folder
# outputs:
#   - CONTROL_PLANE/Database/QUANT_SYSTEM.db
#   - CONTROL_PLANE/Database/quant_system_db_metadata.json
# upstream_data:
#   - Quant_System_DB_Design.md
# downstream_data:
#   - Backend Centers
#   - Feedback Loop
#   - Frontend Dashboards
# dependencies:
#   - pathlib
#   - sqlite3
#   - json
#   - datetime
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-13
# business_criticality: critical
# environment: desktop/server
# registry_group: control_plane
# author: Leon Everts
# reviewer: ChatGPT
# created_date: 2026-06-13
# tags:
#   - control-plane
#   - database
#   - quant-system
# notes:
#   - Creates only the Control Plane database.
#   - Does not create Backend, Frontend, Management or Infrastructure folders.
#   - Does not import trading data.
# ============================================================
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


CODE_REGISTRY: Dict[str, Any] = {
    "script_id": "create_quant_system_db",
    "script_name": "QUANT_SYSTEM DB Creator",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Control_Plane",
    "domain": "System",
    "asset_type": "Database Builder",
    "purpose": "Creates QUANT_SYSTEM.db inside CONTROL_PLANE/Database",
    "inputs": ["CONTROL_PLANE folder"],
    "outputs": [
        "CONTROL_PLANE/Database/QUANT_SYSTEM.db",
        "CONTROL_PLANE/Database/quant_system_db_metadata.json",
    ],
    "upstream_data": ["Quant_System_DB_Design.md"],
    "downstream_data": ["Backend Centers", "Feedback Loop", "Frontend Dashboards"],
    "dependencies": ["pathlib", "sqlite3", "json", "datetime"],
    "schedule": "manual",
    "version": "v1.0.0",
    "last_reviewed": "2026-06-13",
    "business_criticality": "critical",
    "environment": "desktop/server",
    "registry_group": "control_plane",
    "author": "Leon Everts",
    "reviewer": "ChatGPT",
    "created_date": "2026-06-13",
    "tags": ["control-plane", "database", "quant-system"],
    "notes": [
        "Creates only the Control Plane database.",
        "Does not create Backend, Frontend, Management or Infrastructure folders.",
        "Does not import trading data.",
    ],
}


SCHEMA_VERSION = "1.0.0"


def log_info(message: str) -> None:
    print(f"[INFO] {message}")


def log_ok(message: str) -> None:
    print(f"[OK] {message}")


def log_warn(message: str) -> None:
    print(f"[WARN] {message}")


def log_error(message: str) -> None:
    print(f"[ERROR] {message}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def find_control_plane_dir(start: Path) -> Path:
    """
    Find CONTROL_PLANE directory.

    Expected current structure:

    QUANT_OS/
    └── CONTROL_PLANE/
        ├── Database/
        ├── Documentation/
        └── Scripts/
            └── create_quant_system_db.py
    """
    current = start.resolve()

    for path in [current, *current.parents]:
        if path.name.upper() == "CONTROL_PLANE":
            return path

        control_plane = path / "CONTROL_PLANE"
        if control_plane.exists() and control_plane.is_dir():
            return control_plane

    raise FileNotFoundError(
        "CONTROL_PLANE folder not found. "
        "Place this script inside CONTROL_PLANE/Scripts/."
    )


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    ensure_directory(path.parent)

    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
        file.write("\n")

    temp_path.replace(path)


def connect_db(db_path: Path) -> sqlite3.Connection:
    ensure_directory(db_path.parent)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_schema_migrations_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_id TEXT PRIMARY KEY,
            schema_version TEXT NOT NULL,
            applied_at TEXT NOT NULL,
            description TEXT NOT NULL
        );
        """
    )


def migration_exists(conn: sqlite3.Connection, migration_id: str) -> bool:
    cursor = conn.execute(
        """
        SELECT 1
        FROM schema_migrations
        WHERE migration_id = ?
        LIMIT 1;
        """,
        (migration_id,),
    )
    return cursor.fetchone() is not None


def register_migration(
    conn: sqlite3.Connection,
    migration_id: str,
    schema_version: str,
    description: str,
) -> None:
    conn.execute(
        """
        INSERT INTO schema_migrations (
            migration_id,
            schema_version,
            applied_at,
            description
        )
        VALUES (?, ?, ?, ?);
        """,
        (migration_id, schema_version, utc_now(), description),
    )


def apply_initial_schema(conn: sqlite3.Connection) -> None:
    migration_id = "001_initial_quant_system_schema"

    if migration_exists(conn, migration_id):
        log_info("Initial schema already exists. Skipping migration.")
        return

    log_info("Creating QUANT_SYSTEM.db tables...")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS strategies (
            strategy_id TEXT PRIMARY KEY,
            strategy_name TEXT NOT NULL,
            version TEXT NOT NULL,
            status TEXT NOT NULL,
            lifecycle TEXT NOT NULL,
            score REAL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS portfolios (
            portfolio_id TEXT PRIMARY KEY,
            portfolio_name TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS portfolio_members (
            portfolio_id TEXT NOT NULL,
            strategy_id TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (portfolio_id, strategy_id),
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(portfolio_id),
            FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
        );

        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            broker TEXT NOT NULL,
            account_type TEXT NOT NULL,
            balance REAL DEFAULT 0,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS deployments (
            deployment_id TEXT PRIMARY KEY,
            strategy_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            version TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT,
            stopped_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id),
            FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        );

        CREATE TABLE IF NOT EXISTS risk_limits (
            account_id TEXT PRIMARY KEY,
            daily_dd_limit REAL NOT NULL,
            max_dd_limit REAL NOT NULL,
            exposure_limit REAL NOT NULL,
            kill_switch INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(account_id)
        );

        CREATE TABLE IF NOT EXISTS governance_rules (
            rule_id TEXT PRIMARY KEY,
            rule_name TEXT NOT NULL,
            rule_type TEXT NOT NULL,
            threshold REAL,
            action TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS system_events (
            event_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            type TEXT NOT NULL,
            payload TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            change_id TEXT PRIMARY KEY,
            object_type TEXT NOT NULL,
            object_id TEXT NOT NULL,
            change TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            user TEXT NOT NULL DEFAULT 'system'
        );

        CREATE INDEX IF NOT EXISTS idx_strategies_status
            ON strategies(status);

        CREATE INDEX IF NOT EXISTS idx_strategies_lifecycle
            ON strategies(lifecycle);

        CREATE INDEX IF NOT EXISTS idx_portfolio_members_portfolio
            ON portfolio_members(portfolio_id);

        CREATE INDEX IF NOT EXISTS idx_portfolio_members_strategy
            ON portfolio_members(strategy_id);

        CREATE INDEX IF NOT EXISTS idx_deployments_strategy
            ON deployments(strategy_id);

        CREATE INDEX IF NOT EXISTS idx_deployments_account
            ON deployments(account_id);

        CREATE INDEX IF NOT EXISTS idx_deployments_status
            ON deployments(status);

        CREATE INDEX IF NOT EXISTS idx_system_events_type
            ON system_events(type);

        CREATE INDEX IF NOT EXISTS idx_system_events_timestamp
            ON system_events(timestamp);

        CREATE INDEX IF NOT EXISTS idx_audit_logs_object
            ON audit_logs(object_type, object_id);
        """
    )

    register_migration(
        conn=conn,
        migration_id=migration_id,
        schema_version=SCHEMA_VERSION,
        description="Initial QUANT_SYSTEM.db schema",
    )

    log_ok("Initial schema created.")


def insert_system_event(conn: sqlite3.Connection) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    event_id = f"EVT_DB_CREATED_{timestamp}"

    payload = {
        "database": "QUANT_SYSTEM.db",
        "schema_version": SCHEMA_VERSION,
        "message": "QUANT_SYSTEM.db created or verified",
    }

    conn.execute(
        """
        INSERT OR IGNORE INTO system_events (
            event_id,
            source,
            type,
            payload,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            event_id,
            "Control_Plane",
            "QUANT_SYSTEM_DB_CREATED",
            json.dumps(payload, ensure_ascii=False),
            utc_now(),
        ),
    )


def insert_audit_log(conn: sqlite3.Connection) -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    change_id = f"CHG_DB_CREATED_{timestamp}"

    change = {
        "action": "database_created_or_verified",
        "database": "QUANT_SYSTEM.db",
        "schema_version": SCHEMA_VERSION,
    }

    conn.execute(
        """
        INSERT OR IGNORE INTO audit_logs (
            change_id,
            object_type,
            object_id,
            change,
            timestamp,
            user
        )
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        (
            change_id,
            "database",
            "QUANT_SYSTEM.db",
            json.dumps(change, ensure_ascii=False),
            utc_now(),
            "system",
        ),
    )


def get_table_names(conn: sqlite3.Connection) -> List[str]:
    cursor = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name;
        """
    )
    return [row[0] for row in cursor.fetchall()]


def get_table_counts(conn: sqlite3.Connection, tables: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}

    for table in tables:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table};")
        counts[table] = int(cursor.fetchone()[0])

    return counts


def write_metadata_file(
    metadata_path: Path,
    db_path: Path,
    tables: List[str],
    counts: Dict[str, int],
) -> None:
    metadata = {
        "database": "QUANT_SYSTEM.db",
        "schema_version": SCHEMA_VERSION,
        "created_or_verified_at": utc_now(),
        "db_path": str(db_path),
        "tables": tables,
        "table_counts": counts,
        "code_registry": CODE_REGISTRY,
        "principle": {
            "stores": [
                "metadata",
                "status",
                "configurations",
                "references",
                "events",
                "audit logs",
            ],
            "does_not_store": [
                "tick data",
                "OHLC data",
                "large CSV files",
                "raw backtests",
                "raw broker exports",
                "trading history",
            ],
        },
    }

    atomic_write_json(metadata_path, metadata)


def create_quant_system_db(control_plane_dir: Path) -> None:
    database_dir = control_plane_dir / "Database"
    db_path = database_dir / "QUANT_SYSTEM.db"
    metadata_path = database_dir / "quant_system_db_metadata.json"

    ensure_directory(database_dir)

    log_info(f"CONTROL_PLANE directory: {control_plane_dir}")
    log_info(f"Database output: {db_path}")

    conn = connect_db(db_path)

    try:
        with conn:
            create_schema_migrations_table(conn)
            apply_initial_schema(conn)
            insert_system_event(conn)
            insert_audit_log(conn)

        tables = get_table_names(conn)
        counts = get_table_counts(conn, tables)

        write_metadata_file(
            metadata_path=metadata_path,
            db_path=db_path,
            tables=tables,
            counts=counts,
        )

        log_ok("QUANT_SYSTEM.db created or verified successfully.")
        log_ok(f"Metadata written: {metadata_path}")

    except sqlite3.Error as exc:
        log_error(f"SQLite error: {exc}")
        raise

    except OSError as exc:
        log_error(f"File system error: {exc}")
        raise

    finally:
        conn.close()


def main() -> None:
    log_info("Starting QUANT_SYSTEM.db creation...")

    try:
        control_plane_dir = find_control_plane_dir(Path(__file__))
        create_quant_system_db(control_plane_dir)
        log_ok("Done.")

    except Exception as exc:
        log_error(f"Failed to create QUANT_SYSTEM.db: {exc}")
        raise


if __name__ == "__main__":
    main()