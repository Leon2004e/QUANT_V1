# -*- coding: utf-8 -*-
"""
Live_Trade_Normalizer.py

Clean QUANT OS Live Trade Normalizer

Ziel:
- Liest Live closed_trades.db aus:
  INFRASTRUCTURE_LAYER/Storage/1_Pipeline/Trades/Live/account_*/closed_trades.db

- Mappt zuerst die komplette Historie.
- Wendet danach erst den Cutoff an:
  close_time_utc >= 2026-02-22 00:00:00 UTC

- Exportiert nur:
  1) trades.db pro Strategie-Bucket mit NUR Tabelle: trades
  2) mapping_audit_full.csv pro Account

Kein runtime Ordner.
Keine State-Datei.
Keine unmapped_summary.csv.
Keine unmapped_trades.csv.
Keine not_exportable*.csv.
Keine mapping_diagnostics.db.

Mapping-Priorität:
1) Quant_System.db / ea_file_inventory über symbol_norm + magic + direction
2) EA-Dateiname fallback über symbol + magic + strategy_id + side + timeframe
3) Strategy-ID im Kommentar, nur wenn im EA-Inventar bekannt oder kein Inventar vorhanden
4) Previous-trade inference für [sl]/[tp]/leere Kommentare
5) Unique cluster inference über account_id + symbol_norm + magic + direction
6) Export-Regeln + BOTH-Bucket
"""

from __future__ import annotations

import re
import shutil
import sqlite3
import traceback
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


# ============================================================
# CONFIG
# ============================================================

GLOBAL_CUTOFF_DATE_UTC = pd.Timestamp("2026-02-22 00:00:00", tz="UTC")
INPUT_DB_FILENAME = "closed_trades.db"
INPUT_TABLE_NAME = "closed_trades"
OUTPUT_DB_FILENAME = "trades.db"

BAD_MAGIC_VALUES = {0, 11111}
CLEAN_OUTPUT_ACCOUNT_DIR_BEFORE_EXPORT = True


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
INPUT_LIVE_ROOT = STORAGE_DIR / "1_Pipeline" / "Trades" / "Live"
OUTPUT_LIVE_ROOT = STORAGE_DIR / "2_Baseline" / "Trades" / "Live"

STRATEGY_EA_ROOTS = [
    STORAGE_DIR / "1_Pipeline" / "Strategy" / "Strategy_EA",
    STORAGE_DIR / "1_Pipeline" / "Strategy_EA",
    STORAGE_DIR / "6_System" / "EA",
]

QUANT_SYSTEM_DB_CANDIDATES = [
    QUANT_ROOT / "CONTROL_PLANE" / "Database" / "Quant_System.db",
    QUANT_ROOT / "CONTROL_PLANE" / "Databases" / "Quant_System.db",
    QUANT_ROOT / "CONTROL_PLANE" / "Quant_System.db",
    QUANT_ROOT / "CONTROL_PLANE" / "QUANT_SYSTEM.db",
    STORAGE_DIR / "6_System" / "Quant_System.db",
    STORAGE_DIR / "6_System" / "QUANT_SYSTEM.db",
]

QUANT_SYSTEM_DB = next((p for p in QUANT_SYSTEM_DB_CANDIDATES if p.exists()), None)


# ============================================================
# SCHEMA
# ============================================================

TRADES_REQUIRED_COLS = [
    "account_id",
    "position_id",
    "symbol",
    "direction",
    "open_time_utc",
    "close_time_utc",
    "entry_price",
    "exit_price",
    "price_delta",
    "volume_in",
    "volume_out",
    "profit_sum",
    "swap_sum",
    "commission_sum",
    "net_sum",
    "magic",
    "comment_last",
    "close_ticket",
]

TRADES_OPTIONAL_COLS = [
    "sl",
    "tp",
    "best_floating_pnl",
    "worst_floating_pnl",
    "best_price_seen_live",
    "worst_price_seen_live",
    "max_favorable_points_live",
    "max_adverse_points_live",
    "account_type",
    "server",
]

TRADES_ALL_COLS = TRADES_REQUIRED_COLS + TRADES_OPTIONAL_COLS


# ============================================================
# REGEX / NORMALIZATION
# ============================================================

STRAT_DOT_RE = re.compile(
    r"\bStrategy\s+([0-9]+(?:\.[0-9]+){1,3})\b",
    re.IGNORECASE,
)

STRAT_UNDERSCORE_RE = re.compile(
    r"(?:WF_Matrix_)?Strategy_([0-9]+(?:_[0-9]+){1,3})\b",
    re.IGNORECASE,
)

EA_FILENAME_RE = re.compile(
    r"^(?P<symbol>.+?)_(?P<magic>\d+)_(?P<strategy_id>.+?)_"
    r"(?P<side>BUY|SELL|BOTH)_(?P<timeframe>[A-Z0-9]+)\.(?:mq5|ex5)$",
    re.IGNORECASE,
)

