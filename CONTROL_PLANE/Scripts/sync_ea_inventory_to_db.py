# ============================================================
# CODE_REGISTRY
# script_id: sync_ea_inventory_to_db
# script_name: sync_ea_inventory_to_db.py
# owner: Leon Everts
# status: active
# layer: Control Plane
# domain: EA Inventory
# asset_type: Python Script
# purpose: Scan EA files from Infrastructure Storage and write only ea_file_inventory into QUANT_SYSTEM.db
# inputs: INFRASTRUCTURE_LAYER/Storage/6_System/EA
# outputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory
# upstream_data: EA .mq5/.ex5 files
# downstream_data: ea_file_inventory
# dependencies: sqlite3, pathlib, re, logging
# schedule: manual
# version: v2.0.0
# last_reviewed: 2026-06-17
# business_criticality: high
# environment: local
# registry_group: Control Plane Scripts
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: ea, inventory, scanner, database, control-plane
# notes: Only updates ea_file_inventory. Does not touch strategies, code_registry, system_events or metadata.
# ============================================================

from __future__ import annotations

import logging
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


CODE_REGISTRY = {
    "script_id": "sync_ea_inventory_to_db",
    "script_name": "sync_ea_inventory_to_db.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Control Plane",
    "domain": "EA Inventory",
    "asset_type": "Python Script",
    "purpose": "Scan EA files from Infrastructure Storage and write only ea_file_inventory into QUANT_SYSTEM.db",
    "inputs": "INFRASTRUCTURE_LAYER/Storage/6_System/EA",
    "outputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory",
    "upstream_data": "EA .mq5/.ex5 files",
    "downstream_data": "ea_file_inventory",
    "dependencies": "sqlite3, pathlib, re, logging",
    "schedule": "manual",
    "version": "v2.0.0",
    "last_reviewed": "2026-06-17",
    "business_criticality": "high",
    "environment": "local",
    "registry_group": "Control Plane Scripts",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "ea,inventory,scanner,database,control-plane",
    "notes": "Only updates ea_file_inventory. Does not touch strategies, code_registry, system_events or metadata.",
}


SCRIPT_VERSION = "v2.0.0"
VALID_EXTENSIONS = {".mq5", ".ex5"}

EA_FILENAME_PATTERN = re.compile(
    r"^(?P<symbol>[A-Za-z0-9.]+)_"
    r"(?P<ea_number>\d+)_"
    r"(?P<strategy_id>[0-9]+(?:\.[0-9]+)+)_"
    r"(?P<direction>BUY|SELL|BOTH)_"
    r"(?P<timeframe>[A-Za-z0-9]+)"
    r"(?P<extension>\.mq5|\.ex5)$"
)


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
        "ea_root": root / "INFRASTRUCTURE_LAYER" / "Storage" / "6_System" / "EA",
        "db_dir": root / "CONTROL_PLANE" / "Database",
        "db_path": root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db",
    }


def validate_paths(paths: Dict[str, Path]) -> None:
    if not paths["ea_root"].exists():
        raise FileNotFoundError(f"EA folder not found: {paths['ea_root']}")

    paths["db_dir"].mkdir(parents=True, exist_ok=True)


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def create_ea_file_inventory_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ea_file_inventory (
            file_path TEXT PRIMARY KEY,
            file_name TEXT NOT NULL,
            symbol_from_folder TEXT NOT NULL,
            symbol_from_filename TEXT,
            ea_number INTEGER,
            strategy_id TEXT,
            direction TEXT,
            timeframe TEXT,
            extension TEXT NOT NULL,
            parse_status TEXT NOT NULL,
            parse_error TEXT,
            discovered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ea_file_inventory_parse_status
        ON ea_file_inventory(parse_status);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ea_file_inventory_symbol_folder
        ON ea_file_inventory(symbol_from_folder);
        """
    )

    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_ea_file_inventory_strategy_id
        ON ea_file_inventory(strategy_id);
        """
    )

    conn.commit()


