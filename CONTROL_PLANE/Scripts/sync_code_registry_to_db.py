# ============================================================
# CODE_REGISTRY
# script_id: sync_code_registry_to_db
# script_name: sync_code_registry_to_db.py
# owner: Leon Everts
# status: active
# layer: Control Plane
# domain: Code Registry
# asset_type: Python Script
# purpose: Scan QUANT OS Python files and write code metadata into QUANT_SYSTEM.db code_registry table
# inputs: QUANT OS project folders
# outputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry
# upstream_data: Python files with CODE_REGISTRY headers or CODE_REGISTRY dictionaries
# downstream_data: code_registry
# dependencies: sqlite3, pathlib, ast, re, logging
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-17
# business_criticality: high
# environment: local
# registry_group: Control Plane Scripts
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: code-registry, scanner, database, control-plane
# notes: Scanner reads itself and registers itself into code_registry.
# ============================================================

from __future__ import annotations

import ast
import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


CODE_REGISTRY = {
    "script_id": "sync_code_registry_to_db",
    "script_name": "sync_code_registry_to_db.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Control Plane",
    "domain": "Code Registry",
    "asset_type": "Python Script",
    "purpose": "Scan QUANT OS Python files and write code metadata into QUANT_SYSTEM.db code_registry table",
    "inputs": "QUANT OS project folders",
    "outputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry",
    "upstream_data": "Python files with CODE_REGISTRY headers or CODE_REGISTRY dictionaries",
    "downstream_data": "code_registry",
    "dependencies": "sqlite3, pathlib, ast, re, logging",
    "schedule": "manual",
    "version": "v1.0.0",
    "last_reviewed": "2026-06-17",
    "business_criticality": "high",
    "environment": "local",
    "registry_group": "Control Plane Scripts",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "code-registry,scanner,database,control-plane",
    "notes": "Scanner reads itself and registers itself into code_registry.",
}


SCRIPT_VERSION = "v1.0.0"

EXCLUDED_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build",
}