KNOWN_BASE_SYMBOLS = [
    "AUDJPY", "CADJPY", "CHFJPY", "EURJPY", "GBPJPY", "NZDJPY", "USDJPY",
    "EURGBP", "AUDNZD",
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
    "XAUUSD", "XAGUSD",
    "USOIL", "UKOIL",
    "US500", "US100", "US30", "GER40", "DAX", "EU50", "US2000",
    "BTCUSD", "ETHUSD",
]

BROKER_SUFFIXES = [
    ".PRO", ".CASH", ".RAW", ".ECN", ".R", ".M", ".I", ".A", ".B",
    "PRO", "CASH", "RAW", "ECN",
]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def is_missing_text(value: Any) -> bool:
    return str(value).strip() in {"", "nan", "None", "NaN", "<NA>"}


def sanitize_name(value: object) -> str:
    s = str(value).strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", s)
    s = re.sub(r"\s+", "_", s)
    s = s.strip("._ ")
    return s[:200] if s else "UNKNOWN"


def normalize_direction(value: object) -> str:
    x = str(value).strip().upper()

    if x in {"BUY", "LONG", "B", "0"}:
        return "BUY"

    if x in {"SELL", "SHORT", "S", "1"}:
        return "SELL"

    return x


def normalize_symbol(value: object) -> str:
    raw = str(value).strip().upper()

    if not raw:
        return ""

    s = raw.replace("/", "").replace("-", "").replace("_", "")

    for suffix in BROKER_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]

    compact = re.sub(r"[^A-Z0-9]", "", s)

    for base in sorted(KNOWN_BASE_SYMBOLS, key=len, reverse=True):
        b = re.sub(r"[^A-Z0-9]", "", base.upper())

        if compact == b:
            return b

        if compact.startswith(b):
            return b

    letters = re.sub(r"[^A-Z]", "", compact)
    return letters[:6] if len(letters) >= 6 else letters


def is_valid_strategy_id(strategy_id: object) -> bool:
    s = str(strategy_id).strip()

    if s in {"", "nan", "None", "NaN", "<NA>", "0", "11111"}:
        return False

    return bool(re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", s))


def parse_strategy_from_comment(comment: object) -> Optional[str]:
    text = str(comment).strip()

    if is_missing_text(text):
        return None

    m = STRAT_DOT_RE.search(text)
    if m:
        sid = m.group(1).strip()
        return sid if is_valid_strategy_id(sid) else None

    m = STRAT_UNDERSCORE_RE.search(text)
    if m:
        sid = m.group(1).replace("_", ".").strip()
        return sid if is_valid_strategy_id(sid) else None

    return None


def is_sl_tp_or_empty(comment: object) -> bool:
    text = str(comment).strip().lower()
    return text == "" or text.startswith("[sl") or text.startswith("[tp")


def safe_int_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def safe_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)


def safe_optional_float_series(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").astype(float)


def ts_to_str(ts: Any) -> str:
    if ts is None or pd.isna(ts):
        return ""

    t = pd.Timestamp(ts)

    if t.tzinfo is None:
        t = t.tz_localize("UTC")
    else:
        t = t.tz_convert("UTC")

    return t.isoformat()


# ============================================================
# EA MAP
# ============================================================

@dataclass(frozen=True)
class EAMapRow:
    strategy_id: str
    symbol: str
    symbol_norm: str
    magic: int
    match_direction: str
    strategy_side: str
    bucket_side: str
    timeframe: str
    ea_filename: str
    ea_path: str
    source: str


def _make_ea_rows(
    *,
    strategy_id: str,
    symbol: str,
    magic: int,
    side: str,
    timeframe: str = "",
    ea_filename: str = "",
    ea_path: str = "",
    source: str = "",
) -> List[EAMapRow]:
    strategy_id = str(strategy_id).strip()
    symbol = str(symbol).strip()
    side = normalize_direction(side)
    timeframe = str(timeframe).strip().upper()
    ea_filename = str(ea_filename).strip()
    ea_path = str(ea_path).strip()

    if not is_valid_strategy_id(strategy_id):
        return []

    if magic in BAD_MAGIC_VALUES:
        return []

    symbol_norm = normalize_symbol(symbol)

    if not symbol_norm:
        return []

    if side == "BOTH":
        return [
            EAMapRow(strategy_id, symbol, symbol_norm, magic, "BUY", "BOTH", "BOTH", timeframe, ea_filename, ea_path, source),
            EAMapRow(strategy_id, symbol, symbol_norm, magic, "SELL", "BOTH", "BOTH", timeframe, ea_filename, ea_path, source),
        ]

    if side in {"BUY", "SELL"}:
        return [
            EAMapRow(strategy_id, symbol, symbol_norm, magic, side, side, side, timeframe, ea_filename, ea_path, source)
        ]

    return []


def read_ea_inventory() -> pd.DataFrame:
    if QUANT_SYSTEM_DB is None or not QUANT_SYSTEM_DB.exists():
        print("[WARN] Quant_System.db nicht gefunden. Nutze nur EA-Dateien als Fallback.")
        return pd.DataFrame()

    conn = sqlite3.connect(QUANT_SYSTEM_DB)

    try:
        tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)

        if "ea_file_inventory" not in set(tables["name"].astype(str)):
            print("[WARN] Tabelle ea_file_inventory nicht gefunden. Nutze nur EA-Dateien als Fallback.")
            return pd.DataFrame()

        return pd.read_sql_query('SELECT * FROM "ea_file_inventory"', conn)

    finally:
        conn.close()


