# -*- coding: utf-8 -*-
"""
Demo_Account_Combiner.py

QUANT OS - Trades Processing Engine

Ziel:
- Liest alle normalisierten DEMO-Account-Outputs aus:
  INFRASTRUCTURE_LAYER/Storage/2_Baseline/Trades/Live/account_*_DEMO/<strategy_bucket>/trades.db

- Kombiniert alle kurzlebigen FTMO-Demo-Accounts zu einem logischen Demo-Account:
  INFRASTRUCTURE_LAYER/Storage/2_Baseline/Trades/Live/account_COMBINED_DEMO/<strategy_bucket>/trades.db

- Gruppiert nach Strategie-Bucket, nicht nach temporärer Account-ID.
- Sortiert Trades sauber nach close_time_utc / open_time_utc.
- Bewahrt die Original-Account-ID in source_account_id.
- Setzt account_id auf COMBINED_DEMO, damit Backend Analytics und Frontend ein zusammenhängendes Demo-Konto sehen.
- Erzeugt keine Analytics-Tabellen. Output ist nur trades + Audit-Dateien.

Processing bleibt damit sauber:
Normalizer -> trades.db/trades pro Account und Strategie
Combiner   -> trades.db/trades für account_COMBINED_DEMO pro Strategie
Analytics  -> KPIs, Equity, Drawdown, Daily/Weekly/Monthly usw.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

INPUT_DB_FILENAME = "trades.db"
INPUT_TABLE_NAME = "trades"
OUTPUT_DB_FILENAME = "trades.db"
OUTPUT_TABLE_NAME = "trades"

COMBINED_ACCOUNT_ID = "COMBINED_DEMO"
COMBINED_ACCOUNT_FOLDER = "account_COMBINED_DEMO"

# True = account_COMBINED_DEMO wird vor jedem Lauf komplett neu erzeugt.
CLEAN_OUTPUT_BEFORE_EXPORT = True

# Quelle liegt bei dir aktuell unter Baseline/Trades/Live, auch für DEMO-Accounts.
TRADE_AREA = "Live"

DATE_RANGE_RE = re.compile(r"_(\d{4}-\d{2}-\d{2})_to_(\d{4}-\d{2}-\d{2})$")


# ============================================================
# PATHS
# ============================================================

def find_quant_root(start: Path) -> Path:
    required_dirs = [
        "BACKEND_LAYER",
        "CONTROL_PLANE",
        "FRONTEND_LAYER",
        "INFRASTRUCTURE_LAYER",
        "MANAGEMENT_LAYER",
    ]

    for p in [start.resolve()] + list(start.resolve().parents):
        if all((p / name).exists() for name in required_dirs):
            return p

    raise RuntimeError(
        "Quant2-main root nicht gefunden. Erwartet Ordner: "
        "BACKEND_LAYER, CONTROL_PLANE, FRONTEND_LAYER, INFRASTRUCTURE_LAYER, MANAGEMENT_LAYER."
    )


SCRIPT_PATH = Path(__file__).resolve()
QUANT_ROOT = find_quant_root(SCRIPT_PATH)

STORAGE_DIR = QUANT_ROOT / "INFRASTRUCTURE_LAYER" / "Storage"
BASELINE_TRADES_ROOT = STORAGE_DIR / "2_Baseline" / "Trades" / TRADE_AREA
OUTPUT_COMBINED_ROOT = BASELINE_TRADES_ROOT / COMBINED_ACCOUNT_FOLDER


# ============================================================
# HELPERS
# ============================================================

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def ts_now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S%z")


def sanitize_name(value: object) -> str:
    s = str(value).strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._ ")
    return s[:200] if s else "UNKNOWN"


def parse_account_id_from_folder(account_dir: Path) -> str:
    name = account_dir.name
    if name.startswith("account_"):
        return name[len("account_") :]
    return name


def strip_date_range_from_bucket(bucket_name: str) -> str:
    return DATE_RANGE_RE.sub("", bucket_name)


def extract_date_str(series: pd.Series, mode: str) -> str:
    dt = pd.to_datetime(series, utc=True, errors="coerce").dropna()
    if dt.empty:
        return "UNKNOWN"
    value = dt.min() if mode == "min" else dt.max()
    return value.strftime("%Y-%m-%d")


def read_sqlite_table(db_path: Path, table_name: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    finally:
        conn.close()


def write_sqlite_table_replace(db_path: Path, table_name: str, df: pd.DataFrame) -> None:
    ensure_dir(db_path.parent)
    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()
    finally:
        conn.close()


def table_exists(db_path: Path, table_name: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


# ============================================================
# DISCOVERY
# ============================================================

@dataclass(frozen=True)
class StrategyDbRef:
    source_account_folder: str
    source_account_id: str
    bucket_name: str
    bucket_key: str
    db_path: Path


def discover_demo_strategy_dbs(root: Path) -> List[StrategyDbRef]:
    if not root.exists():
        raise FileNotFoundError(f"Baseline Trades Root nicht gefunden: {root}")

    refs: List[StrategyDbRef] = []

    account_dirs = sorted(
        p for p in root.iterdir()
        if p.is_dir()
        and p.name.startswith("account_")
        and p.name.endswith("_DEMO")
        and p.name != COMBINED_ACCOUNT_FOLDER
    )

    for account_dir in account_dirs:
        source_account_id = parse_account_id_from_folder(account_dir)

        for strategy_dir in sorted(p for p in account_dir.iterdir() if p.is_dir()):
            db_path = strategy_dir / INPUT_DB_FILENAME
            if not db_path.exists():
                continue
            if not table_exists(db_path, INPUT_TABLE_NAME):
                continue

            bucket_name = strategy_dir.name
            bucket_key = strip_date_range_from_bucket(bucket_name)

            refs.append(
                StrategyDbRef(
                    source_account_folder=account_dir.name,
                    source_account_id=source_account_id,
                    bucket_name=bucket_name,
                    bucket_key=bucket_key,
                    db_path=db_path,
                )
            )

    return refs


# ============================================================
# NORMALIZATION FOR COMBINE
# ============================================================

def normalize_trade_frame(df: pd.DataFrame, ref: StrategyDbRef) -> pd.DataFrame:
    out = df.copy()

    # Original-Account nie verlieren.
    if "source_account_id" not in out.columns:
        out["source_account_id"] = ref.source_account_id
    else:
        out["source_account_id"] = out["source_account_id"].fillna(ref.source_account_id).astype(str)

    out["source_account_folder"] = ref.source_account_folder
    out["source_bucket"] = ref.bucket_name
    out["combined_account_id"] = COMBINED_ACCOUNT_ID

    # Für Frontend/Analytics als ein logisches Demo-Konto behandeln.
    out["account_id"] = COMBINED_ACCOUNT_ID

    # Zeitspalten robust normalisieren.
    for col in ["open_time_utc", "close_time_utc"]:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], utc=True, errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S%z")

    # Numerische Kernfelder robust machen.
    for col in [
        "entry_price", "exit_price", "price_delta", "volume_in", "volume_out",
        "profit_sum", "swap_sum", "commission_sum", "net_sum", "magic",
        "sl", "tp", "best_floating_pnl", "worst_floating_pnl",
        "max_favorable_points_live", "max_adverse_points_live",
    ]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    # Kombinierte eindeutige ID.
    id_parts = []
    for col in ["source_account_id", "position_id", "close_ticket", "open_time_utc", "close_time_utc"]:
        if col in out.columns:
            id_parts.append(out[col].astype(str))

    if id_parts:
        combined = id_parts[0]
        for part in id_parts[1:]:
            combined = combined + "|" + part
        out["combined_trade_id"] = combined
    else:
        out["combined_trade_id"] = ref.source_account_id + "|" + ref.bucket_name + "|" + out.index.astype(str)

    return out


def combine_group(refs: List[StrategyDbRef]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    audit_rows: List[dict] = []

    for ref in refs:
        try:
            raw = read_sqlite_table(ref.db_path, INPUT_TABLE_NAME)
            normalized = normalize_trade_frame(raw, ref)
            frames.append(normalized)

            audit_rows.append(
                {
                    "status": "OK",
                    "source_account_folder": ref.source_account_folder,
                    "source_account_id": ref.source_account_id,
                    "source_bucket": ref.bucket_name,
                    "bucket_key": ref.bucket_key,
                    "db_path": str(ref.db_path),
                    "rows_read": int(len(raw)),
                    "error": "",
                }
            )

        except Exception as exc:
            audit_rows.append(
                {
                    "status": "ERROR",
                    "source_account_folder": ref.source_account_folder,
                    "source_account_id": ref.source_account_id,
                    "source_bucket": ref.bucket_name,
                    "bucket_key": ref.bucket_key,
                    "db_path": str(ref.db_path),
                    "rows_read": 0,
                    "error": repr(exc),
                }
            )
            traceback.print_exc()

    if not frames:
        return pd.DataFrame(), pd.DataFrame(audit_rows)

    combined = pd.concat(frames, ignore_index=True, sort=False)

    # Duplikate entfernen, ohne echte verschiedene Trades aus verschiedenen Accounts zu verlieren.
    if "combined_trade_id" in combined.columns:
        combined = combined.drop_duplicates(subset=["combined_trade_id"], keep="last")
    else:
        dedupe_cols = [c for c in ["source_account_id", "position_id", "close_ticket"] if c in combined.columns]
        if dedupe_cols:
            combined = combined.drop_duplicates(subset=dedupe_cols, keep="last")

    # Saubere chronologische Reihenfolge.
    sort_cols = [c for c in ["close_time_utc", "open_time_utc", "source_account_id", "position_id", "close_ticket"] if c in combined.columns]
    if sort_cols:
        combined = combined.sort_values(sort_cols).reset_index(drop=True)

    return combined, pd.DataFrame(audit_rows)


# ============================================================
# OUTPUT
# ============================================================

def create_trades_indexes(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        index_sql = [
            "CREATE INDEX IF NOT EXISTS idx_trades_close_time ON trades(close_time_utc)",
            "CREATE INDEX IF NOT EXISTS idx_trades_open_time ON trades(open_time_utc)",
            "CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_source_account_id ON trades(source_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol_norm ON trades(symbol_norm)",
            "CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_magic ON trades(magic)",
            "CREATE INDEX IF NOT EXISTS idx_trades_close_ticket ON trades(close_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_trades_combined_trade_id ON trades(combined_trade_id)",
        ]

        for sql in index_sql:
            try:
                cur.execute(sql)
            except sqlite3.OperationalError:
                # Falls einzelne Spalten in älteren Normalizer-Outputs fehlen.
                pass

        conn.commit()
    finally:
        conn.close()


def make_output_bucket_name(bucket_key: str, trades: pd.DataFrame) -> str:
    if "close_time_utc" in trades.columns:
        start = extract_date_str(trades["close_time_utc"], "min")
        end = extract_date_str(trades["close_time_utc"], "max")
    elif "open_time_utc" in trades.columns:
        start = extract_date_str(trades["open_time_utc"], "min")
        end = extract_date_str(trades["open_time_utc"], "max")
    else:
        start = "UNKNOWN"
        end = "UNKNOWN"

    return sanitize_name(f"{bucket_key}_{start}_to_{end}")


def export_combined_strategy(bucket_key: str, trades: pd.DataFrame) -> Path:
    output_bucket_name = make_output_bucket_name(bucket_key, trades)
    output_dir = OUTPUT_COMBINED_ROOT / output_bucket_name
    output_db = output_dir / OUTPUT_DB_FILENAME

    ensure_dir(output_dir)
    write_sqlite_table_replace(output_db, OUTPUT_TABLE_NAME, trades)
    create_trades_indexes(output_db)

    return output_db


def export_audits(all_audit: pd.DataFrame, summary: pd.DataFrame) -> None:
    ensure_dir(OUTPUT_COMBINED_ROOT)
    all_audit.to_csv(OUTPUT_COMBINED_ROOT / "demo_combiner_audit_full.csv", index=False)
    summary.to_csv(OUTPUT_COMBINED_ROOT / "demo_combiner_summary.csv", index=False)


# ============================================================
# MAIN
# ============================================================

def run() -> None:
    print("=" * 80)
    print("QUANT OS - Demo Account Combiner")
    print("=" * 80)
    print(f"Quant Root:        {QUANT_ROOT}")
    print(f"Input Root:        {BASELINE_TRADES_ROOT}")
    print(f"Output Root:       {OUTPUT_COMBINED_ROOT}")
    print(f"Combined Account:  {COMBINED_ACCOUNT_ID}")
    print(f"Run UTC:           {ts_now_utc()}")
    print("=" * 80)

    refs = discover_demo_strategy_dbs(BASELINE_TRADES_ROOT)

    if not refs:
        print("Keine DEMO trades.db Dateien gefunden.")
        return

    if CLEAN_OUTPUT_BEFORE_EXPORT and OUTPUT_COMBINED_ROOT.exists():
        shutil.rmtree(OUTPUT_COMBINED_ROOT)

    grouped: Dict[str, List[StrategyDbRef]] = {}
    for ref in refs:
        grouped.setdefault(ref.bucket_key, []).append(ref)

    all_audits: List[pd.DataFrame] = []
    summary_rows: List[dict] = []

    for bucket_key, group_refs in sorted(grouped.items()):
        combined, audit = combine_group(group_refs)
        all_audits.append(audit)

        if combined.empty:
            summary_rows.append(
                {
                    "bucket_key": bucket_key,
                    "status": "EMPTY",
                    "source_strategy_dbs": len(group_refs),
                    "source_accounts": ",".join(sorted({r.source_account_id for r in group_refs})),
                    "rows_written": 0,
                    "output_db": "",
                    "first_close_time_utc": "",
                    "last_close_time_utc": "",
                }
            )
            continue

        output_db = export_combined_strategy(bucket_key, combined)

        first_close = ""
        last_close = ""
        if "close_time_utc" in combined.columns:
            dt = pd.to_datetime(combined["close_time_utc"], utc=True, errors="coerce").dropna()
            if not dt.empty:
                first_close = dt.min().strftime("%Y-%m-%d %H:%M:%S%z")
                last_close = dt.max().strftime("%Y-%m-%d %H:%M:%S%z")

        summary_rows.append(
            {
                "bucket_key": bucket_key,
                "status": "OK",
                "source_strategy_dbs": len(group_refs),
                "source_accounts": ",".join(sorted({r.source_account_id for r in group_refs})),
                "rows_written": int(len(combined)),
                "output_db": str(output_db),
                "first_close_time_utc": first_close,
                "last_close_time_utc": last_close,
            }
        )

        print(f"OK  {bucket_key} -> {len(combined)} Trades")

    all_audit_df = pd.concat(all_audits, ignore_index=True, sort=False) if all_audits else pd.DataFrame()
    summary_df = pd.DataFrame(summary_rows)
    export_audits(all_audit_df, summary_df)

    print("=" * 80)
    print("FERTIG")
    print(f"Strategien kombiniert: {len(summary_df[summary_df['status'] == 'OK']) if not summary_df.empty else 0}")
    print(f"Audit: {OUTPUT_COMBINED_ROOT / 'demo_combiner_audit_full.csv'}")
    print(f"Summary: {OUTPUT_COMBINED_ROOT / 'demo_combiner_summary.csv'}")
    print("=" * 80)


if __name__ == "__main__":
    run()