def clear_ea_file_inventory(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM ea_file_inventory;")
    conn.commit()


def discover_ea_files(ea_root: Path) -> List[Path]:
    return sorted(
        path for path in ea_root.rglob("*")
        if path.is_file() and path.suffix.lower() in VALID_EXTENSIONS
    )


def parse_ea_filename(file_path: Path) -> Dict[str, object]:
    file_name_original = file_path.name
    file_name_stripped = file_name_original.strip()
    extension = file_path.suffix.lower()
    symbol_from_folder = file_path.parent.name

    result = {
        "file_path": str(file_path),
        "file_name": file_name_original,
        "symbol_from_folder": symbol_from_folder,
        "symbol_from_filename": None,
        "ea_number": None,
        "strategy_id": None,
        "direction": None,
        "timeframe": None,
        "extension": extension,
        "parse_status": "valid",
        "parse_error": None,
    }

    if extension not in VALID_EXTENSIONS:
        result["parse_status"] = "invalid"
        result["parse_error"] = f"Invalid extension: {extension}"
        return result

    if file_name_original != file_name_stripped:
        result["parse_status"] = "invalid"
        result["parse_error"] = "Filename has leading/trailing whitespace"
        return result

    if " " in file_name_original:
        result["parse_status"] = "invalid"
        result["parse_error"] = "Filename contains whitespace"
        return result

    match = EA_FILENAME_PATTERN.match(file_name_original)

    if not match:
        result["parse_status"] = "invalid"
        result["parse_error"] = (
            "Filename does not match pattern: "
            "SYMBOL_EA_NUMBER_STRATEGY_ID_DIRECTION_TIMEFRAME.ext"
        )
        return result

    data = match.groupdict()

    result["symbol_from_filename"] = data["symbol"]
    result["ea_number"] = int(data["ea_number"])
    result["strategy_id"] = data["strategy_id"]
    result["direction"] = data["direction"]
    result["timeframe"] = data["timeframe"]
    result["extension"] = data["extension"].lower()

    if data["symbol"] != symbol_from_folder:
        result["parse_status"] = "warning"
        result["parse_error"] = (
            f"Symbol folder mismatch: folder={symbol_from_folder}, filename={data['symbol']}"
        )

    return result


def insert_inventory_row(conn: sqlite3.Connection, item: Dict[str, object]) -> None:
    now = utc_now()

    conn.execute(
        """
        INSERT INTO ea_file_inventory (
            file_path,
            file_name,
            symbol_from_folder,
            symbol_from_filename,
            ea_number,
            strategy_id,
            direction,
            timeframe,
            extension,
            parse_status,
            parse_error,
            discovered_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            item["file_path"],
            item["file_name"],
            item["symbol_from_folder"],
            item["symbol_from_filename"],
            item["ea_number"],
            item["strategy_id"],
            item["direction"],
            item["timeframe"],
            item["extension"],
            item["parse_status"],
            item["parse_error"],
            now,
            now,
        ),
    )


def fetch_issue_rows(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT
            file_name,
            symbol_from_folder,
            symbol_from_filename,
            parse_status,
            parse_error
        FROM ea_file_inventory
        WHERE parse_status != 'valid'
        ORDER BY parse_status, file_name;
        """
    ).fetchall()


def print_issue_report(issue_rows: List[sqlite3.Row]) -> None:
    print("\n" + "=" * 100)
    print("EA INVENTORY ISSUES")
    print("=" * 100)

    if not issue_rows:
        print("No invalid or warning files found.")
        print("=" * 100)
        return

    invalid_rows = [row for row in issue_rows if row["parse_status"] == "invalid"]
    warning_rows = [row for row in issue_rows if row["parse_status"] == "warning"]

    if invalid_rows:
        print("\nINVALID FILES")
        print("-" * 100)
        for index, row in enumerate(invalid_rows, start=1):
            print(f"\n[{index}] {row['file_name']}")
            print(f"Folder Symbol   : {row['symbol_from_folder']}")
            print(f"Filename Symbol : {row['symbol_from_filename']}")
            print(f"Reason          : {row['parse_error']}")

    if warning_rows:
        print("\nWARNING FILES")
        print("-" * 100)
        for index, row in enumerate(warning_rows, start=1):
            print(f"\n[{index}] {row['file_name']}")
            print(f"Folder Symbol   : {row['symbol_from_folder']}")
            print(f"Filename Symbol : {row['symbol_from_filename']}")
            print(f"Reason          : {row['parse_error']}")

    print("\n" + "=" * 100)
    print(f"Total Issues : {len(issue_rows)}")
    print(f"Invalid      : {len(invalid_rows)}")
    print(f"Warnings     : {len(warning_rows)}")
    print("=" * 100)


def sync_ea_inventory_to_db(root: Path) -> Dict[str, object]:
    paths = get_paths(root)
    validate_paths(paths)

    files = discover_ea_files(paths["ea_root"])

    conn = connect_db(paths["db_path"])

    try:
        create_ea_file_inventory_table(conn)
        clear_ea_file_inventory(conn)

        valid_count = 0
        warning_count = 0
        invalid_count = 0

        for file_path in files:
            item = parse_ea_filename(file_path)
            insert_inventory_row(conn, item)

            if item["parse_status"] == "valid":
                valid_count += 1
            elif item["parse_status"] == "warning":
                warning_count += 1
            else:
                invalid_count += 1

        conn.commit()

        issue_rows = fetch_issue_rows(conn)

        summary = {
            "files_scanned": len(files),
            "valid_files": valid_count,
            "warning_files": warning_count,
            "invalid_files": invalid_count,
            "db_path": str(paths["db_path"]),
            "ea_root": str(paths["ea_root"]),
            "table_updated": "ea_file_inventory",
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

    logging.info("START | sync_ea_inventory_to_db")

    root = find_quant_root()
    logging.info("INPUT_LOADED | QUANT OS root: %s", root)

    logging.info("PROCESSING_STARTED")

    summary = sync_ea_inventory_to_db(root)

    logging.info("PROCESSING_COMPLETED")
    logging.info("OUTPUT_WRITTEN | %s", summary)
    logging.info("END")


if __name__ == "__main__":
    main()