def ea_rows_from_inventory(inv: pd.DataFrame) -> List[EAMapRow]:
    if inv.empty:
        return []

    required = {"strategy_id", "ea_number", "direction"}
    missing = required - set(inv.columns)

    if missing:
        print(f"[WARN] ea_file_inventory fehlt Spalten: {sorted(missing)}")
        return []

    rows: List[EAMapRow] = []

    for _, r in inv.iterrows():
        parse_status = str(r.get("parse_status", "")).strip().lower()

        if parse_status and parse_status not in {"valid", "warning"}:
            continue

        strategy_id = str(r.get("strategy_id", "")).strip()
        magic_raw = pd.to_numeric(r.get("ea_number"), errors="coerce")

        if pd.isna(magic_raw):
            continue

        magic = int(magic_raw)
        symbol = str(r.get("symbol_from_filename", "")).strip()

        if is_missing_text(symbol):
            symbol = str(r.get("symbol_from_folder", "")).strip()

        file_name = str(r.get("file_name", "")).strip()

        if is_missing_text(symbol) and file_name:
            m = EA_FILENAME_RE.match(file_name)
            if m:
                symbol = m.group("symbol")

        rows.extend(
            _make_ea_rows(
                strategy_id=strategy_id,
                symbol=symbol,
                magic=magic,
                side=str(r.get("direction", "")).strip(),
                timeframe=str(r.get("timeframe", "")).strip(),
                ea_filename=file_name,
                ea_path=str(r.get("file_path", "")).strip(),
                source="quant_system_db",
            )
        )

    return rows


def ea_rows_from_filesystem() -> List[EAMapRow]:
    rows: List[EAMapRow] = []
    seen: set = set()

    for root in STRATEGY_EA_ROOTS:
        if not root.exists():
            continue

        for p in list(root.rglob("*.mq5")) + list(root.rglob("*.ex5")):
            try:
                rp = p.resolve()
            except Exception:
                rp = p

            if rp in seen:
                continue

            seen.add(rp)
            m = EA_FILENAME_RE.match(p.name)

            if not m:
                continue

            try:
                magic = int(m.group("magic"))
            except Exception:
                continue

            rows.extend(
                _make_ea_rows(
                    strategy_id=m.group("strategy_id"),
                    symbol=m.group("symbol"),
                    magic=magic,
                    side=m.group("side"),
                    timeframe=m.group("timeframe"),
                    ea_filename=p.name,
                    ea_path=str(p),
                    source="filesystem",
                )
            )

    return rows


def build_ea_map() -> pd.DataFrame:
    rows = ea_rows_from_inventory(read_ea_inventory()) + ea_rows_from_filesystem()

    columns = [
        "strategy_id",
        "symbol",
        "symbol_norm",
        "magic",
        "match_direction",
        "strategy_side",
        "bucket_side",
        "timeframe",
        "ea_filename",
        "ea_path",
        "source",
    ]

    if not rows:
        return pd.DataFrame(columns=columns)

    df = pd.DataFrame([r.__dict__ for r in rows])

    df["magic"] = pd.to_numeric(df["magic"], errors="coerce").astype("Int64")

    for c in columns:
        if c not in df.columns:
            df[c] = ""

    for c in [
        "strategy_id",
        "symbol",
        "symbol_norm",
        "match_direction",
        "strategy_side",
        "bucket_side",
        "timeframe",
        "ea_filename",
        "ea_path",
        "source",
    ]:
        df[c] = df[c].astype(str).fillna("").str.strip()

    df["symbol_norm"] = df["symbol_norm"].str.upper()
    df["match_direction"] = df["match_direction"].str.upper()
    df["strategy_side"] = df["strategy_side"].str.upper()
    df["bucket_side"] = df["bucket_side"].str.upper()

    df["source_rank"] = df["source"].map({"quant_system_db": 0, "filesystem": 1}).fillna(9)
    df = df.sort_values(["source_rank", "symbol_norm", "magic", "match_direction", "strategy_id"])

    df = df.drop_duplicates(
        subset=["symbol_norm", "magic", "match_direction", "strategy_id"],
        keep="first",
    )

    return df[columns].reset_index(drop=True)


