"""
# ============================================================
# CODE_REGISTRY
# ============================================================
# script_id: scan_code_registry
# script_name: Code Registry Scanner
# owner: Leon Everts
# status: active
# layer: Management
# domain: Code_Registry
# asset_type: Registry Scanner
# purpose: Scans QUANT OS Python files and writes CODE_REGISTRY metadata only into QUANT_SYSTEM.db
# inputs:
#   - QUANT OS project folder
# outputs:
#   - CONTROL_PLANE/Database/QUANT_SYSTEM.db table code_registry
# upstream_data:
#   - Python scripts containing CODE_REGISTRY
# downstream_data:
#   - Code Registry Dashboard
#   - Management Workspace
#   - QUANT_SYSTEM.db
# dependencies:
#   - pathlib
#   - ast
#   - json
#   - sqlite3
#   - datetime
# schedule: manual
# version: v1.0.2
# last_reviewed: 2026-06-15
# business_criticality: high
# environment: desktop/server
# registry_group: code_registry
# author: Leon Everts
# reviewer: ChatGPT
# created_date: 2026-06-15
# tags:
#   - management
#   - code-registry
#   - scanner
# notes:
#   - Designed for QUANT OS folder names using MANAGEMENT_LAYER and CONTROL_PLANE.
#   - Scans all Python files under project root.
#   - Reads CODE_REGISTRY dictionaries without executing scanned files.
#   - Writes only into QUANT_SYSTEM.db.
#   - Does not create JSON or CSV registry exports.
# ============================================================
"""

from __future__ import annotations

import ast
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


CODE_REGISTRY: Dict[str, Any] = {
    "script_id": "scan_code_registry",
    "script_name": "Code Registry Scanner",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Management",
    "domain": "Code_Registry",
    "asset_type": "Registry Scanner",
    "purpose": "Scans QUANT OS Python files and writes CODE_REGISTRY metadata only into QUANT_SYSTEM.db",
    "inputs": ["QUANT OS project folder"],
    "outputs": ["CONTROL_PLANE/Database/QUANT_SYSTEM.db table code_registry"],
    "upstream_data": ["Python scripts containing CODE_REGISTRY"],
    "downstream_data": [
        "Code Registry Dashboard",
        "Management Workspace",
        "QUANT_SYSTEM.db",
    ],
    "dependencies": ["pathlib", "ast", "json", "sqlite3", "datetime"],
    "schedule": "manual",
    "version": "v1.0.2",
    "last_reviewed": "2026-06-15",
    "business_criticality": "high",
    "environment": "desktop/server",
    "registry_group": "code_registry",
    "author": "Leon Everts",
    "reviewer": "ChatGPT",
    "created_date": "2026-06-15",
    "tags": ["management", "code-registry", "scanner"],
    "notes": [
        "Designed for QUANT OS folder names using MANAGEMENT_LAYER and CONTROL_PLANE.",
        "Scans all Python files under project root.",
        "Reads CODE_REGISTRY dictionaries without executing scanned files.",
        "Writes only into QUANT_SYSTEM.db.",
        "Does not create JSON or CSV registry exports.",
    ],
}


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


def find_quant_root(start: Path) -> Path:
    """
    Find QUANT OS root.

    Expected root contains:
    - MANAGEMENT_LAYER/
    - CONTROL_PLANE/
    """
    current = start.resolve()

    for path in [current, *current.parents]:
        management_layer = path / "MANAGEMENT_LAYER"
        control_plane = path / "CONTROL_PLANE"

        if management_layer.exists() and control_plane.exists():
            return path

    raise FileNotFoundError(
        "QUANT OS root not found. Expected folders: MANAGEMENT_LAYER/ and CONTROL_PLANE/."
    )


def should_skip_file(path: Path) -> bool:
    skip_parts = {
        ".git",
        "__pycache__",
        ".venv",
        "venv",
        "env",
        ".mypy_cache",
        ".pytest_cache",
        "site-packages",
        "node_modules",
    }

    return any(part in skip_parts for part in path.parts)


def get_quant_system_db_path(quant_root: Path) -> Path:
    candidates = [
        quant_root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db",
        quant_root / "CONTROL_PLANE" / "DATABASE" / "QUANT_SYSTEM.db",
        quant_root / "CONTROL_PLANE" / "QUANT_SYSTEM.db",
    ]

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "QUANT_SYSTEM.db not found. Expected one of: "
        "CONTROL_PLANE/Database/QUANT_SYSTEM.db, "
        "CONTROL_PLANE/DATABASE/QUANT_SYSTEM.db, "
        "CONTROL_PLANE/QUANT_SYSTEM.db"
    )