REQUIRED_FIELDS = [
    "script_id",
    "script_name",
    "owner",
    "status",
    "layer",
    "domain",
    "asset_type",
    "purpose",
    "inputs",
    "outputs",
    "upstream_data",
    "downstream_data",
    "dependencies",
    "schedule",
    "version",
    "last_reviewed",
    "business_criticality",
    "environment",
    "registry_group",
    "author",
    "reviewer",
    "created_date",
    "tags",
    "notes",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def find_quant_root(start_path: Optional[Path] = None) -> Path:
    current = (start_path or Path(__file__).resolve()).parent

    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists() and (path / "INFRASTRUCTURE_LAYER").exists():
            return path

    raise FileNotFoundError(
        "QUANT OS root not found. Expected CONTROL_PLANE and INFRASTRUCTURE_LAYER."
    )


def get_paths(root: Path) -> Dict[str, Path]:
    return {
        "db_dir": root / "CONTROL_PLANE" / "Database",
        "db_path": root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db",
    }


def connect_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_code_registry_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS code_registry (
            script_id TEXT PRIMARY KEY,
            script_name TEXT NOT NULL,
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
            file_path TEXT NOT NULL,
            relative_path TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_extension TEXT NOT NULL,
            scan_status TEXT NOT NULL,
            scan_error TEXT,
            registry_source TEXT NOT NULL,
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_code_registry_layer
        ON code_registry(layer);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_code_registry_status
        ON code_registry(status);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_code_registry_domain
        ON code_registry(domain);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_code_registry_scan_status
        ON code_registry(scan_status);
        """
    )

    conn.commit()


def clear_code_registry(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM code_registry;")
    conn.commit()


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in path.parts)


def discover_python_files(root: Path) -> List[Path]:
    files: List[Path] = []

    for path in root.rglob("*.py"):
        if path.is_file() and not should_skip(path):
            files.append(path)

    return sorted(files)


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def stringify(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(x) for x in value)

    if isinstance(value, dict):
        return str(value)

    return str(value)


def extract_runtime_code_registry(source: str) -> Optional[Dict[str, Any]]:
    """
    Extracts CODE_REGISTRY = {...} using AST.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "CODE_REGISTRY":
                    try:
                        value = ast.literal_eval(node.value)
                        if isinstance(value, dict):
                            return value
                    except Exception:
                        return None

        if isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and target.id == "CODE_REGISTRY":
                try:
                    value = ast.literal_eval(node.value)
                    if isinstance(value, dict):
                        return value
                except Exception:
                    return None

    return None


def extract_header_code_registry(source: str) -> Dict[str, str]:
    """
    Extracts comment header lines like:
    # script_id: abc
    # purpose: ...
    """
    header: Dict[str, str] = {}

    lines = source.splitlines()
    in_registry = False

    for line in lines[:120]:
        stripped = line.strip()

        if stripped.startswith("# CODE_REGISTRY"):
            in_registry = True
            continue

        if in_registry and stripped.startswith("# ==="):
            continue

        if in_registry:
            if not stripped.startswith("#"):
                if stripped:
                    break
                continue

            content = stripped[1:].strip()

            if not content:
                continue

            match = re.match(r"^([A-Za-z0-9_]+)\s*:\s*(.*)$", content)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                header[key] = value

    return header


def build_registry_record(path: Path, root: Path) -> Dict[str, Any]:
    source = safe_read_text(path)
    runtime_registry = extract_runtime_code_registry(source)
    header_registry = extract_header_code_registry(source)

    if runtime_registry:
        registry = dict(runtime_registry)
        registry_source = "runtime_dict"
        scan_status = "valid"
        scan_error = None
    elif header_registry:
        registry = dict(header_registry)
        registry_source = "header"
        scan_status = "valid"
        scan_error = None
    else:
        registry = {}
        registry_source = "none"
        scan_status = "missing_registry"
        scan_error = "No CODE_REGISTRY header or CODE_REGISTRY dictionary found"

    relative_path = str(path.relative_to(root))

    if not registry.get("script_id"):
        registry["script_id"] = relative_path.replace("\\", "/")

    if not registry.get("script_name"):
        registry["script_name"] = path.name

    missing_required = [
        field for field in REQUIRED_FIELDS
        if not stringify(registry.get(field)).strip()
    ]

    if scan_status == "valid" and missing_required:
        scan_status = "warning"
        scan_error = "Missing fields: " + ", ".join(missing_required)

    record: Dict[str, Any] = {}

    for field in REQUIRED_FIELDS:
        record[field] = stringify(registry.get(field))

    record["file_path"] = str(path)
    record["relative_path"] = relative_path
    record["file_name"] = path.name
    record["file_extension"] = path.suffix
    record["scan_status"] = scan_status
    record["scan_error"] = scan_error
    record["registry_source"] = registry_source
    record["discovered_at"] = utc_now()
    record["updated_at"] = utc_now()

    return record


def insert_code_registry_record(conn: sqlite3.Connection, record: Dict[str, Any]) -> None:
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
            file_path,
            relative_path,
            file_name,
            file_extension,
            scan_status,
            scan_error,
            registry_source,
            discovered_at,
            updated_at
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """,
        (
            record["script_id"],
            record["script_name"],
            record["owner"],
            record["status"],
            record["layer"],
            record["domain"],
            record["asset_type"],
            record["purpose"],
            record["inputs"],
            record["outputs"],
            record["upstream_data"],
            record["downstream_data"],
            record["dependencies"],
            record["schedule"],
            record["version"],
            record["last_reviewed"],
            record["business_criticality"],
            record["environment"],
            record["registry_group"],
            record["author"],
            record["reviewer"],
            record["created_date"],
            record["tags"],
            record["notes"],
            record["file_path"],
            record["relative_path"],
            record["file_name"],
            record["file_extension"],
            record["scan_status"],
            record["scan_error"],
            record["registry_source"],
            record["discovered_at"],
            record["updated_at"],
        ),
    )


def fetch_issue_rows(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            script_id,
            script_name,
            relative_path,
            scan_status,
            scan_error,
            registry_source
        FROM code_registry
        WHERE scan_status != 'valid'
        ORDER BY scan_status, relative_path;
        """
    ).fetchall()


def print_issue_report(issue_rows: List[sqlite3.Row]) -> None:
    print("\n" + "=" * 100)
    print("CODE REGISTRY ISSUES")
    print("=" * 100)

    if not issue_rows:
        print("No code registry issues found.")
        print("=" * 100)
        return

    for index, row in enumerate(issue_rows, start=1):
        print(f"\n[{index}] {row['relative_path']}")
        print(f"Script ID       : {row['script_id']}")
        print(f"Script Name     : {row['script_name']}")
        print(f"Status          : {row['scan_status']}")
        print(f"Source          : {row['registry_source']}")
        print(f"Reason          : {row['scan_error']}")

    print("\n" + "=" * 100)
    print(f"Total Issues: {len(issue_rows)}")
    print("=" * 100)


def sync_code_registry_to_db(root: Path) -> Dict[str, Any]:
    paths = get_paths(root)
    py_files = discover_python_files(root)

    conn = connect_db(paths["db_path"])

    try:
        create_code_registry_table(conn)
        clear_code_registry(conn)

        valid_count = 0
        warning_count = 0
        missing_count = 0

        for path in py_files:
            record = build_registry_record(path, root)
            insert_code_registry_record(conn, record)

            if record["scan_status"] == "valid":
                valid_count += 1
            elif record["scan_status"] == "warning":
                warning_count += 1
            else:
                missing_count += 1

        conn.commit()

        issue_rows = fetch_issue_rows(conn)

        summary = {
            "files_scanned": len(py_files),
            "valid_files": valid_count,
            "warning_files": warning_count,
            "missing_registry_files": missing_count,
            "db_path": str(paths["db_path"]),
            "table_updated": "code_registry",
            "self_registered": any(
                path.name == Path(__file__).name and path.resolve() == Path(__file__).resolve()
                for path in py_files
            ),
        }

        print_issue_report(issue_rows)

        return summary

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def main() -> None:
    setup_logging()

    logging.info("START | sync_code_registry_to_db")

    root = find_quant_root()
    logging.info("INPUT_LOADED | QUANT OS root: %s", root)

    logging.info("PROCESSING_STARTED")

    summary = sync_code_registry_to_db(root)

    logging.info("PROCESSING_COMPLETED")
    logging.info("OUTPUT_WRITTEN | %s", summary)
    logging.info("END")


if __name__ == "__main__":
    main()