def build_ea_lookup(ea_map: pd.DataFrame) -> Dict[Tuple[str, int, str], Dict[str, Any]]:
    lookup: Dict[Tuple[str, int, str], Dict[str, Any]] = {}

    if ea_map.empty:
        return lookup

    for key, g in ea_map.groupby(["symbol_norm", "magic", "match_direction"], dropna=False):
        symbol_norm, magic, direction = key
        unique = g[
            ["strategy_id", "strategy_side", "bucket_side", "timeframe", "ea_filename", "source"]
        ].drop_duplicates()

        if len(unique) != 1:
            continue

        row = unique.iloc[0].to_dict()

        lookup[(str(symbol_norm), int(magic), str(direction))] = {
            "strategy_id": str(row["strategy_id"]),
            "strategy_side": str(row["strategy_side"]),
            "bucket_side": str(row["bucket_side"]),
            "timeframe": str(row.get("timeframe", "")),
            "ea_filename": str(row.get("ea_filename", "")),
            "source": str(row.get("source", "")),
        }

    return lookup


def build_valid_strategy_set(ea_map: pd.DataFrame) -> set:
    if ea_map.empty:
        return set()

    return set(
        str(x).strip()
        for x in ea_map["strategy_id"].dropna().astype(str).tolist()
        if is_valid_strategy_id(x)
    )


# ============================================================
# INPUT
# ============================================================

def read_closed_trades_db(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=TRADES_ALL_COLS)

    conn = sqlite3.connect(path)

    try:
        table_info = pd.read_sql_query(f"PRAGMA table_info({INPUT_TABLE_NAME})", conn)
        existing_cols = set(table_info["name"].astype(str).tolist())

        missing = [c for c in TRADES_REQUIRED_COLS if c not in existing_cols]

        if missing:
            raise ValueError(f"Missing required columns in {path}: {missing}")

        selected_cols = TRADES_REQUIRED_COLS + [c for c in TRADES_OPTIONAL_COLS if c in existing_cols]
        select_sql = ", ".join([f'"{c}"' for c in selected_cols])
        df = pd.read_sql_query(f'SELECT {select_sql} FROM "{INPUT_TABLE_NAME}"', conn)

    finally:
        conn.close()

    for c in TRADES_OPTIONAL_COLS:
        if c not in df.columns:
            df[c] = pd.NA

    df = df[TRADES_ALL_COLS].copy()

    for c in ["account_id", "position_id", "magic", "close_ticket"]:
        df[c] = safe_int_series(df[c])

    for c in [
        "entry_price",
        "exit_price",
        "price_delta",
        "volume_in",
        "volume_out",
        "profit_sum",
        "swap_sum",
        "commission_sum",
        "net_sum",
    ]:
        df[c] = safe_float_series(df[c])

    for c in [
        "sl",
        "tp",
        "best_floating_pnl",
        "worst_floating_pnl",
        "best_price_seen_live",
        "worst_price_seen_live",
        "max_favorable_points_live",
        "max_adverse_points_live",
    ]:
        df[c] = safe_optional_float_series(df[c])

    df["open_time_utc"] = pd.to_datetime(df["open_time_utc"], errors="coerce", utc=True)
    df["close_time_utc"] = pd.to_datetime(df["close_time_utc"], errors="coerce", utc=True)

    for c in ["symbol", "direction", "comment_last", "account_type", "server"]:
        df[c] = df[c].astype(str).fillna("").str.strip()

    df["direction"] = df["direction"].apply(normalize_direction)
    df["symbol_norm"] = df["symbol"].apply(normalize_symbol)
    df["strategy_id_from_comment"] = df["comment_last"].apply(parse_strategy_from_comment)
    df["raw_magic_is_bad"] = (
        pd.to_numeric(df["magic"], errors="coerce")
        .fillna(-999999)
        .astype(int)
        .isin(BAD_MAGIC_VALUES)
    )

    df = df.dropna(subset=["account_id", "position_id", "close_ticket", "close_time_utc"]).copy()

    return df.sort_values(
        ["account_id", "close_time_utc", "position_id", "close_ticket"]
    ).reset_index(drop=True)


# ============================================================
# MAPPING
# ============================================================