def extract_code_registry_from_file(path: Path) -> Dict[str, Any]:
    """
    Extract CODE_REGISTRY without executing the file.
    """
    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = path.read_text(encoding="latin-1")

    tree = ast.parse(source, filename=str(path))

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CODE_REGISTRY":
                    value = ast.literal_eval(node.value)

                    if not isinstance(value, dict):
                        raise ValueError("CODE_REGISTRY exists but is not a dictionary.")

                    return value

        if isinstance(node, ast.AnnAssign):
            target = node.target

            if isinstance(target, ast.Name) and target.id == "CODE_REGISTRY":
                value = ast.literal_eval(node.value)

                if not isinstance(value, dict):
                    raise ValueError("CODE_REGISTRY exists but is not a dictionary.")

                return value

    raise ValueError("No CODE_REGISTRY dictionary found.")


def normalize_registry(
    registry: Dict[str, Any],
    file_path: Path,
    quant_root: Path,
    scan_status: str,
    scan_error: str = "",
) -> Dict[str, Any]:
    relative_path = file_path.relative_to(quant_root)

    return {
        "script_id": registry.get("script_id", ""),
        "script_name": registry.get("script_name", ""),
        "owner": registry.get("owner", ""),
        "status": registry.get("status", ""),
        "layer": registry.get("layer", ""),
        "domain": registry.get("domain", ""),
        "asset_type": registry.get("asset_type", ""),
        "purpose": registry.get("purpose", ""),
        "inputs": registry.get("inputs", []),
        "outputs": registry.get("outputs", []),
        "upstream_data": registry.get("upstream_data", []),
        "downstream_data": registry.get("downstream_data", []),
        "dependencies": registry.get("dependencies", []),
        "schedule": registry.get("schedule", ""),
        "version": registry.get("version", ""),
        "last_reviewed": registry.get("last_reviewed", ""),
        "business_criticality": registry.get("business_criticality", ""),
        "environment": registry.get("environment", ""),
        "registry_group": registry.get("registry_group", ""),
        "author": registry.get("author", ""),
        "reviewer": registry.get("reviewer", ""),
        "created_date": registry.get("created_date", ""),
        "tags": registry.get("tags", []),
        "notes": registry.get("notes", []),
        "path": str(file_path),
        "relative_path": str(relative_path),
        "scan_status": scan_status,
        "scan_error": scan_error,
        "scanned_at": utc_now(),
    }


def scan_python_files(quant_root: Path) -> List[Dict[str, Any]]:
    log_info(f"Scanning Python files under: {quant_root}")

    rows: List[Dict[str, Any]] = []

    python_files = [
        path
        for path in quant_root.rglob("*.py")
        if path.is_file() and not should_skip_file(path)
    ]

    log_info(f"Found Python files: {len(python_files)}")

    for file_path in python_files:
        try:
            registry = extract_code_registry_from_file(file_path)

            row = normalize_registry(
                registry=registry,
                file_path=file_path,
                quant_root=quant_root,
                scan_status="ok",
            )

            if not row.get("script_id"):
                raise ValueError("CODE_REGISTRY missing required field: script_id")

            rows.append(row)

            log_ok(
                f"Registry found: {row.get('script_id')} | {row.get('relative_path')}"
            )

        except Exception as exc:
            row = normalize_registry(
                registry={},
                file_path=file_path,
                quant_root=quant_root,
                scan_status="missing_or_invalid",
                scan_error=str(exc),
            )

            rows.append(row)

            log_warn(f"No valid CODE_REGISTRY: {file_path.name} | {exc}")

    return rows