def initialize_mapping_cols(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    defaults = {
        "strategy_id": "",
        "strategy_side": "",
        "bucket_side": "",
        "timeframe": "",
        "ea_filename": "",
        "strategy_mapping_source": "",
        "strategy_mapping_confidence": "",
        "strategy_mapping_reason": "",
        "inference_sample_trades": 0,
        "inference_key": "",
        "canonical_magic": pd.NA,
        "canonical_bucket": "",
        "bucket_side_auto_reason": "",
        "is_exportable": False,
        "not_exportable_reason": "",
    }

    for c, v in defaults.items():
        d[c] = v

    return d


def map_by_ea_lookup(df: pd.DataFrame, ea_lookup: Dict[Tuple[str, int, str], Dict[str, Any]]) -> pd.DataFrame:
    d = df.copy()
    n = 0

    for idx, row in d.iterrows():
        if is_valid_strategy_id(row.get("strategy_id", "")):
            continue

        try:
            magic = int(row["magic"])
        except Exception:
            continue

        key = (
            str(row.get("symbol_norm", "")).upper(),
            magic,
            str(row.get("direction", "")).upper(),
        )

        match = ea_lookup.get(key)

        if match is None:
            continue

        d.at[idx, "strategy_id"] = match["strategy_id"]
        d.at[idx, "strategy_side"] = match["strategy_side"]
        d.at[idx, "bucket_side"] = match["bucket_side"]
        d.at[idx, "timeframe"] = match["timeframe"]
        d.at[idx, "ea_filename"] = match["ea_filename"]
        d.at[idx, "strategy_mapping_source"] = "ea_symbol_magic_direction"
        d.at[idx, "strategy_mapping_confidence"] = "HIGH"
        d.at[idx, "strategy_mapping_reason"] = f"exact_match_from_{match['source']}"
        n += 1

    print(f"[EA_MAPPING] newly_mapped={n}")
    return d


def map_by_comment(df: pd.DataFrame, valid_strategy_ids: set) -> pd.DataFrame:
    d = df.copy()
    n = 0

    for idx, row in d.iterrows():
        if is_valid_strategy_id(row.get("strategy_id", "")):
            continue

        sid = row.get("strategy_id_from_comment")

        if not is_valid_strategy_id(sid):
            continue

        if valid_strategy_ids and sid not in valid_strategy_ids:
            continue

        direction = str(row.get("direction", "")).upper()

        d.at[idx, "strategy_id"] = sid
        d.at[idx, "strategy_side"] = direction
        d.at[idx, "bucket_side"] = direction
        d.at[idx, "strategy_mapping_source"] = "comment_last"
        d.at[idx, "strategy_mapping_confidence"] = "HIGH"
        d.at[idx, "strategy_mapping_reason"] = "valid_strategy_id_in_comment"
        n += 1

    print(f"[COMMENT_MAPPING] newly_mapped={n}")
    return d


def infer_previous_trade(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d = d.sort_values(["account_id", "close_time_utc", "position_id", "close_ticket"]).reset_index(drop=True)

    last_known: Dict[Tuple[Any, str, Any, str], Dict[str, Any]] = {}
    n = 0

    for idx, row in d.iterrows():
        key = (
            row.get("account_id"),
            str(row.get("symbol_norm", "")).upper(),
            row.get("magic"),
            str(row.get("direction", "")).upper(),
        )

        if is_valid_strategy_id(row.get("strategy_id", "")):
            last_known[key] = {
                "strategy_id": row.get("strategy_id", ""),
                "strategy_side": row.get("strategy_side", ""),
                "bucket_side": row.get("bucket_side", ""),
                "timeframe": row.get("timeframe", ""),
                "ea_filename": row.get("ea_filename", ""),
            }
            continue

        if not is_sl_tp_or_empty(row.get("comment_last", "")):
            continue

        prev = last_known.get(key)

        if prev is None:
            continue

        d.at[idx, "strategy_id"] = prev["strategy_id"]
        d.at[idx, "strategy_side"] = prev["strategy_side"]
        d.at[idx, "bucket_side"] = prev["bucket_side"]
        d.at[idx, "timeframe"] = prev["timeframe"]
        d.at[idx, "ea_filename"] = prev["ea_filename"]
        d.at[idx, "strategy_mapping_source"] = "previous_trade_same_account_symbol_magic_direction"
        d.at[idx, "strategy_mapping_confidence"] = "MEDIUM_HIGH"
        d.at[idx, "strategy_mapping_reason"] = "sl_tp_or_empty_comment_inherited_from_previous_known_trade"
        d.at[idx, "inference_sample_trades"] = 1
        d.at[idx, "inference_key"] = "|".join(str(x) for x in key)
        n += 1

    print(f"[PREVIOUS_TRADE_INFERENCE] newly_mapped={n}")
    return d


def infer_unique_cluster(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    base = d[d["strategy_id"].apply(is_valid_strategy_id)].copy()

    if base.empty:
        print("[CLUSTER_INFERENCE] newly_mapped=0")
        return d

    lookup: Dict[Tuple[Any, str, Any, str], Dict[str, Any]] = {}

    for key, g in base.groupby(["account_id", "symbol_norm", "magic", "direction"], dropna=False):
        strategy_ids = sorted(set(g["strategy_id"].astype(str).tolist()))

        if len(strategy_ids) != 1:
            continue

        lookup[key] = {
            "strategy_id": strategy_ids[0],
            "strategy_side": ",".join(sorted(set(g["strategy_side"].astype(str).tolist()))),
            "bucket_side": ",".join(sorted(set(g["bucket_side"].astype(str).tolist()))),
            "timeframe": ",".join(sorted(set(g["timeframe"].astype(str).tolist()))),
            "ea_filename": ",".join(sorted(set(g["ea_filename"].astype(str).tolist()))),
            "sample": int(len(g)),
        }

    n = 0

    for idx, row in d.iterrows():
        if is_valid_strategy_id(row.get("strategy_id", "")):
            continue

        if not is_sl_tp_or_empty(row.get("comment_last", "")):
            continue

        key = (
            row.get("account_id"),
            str(row.get("symbol_norm", "")).upper(),
            row.get("magic"),
            str(row.get("direction", "")).upper(),
        )

        match = lookup.get(key)

        if match is None:
            continue

        d.at[idx, "strategy_id"] = match["strategy_id"]
        d.at[idx, "strategy_side"] = match["strategy_side"]
        d.at[idx, "bucket_side"] = match["bucket_side"]
        d.at[idx, "timeframe"] = match["timeframe"]
        d.at[idx, "ea_filename"] = match["ea_filename"]
        d.at[idx, "strategy_mapping_source"] = "cluster_account_symbol_magic_direction"
        d.at[idx, "strategy_mapping_confidence"] = "MEDIUM_HIGH"
        d.at[idx, "strategy_mapping_reason"] = "unique_strategy_in_same_account_symbol_magic_direction_cluster"
        d.at[idx, "inference_sample_trades"] = match["sample"]
        d.at[idx, "inference_key"] = "|".join(str(x) for x in key)
        n += 1

    print(f"[CLUSTER_INFERENCE] newly_mapped={n}")
    return d


def apply_export_rules_and_both(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    d["canonical_magic"] = pd.NA
    d["canonical_bucket"] = ""
    d["bucket_side_auto_reason"] = ""
    d["is_exportable"] = False
    d["not_exportable_reason"] = ""

    mapped_mask = d["strategy_id"].apply(is_valid_strategy_id)
    d.loc[~mapped_mask, "not_exportable_reason"] = "no_valid_strategy_id"

    if not mapped_mask.any():
        return d

    for key, idxs in d[mapped_mask].groupby(["account_id", "symbol_norm", "strategy_id", "magic"], dropna=False).groups.items():
        account_id, symbol_norm, strategy_id, magic = key

        try:
            canonical_magic = int(magic)
        except Exception:
            canonical_magic = None

        if canonical_magic is None or canonical_magic in BAD_MAGIC_VALUES:
            d.loc[idxs, "not_exportable_reason"] = "no_valid_canonical_magic"
            continue

        g = d.loc[idxs]
        directions = set(g["direction"].astype(str).str.upper().tolist())
        existing_sides = set(g["bucket_side"].astype(str).str.upper().tolist())

        if "BOTH" in existing_sides:
            final_side = "BOTH"
            reason = "ea_inventory_both"
        elif {"BUY", "SELL"}.issubset(directions):
            final_side = "BOTH"
            reason = "auto_both_same_account_symbol_strategy_magic"
        elif len(directions) == 1:
            final_side = next(iter(directions))
            reason = "single_direction"
        else:
            final_side = "BOTH"
            reason = "mixed_direction_same_account_symbol_strategy_magic"

        d.loc[idxs, "canonical_magic"] = canonical_magic
        d.loc[idxs, "bucket_side"] = final_side
        d.loc[idxs, "canonical_bucket"] = f"{symbol_norm}_{canonical_magic}_{strategy_id}_{final_side}"
        d.loc[idxs, "bucket_side_auto_reason"] = reason
        d.loc[idxs, "is_exportable"] = True
        d.loc[idxs, "not_exportable_reason"] = ""

    d["canonical_magic"] = pd.to_numeric(d["canonical_magic"], errors="coerce").astype("Int64")
    d["is_exportable"] = d["is_exportable"].astype(bool)

    return d


def map_trades(df: pd.DataFrame, ea_map: pd.DataFrame) -> pd.DataFrame:
    d = initialize_mapping_cols(df)

    ea_lookup = build_ea_lookup(ea_map)
    valid_strategy_ids = build_valid_strategy_set(ea_map)

    d = map_by_ea_lookup(d, ea_lookup)
    d = map_by_comment(d, valid_strategy_ids)
    d = infer_previous_trade(d)
    d = infer_unique_cluster(d)
    d = apply_export_rules_and_both(d)

    total = len(d)
    mapped = int(d["strategy_id"].apply(is_valid_strategy_id).sum())
    exportable = int(d["is_exportable"].sum())

    print(f"[MAPPING_RESULT] mapped={mapped}/{total} exportable={exportable}/{total}")
    return d


def apply_cutoff(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    d = df.copy()
    d["close_time_utc"] = pd.to_datetime(d["close_time_utc"], errors="coerce", utc=True)
    d = d.dropna(subset=["close_time_utc"])
    d = d[d["close_time_utc"] >= GLOBAL_CUTOFF_DATE_UTC].copy()

    print(
        f"[DATE_FILTER] cutoff={GLOBAL_CUTOFF_DATE_UTC.isoformat()} "
        f"before={before} after={len(d)} removed={before - len(d)}"
    )

    return d.reset_index(drop=True)


# ============================================================
# NORMALIZED TRADE OUTPUT HELPERS
# ============================================================

def bucket_trades(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["close_time_utc", "position_id", "close_ticket"]).reset_index(drop=True)


# ============================================================
# OUTPUT
# ============================================================

def sqlite_write_table_replace(db_path: Path, table_name: str, df: pd.DataFrame) -> None:
    ensure_dir(db_path.parent)

    conn = sqlite3.connect(db_path)

    try:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.commit()

    finally:
        conn.close()


def create_strategy_db_indexes(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)

    try:
        cur = conn.cursor()
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_trades_close_time ON trades(close_time_utc)",
            "CREATE INDEX IF NOT EXISTS idx_trades_close_ticket ON trades(close_ticket)",
            "CREATE INDEX IF NOT EXISTS idx_trades_position_id ON trades(position_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol_norm ON trades(symbol_norm)",
            "CREATE INDEX IF NOT EXISTS idx_trades_magic ON trades(magic)",
            "CREATE INDEX IF NOT EXISTS idx_trades_strategy_id ON trades(strategy_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_account_id ON trades(account_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_canonical_bucket ON trades(canonical_bucket)",
        ]

        for sql in indexes:
            cur.execute(sql)

        conn.commit()

    finally:
        conn.close()


def export_strategy_db(bucket_dir: Path, trades: pd.DataFrame) -> None:
    ensure_dir(bucket_dir)

    db_path = bucket_dir / OUTPUT_DB_FILENAME
    trades_out = bucket_trades(trades)

    # Normalizer-Verantwortung: ausschließlich normalisierte Trades speichern.
    # Keine KPI-, Daily-, Weekly- oder Monthly-Analytics im Normalizer.
    sqlite_write_table_replace(db_path, "trades", trades_out)

    create_strategy_db_indexes(db_path)


def export_mapping_audit_full(output_account_dir: Path, df: pd.DataFrame) -> None:
    ensure_dir(output_account_dir)

    cols = [
        "account_id",
        "position_id",
        "close_ticket",
        "symbol",
        "symbol_norm",
        "direction",
        "magic",
        "comment_last",
        "open_time_utc",
        "close_time_utc",
        "entry_price",
        "exit_price",
        "price_delta",
        "volume_in",
        "volume_out",
        "profit_sum",
        "swap_sum",
        "commission_sum",
        "net_sum",
        "sl",
        "tp",
        "account_type",
        "server",
        "strategy_id_from_comment",
        "raw_magic_is_bad",
        "strategy_id",
        "strategy_side",
        "bucket_side",
        "timeframe",
        "ea_filename",
        "strategy_mapping_source",
        "strategy_mapping_confidence",
        "strategy_mapping_reason",
        "inference_sample_trades",
        "inference_key",
        "canonical_magic",
        "canonical_bucket",
        "bucket_side_auto_reason",
        "is_exportable",
        "not_exportable_reason",
    ]

    existing = [c for c in cols if c in df.columns]
    audit = df[existing].copy()

    sort_cols = [
        c
        for c in ["symbol_norm", "magic", "direction", "close_time_utc", "position_id", "close_ticket"]
        if c in audit.columns
    ]

    if sort_cols:
        audit = audit.sort_values(sort_cols, na_position="last")

    audit.to_csv(output_account_dir / "mapping_audit_full.csv", index=False, encoding="utf-8-sig")


def clean_output_account_dir(output_account_dir: Path) -> None:
    if not CLEAN_OUTPUT_ACCOUNT_DIR_BEFORE_EXPORT:
        return

    if not output_account_dir.exists():
        return

    for child in output_account_dir.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        elif child.is_file():
            child.unlink()


def strategy_bucket_folder_name(
    symbol_norm: str,
    magic: object,
    strategy_id: str,
    side: str,
    trades: pd.DataFrame,
) -> str:
    close_times = pd.to_datetime(trades["close_time_utc"], errors="coerce", utc=True).dropna()

    if close_times.empty:
        start = "unknown"
        end = "unknown"
    else:
        start = close_times.min().strftime("%Y-%m-%d")
        end = close_times.max().strftime("%Y-%m-%d")

    return (
        f"{sanitize_name(symbol_norm)}_"
        f"{sanitize_name(magic)}_"
        f"{sanitize_name(strategy_id)}_"
        f"{sanitize_name(side)}_"
        f"{start}_to_{end}"
    )


def export_account(output_account_dir: Path, df: pd.DataFrame) -> Tuple[int, int]:
    ensure_dir(output_account_dir)
    clean_output_account_dir(output_account_dir)

    export_mapping_audit_full(output_account_dir, df)

    canonical_magic = pd.to_numeric(df["canonical_magic"], errors="coerce")

    valid = df[
        df["is_exportable"].astype(bool)
        & df["strategy_id"].apply(is_valid_strategy_id)
        & canonical_magic.notna()
        & ~canonical_magic.astype("Int64").isin(list(BAD_MAGIC_VALUES))
    ].copy()

    if valid.empty:
        return 0, len(df)

    bucket_count = 0

    for (symbol_norm, strategy_id, magic, side), g in valid.groupby(
        ["symbol_norm", "strategy_id", "canonical_magic", "bucket_side"],
        dropna=False,
        sort=True,
    ):
        folder = strategy_bucket_folder_name(symbol_norm, magic, strategy_id, side, g)
        bucket_dir = output_account_dir / folder
        export_strategy_db(bucket_dir, g)
        bucket_count += 1

    skipped = len(df) - len(valid)
    return bucket_count, skipped


# ============================================================
# PROCESSING
# ============================================================

def find_account_dirs(root: Path) -> List[Path]:
    if not root.exists():
        return []

    return sorted(
        [
            p for p in root.iterdir()
            if p.is_dir() and re.match(r"^account_\d+_(LIVE|DEMO)$", p.name, re.IGNORECASE)
        ],
        key=lambda x: x.name,
    )


def process_account(account_dir: Path, ea_map: pd.DataFrame) -> None:
    closed_path = account_dir / INPUT_DB_FILENAME

    if not closed_path.exists():
        print(f"[WARN] {account_dir.name}: {INPUT_DB_FILENAME} nicht gefunden")
        return

    df_all = read_closed_trades_db(closed_path)

    if df_all.empty:
        print(f"[INFO] {account_dir.name}: keine Trades")
        return

    print(f"[ACCOUNT_LOAD] {account_dir.name}: rows_all_history={len(df_all)}")

    df_all = map_trades(df_all, ea_map)
    df = apply_cutoff(df_all)

    mapped = int(df["strategy_id"].apply(is_valid_strategy_id).sum())
    exportable = int(df["is_exportable"].sum())
    unmapped = len(df) - mapped

    print(
        f"[ACCOUNT_AFTER_CUTOFF] {account_dir.name}: "
        f"rows={len(df)} mapped={mapped} exportable={exportable} unmapped={unmapped}"
    )

    output_account_dir = OUTPUT_LIVE_ROOT / account_dir.name
    bucket_count, skipped = export_account(output_account_dir, df)

    print(
        f"[OK] {account_dir.name}: buckets={bucket_count} skipped={skipped} "
        f"output={output_account_dir}"
    )


def run_once() -> None:
    ensure_dir(OUTPUT_LIVE_ROOT)

    print(f"[INFO] SCRIPT_PATH       = {SCRIPT_PATH}")
    print(f"[INFO] QUANT_ROOT        = {QUANT_ROOT}")
    print(f"[INFO] INPUT_LIVE_ROOT   = {INPUT_LIVE_ROOT}")
    print(f"[INFO] OUTPUT_LIVE_ROOT  = {OUTPUT_LIVE_ROOT}")
    print(f"[INFO] QUANT_SYSTEM_DB   = {QUANT_SYSTEM_DB if QUANT_SYSTEM_DB else 'not found'}")
    print(f"[INFO] CUTOFF            = {GLOBAL_CUTOFF_DATE_UTC}")
    print("[INFO] RUNTIME_STATE     = disabled")
    print("[INFO] EXTRA_DEBUG_FILES = disabled")
    print("[INFO] DEBUG_CSV         = mapping_audit_full.csv")

    ea_map = build_ea_map()

    print(f"[INFO] EA mapping rows    = {len(ea_map)}")

    if not ea_map.empty:
        print(f"[INFO] EA strategies      = {ea_map['strategy_id'].nunique()}")
        print(f"[INFO] EA BOTH rows       = {int((ea_map['bucket_side'] == 'BOTH').sum())}")

    accounts = find_account_dirs(INPUT_LIVE_ROOT)

    print(f"[INFO] Accounts found     = {len(accounts)}")

    for account_dir in accounts:
        try:
            process_account(account_dir, ea_map)
        except Exception as e:
            print(f"[ERROR] account failed: {account_dir.name} | {e}")
            traceback.print_exc()

    print(f"[DONE] {datetime.now(timezone.utc).isoformat(timespec='seconds')}")


def main() -> None:
    run_once()


if __name__ == "__main__":
    main()