def ensure_code_registry_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS code_registry (
            script_id TEXT PRIMARY KEY,
            script_name TEXT,
            owner TEXT,
            status TEXT,
            layer TEXT,
            domain TEXT,
            asset_type TEXT,
            purpose TEXT,
            inputs TEXT,
            outputs TEXT,
            upstream_data TEXT,
            downstream_data TEXT,
            dependencies TEXT,
            schedule TEXT,
            version TEXT,
            last_reviewed TEXT,
            business_criticality TEXT,
            environment TEXT,
            registry_group TEXT,
            author TEXT,
            reviewer TEXT,
            created_date TEXT,
            tags TEXT,
            notes TEXT,
            path TEXT,
            relative_path TEXT,
            scan_status TEXT,
            scan_error TEXT,
            scanned_at TEXT
        );
        """
    )

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_code_registry_layer ON code_registry(layer);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_code_registry_status ON code_registry(status);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_code_registry_domain ON code_registry(domain);"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_code_registry_registry_group ON code_registry(registry_group);"
    )


def clear_previous_scan(conn: sqlite3.Connection) -> None:
    """
    Keeps table schema, removes old scan state.

    This makes the table reflect the current codebase.
    """
    conn.execute("DELETE FROM code_registry;")


def write_registry_to_db(db_path: Path, rows: List[Dict[str, Any]]) -> None:
    log_info(f"Writing registry only to database: {db_path}")

    conn = sqlite3.connect(db_path)

    try:
        with conn:
            ensure_code_registry_table(conn)
            clear_previous_scan(conn)

            valid_rows = [row for row in rows if row.get("script_id")]

            for row in valid_rows:
                conn.execute(
                    """
                    INSERT INTO code_registry (
                        script_id,
                        script_name,
                        owner,
                        status,
                        layer,
                        domain,
                        asset_type,
                        purpose,
                        inputs,
                        outputs,
                        upstream_data,
                        downstream_data,
                        dependencies,
                        schedule,
                        version,
                        last_reviewed,
                        business_criticality,
                        environment,
                        registry_group,
                        author,
                        reviewer,
                        created_date,
                        tags,
                        notes,
                        path,
                        relative_path,
                        scan_status,
                        scan_error,
                        scanned_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        row.get("script_id", ""),
                        row.get("script_name", ""),
                        row.get("owner", ""),
                        row.get("status", ""),
                        row.get("layer", ""),
                        row.get("domain", ""),
                        row.get("asset_type", ""),
                        row.get("purpose", ""),
                        json.dumps(row.get("inputs", []), ensure_ascii=False),
                        json.dumps(row.get("outputs", []), ensure_ascii=False),
                        json.dumps(row.get("upstream_data", []), ensure_ascii=False),
                        json.dumps(row.get("downstream_data", []), ensure_ascii=False),
                        json.dumps(row.get("dependencies", []), ensure_ascii=False),
                        row.get("schedule", ""),
                        row.get("version", ""),
                        row.get("last_reviewed", ""),
                        row.get("business_criticality", ""),
                        row.get("environment", ""),
                        row.get("registry_group", ""),
                        row.get("author", ""),
                        row.get("reviewer", ""),
                        row.get("created_date", ""),
                        json.dumps(row.get("tags", []), ensure_ascii=False),
                        json.dumps(row.get("notes", []), ensure_ascii=False),
                        row.get("path", ""),
                        row.get("relative_path", ""),
                        row.get("scan_status", ""),
                        row.get("scan_error", ""),
                        row.get("scanned_at", ""),
                    ),
                )

        log_ok("code_registry table updated in QUANT_SYSTEM.db.")

    finally:
        conn.close()


def insert_scan_event(db_path: Path, valid_count: int, invalid_count: int) -> None:
    """
    Writes scan event into system_events if the table exists.
    """
    conn = sqlite3.connect(db_path)

    try:
        with conn:
            cursor = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table' AND name='system_events';
                """
            )

            if cursor.fetchone() is None:
                return

            event_id = f"EVT_CODE_REGISTRY_SCAN_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

            payload = {
                "valid_code_registry_entries": valid_count,
                "missing_or_invalid_entries": invalid_count,
                "scanner_version": CODE_REGISTRY["version"],
            }

            conn.execute(
                """
                INSERT INTO system_events (
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
                    "Management.Code_Registry",
                    "CODE_REGISTRY_SCAN_COMPLETED",
                    json.dumps(payload, ensure_ascii=False),
                    utc_now(),
                ),
            )

    finally:
        conn.close()


def main() -> None:
    log_info("Starting Code Registry scan...")

    try:
        quant_root = find_quant_root(Path(__file__))
        log_info(f"QUANT OS root: {quant_root}")

        db_path = get_quant_system_db_path(quant_root)
        log_info(f"QUANT_SYSTEM.db found: {db_path}")

        rows = scan_python_files(quant_root)

        write_registry_to_db(db_path, rows)

        valid_count = len([row for row in rows if row.get("scan_status") == "ok"])
        invalid_count = len(rows) - valid_count

        insert_scan_event(
            db_path=db_path,
            valid_count=valid_count,
            invalid_count=invalid_count,
        )

        log_ok("Code Registry scan completed.")
        log_info(f"Valid CODE_REGISTRY entries: {valid_count}")
        log_info(f"Missing or invalid CODE_REGISTRY entries: {invalid_count}")
        log_info("No JSON or CSV exports were created.")

    except Exception as exc:
        log_error(f"Code Registry scan failed: {exc}")
        raise


if __name__ == "__main__":
    main()