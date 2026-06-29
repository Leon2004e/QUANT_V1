# ============================================================
# CODE_REGISTRY
# script_id: ea_inventory_widget
# script_name: ea_inventory_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Widget
# purpose: EA Inventory Dashboard for QUANT_SYSTEM.db Building Block
# inputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory
# outputs: Tkinter widget panel
# upstream_data: ea_file_inventory
# downstream_data: main.py
# dependencies: tkinter, ttk, sqlite3, pathlib, os, subprocess, sys, csv
# schedule: manual
# version: v2.1.0
# last_reviewed: 2026-06-18
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, widget, ea-inventory, management-workspace, dashboard, excel-table
# notes: Mac/Windows-safe dark UI. Excel-like sortable table. Full visible filter system with scrollable inspector.
# ============================================================

from __future__ import annotations

import csv
import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


CODE_REGISTRY = {
    "script_id": "ea_inventory_widget",
    "script_name": "ea_inventory_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Widget",
    "purpose": "EA Inventory Dashboard for QUANT_SYSTEM.db Building Block",
    "inputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory",
    "outputs": "Tkinter widget panel",
    "upstream_data": "ea_file_inventory",
    "downstream_data": "main.py",
    "dependencies": "tkinter, ttk, sqlite3, pathlib, os, subprocess, sys, csv",
    "schedule": "manual",
    "version": "v2.1.0",
    "last_reviewed": "2026-06-18",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,widget,ea-inventory,management-workspace,dashboard,excel-table",
    "notes": "Mac/Windows-safe dark UI. Excel-like sortable table. Full visible filter system with scrollable inspector.",
}


# ============================================================
# DESIGN TOKENS
# ============================================================

BG = "#05080D"
PANEL = "#0B111B"
CARD = "#111827"
CARD_2 = "#0E1623"
CARD_3 = "#0A1019"
BORDER = "#263449"
BORDER_SOFT = "#1B2738"

TEXT = "#F4F7FB"
MUTED = "#9AA7B8"
DIM = "#64748B"

BLUE = "#3B82F6"
BLUE_DARK = "#0B4EDB"
GREEN = "#22C55E"
YELLOW = "#FACC15"
RED = "#EF4444"
PURPLE = "#8B5CF6"
CYAN = "#22D3EE"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_H1 = ("Helvetica", 15, "bold")
FONT_H2 = ("Helvetica", 11, "bold")
FONT_MAIN = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_XS = ("Helvetica", 8)


# ============================================================
# HELPERS
# ============================================================

def find_quant_root(start: Path) -> Path:
    current = start.resolve()

    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists():
            return path

    raise FileNotFoundError("QUANT OS root not found. Expected CONTROL_PLANE folder.")


def open_path(path: Path) -> None:
    if not path.exists():
        messagebox.showerror("File not found", str(path))
        return

    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def safe_int(value: Any) -> int:
    if value is None:
        return -10**12

    text = str(value).strip()

    if not text:
        return -10**12

    try:
        return int(float(text))
    except ValueError:
        return -10**12


def percent(part: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{part / total * 100:.1f}%"


# ============================================================
# CUSTOM MAC/WINDOWS SAFE CONTROLS
# ============================================================

class ActionButton(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        width: int = 118,
        height: int = 34,
        bg: str = CARD_2,
        fg: str = TEXT,
        border: str = BORDER,
        active_bg: str = "#172338",
    ):
        super().__init__(
            parent,
            bg=bg,
            width=width,
            height=height,
            highlightbackground=border,
            highlightthickness=1,
            cursor="hand2",
        )
        self.pack_propagate(False)

        self.command = command
        self.normal_bg = bg
        self.active_bg = active_bg

        self.label = tk.Label(
            self,
            text=text,
            bg=bg,
            fg=fg,
            font=FONT_SMALL,
            cursor="hand2",
        )
        self.label.pack(fill="both", expand=True)

        for widget in (self, self.label):
            widget.bind("<Button-1>", self._click)
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)

    def _click(self, _event=None) -> None:
        self.command()

    def _enter(self, _event=None) -> None:
        self.configure(bg=self.active_bg)
        self.label.configure(bg=self.active_bg)

    def _leave(self, _event=None) -> None:
        self.configure(bg=self.normal_bg)
        self.label.configure(bg=self.normal_bg)


class ClickCard(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        value: str,
        color: str,
        command: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=16,
            pady=13,
            height=86,
            cursor="hand2" if command else "",
        )
        self.pack_propagate(False)

        self.command = command
        self.normal_bg = CARD

        self.title_label = tk.Label(self, text=title, bg=CARD, fg=MUTED, font=FONT_XS)
        self.title_label.pack(anchor="w")

        self.value_label = tk.Label(
            self,
            text=value,
            bg=CARD,
            fg=color,
            font=("Helvetica", 21, "bold"),
        )
        self.value_label.pack(anchor="w", pady=(6, 0))

        self.sub_label = tk.Label(
            self,
            text="",
            bg=CARD,
            fg=MUTED,
            font=FONT_XS,
        )
        self.sub_label.pack(anchor="w", pady=(3, 0))

        tk.Label(self, text="●", bg=CARD, fg=color, font=FONT_XS).place(relx=0.95, rely=0.47)

        if command:
            for widget in (self, self.title_label, self.value_label, self.sub_label):
                widget.configure(cursor="hand2")
                widget.bind("<Button-1>", self._click)
                widget.bind("<Enter>", self._enter)
                widget.bind("<Leave>", self._leave)

    def _click(self, _event=None) -> None:
        if self.command:
            self.command()

    def _enter(self, _event=None) -> None:
        self.configure(bg="#172338")
        for w in [self.title_label, self.value_label, self.sub_label]:
            w.configure(bg="#172338")

    def _leave(self, _event=None) -> None:
        self.configure(bg=self.normal_bg)
        for w in [self.title_label, self.value_label, self.sub_label]:
            w.configure(bg=self.normal_bg)

    def set_value(self, value: Any, sub: str = "") -> None:
        self.value_label.configure(text=str(value))
        self.sub_label.configure(text=sub)


# ============================================================
# DATABASE SERVICE
# ============================================================

class EAInventoryDBService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def table_exists(self) -> bool:
        if not self.db_path.exists():
            return False

        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = 'ea_file_inventory'
                LIMIT 1;
                """
            ).fetchone()

        return row is not None

    def count(self, where: Optional[str] = None) -> int:
        if not self.table_exists():
            return 0

        sql = "SELECT COUNT(*) AS n FROM ea_file_inventory"
        if where:
            sql += " WHERE " + where

        with self.connect() as conn:
            row = conn.execute(sql).fetchone()

        return int(row["n"]) if row else 0

    def fetch_records(
        self,
        search: str = "",
        symbol_filter: str = "",
        status_filter: str = "",
        direction_filter: str = "",
        timeframe_filter: str = "",
        limit: int = 10000,
    ) -> List[Dict[str, Any]]:
        if not self.table_exists():
            return []

        sql = """
            SELECT
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
                file_path
            FROM ea_file_inventory
            WHERE 1 = 1
        """

        params: List[Any] = []

        if search.strip():
            s = f"%{search.strip()}%"
            sql += """
                AND (
                    CAST(file_name AS TEXT) LIKE ?
                    OR CAST(symbol_from_folder AS TEXT) LIKE ?
                    OR CAST(symbol_from_filename AS TEXT) LIKE ?
                    OR CAST(ea_number AS TEXT) LIKE ?
                    OR CAST(strategy_id AS TEXT) LIKE ?
                    OR CAST(direction AS TEXT) LIKE ?
                    OR CAST(timeframe AS TEXT) LIKE ?
                    OR CAST(parse_status AS TEXT) LIKE ?
                )
            """
            params.extend([s] * 8)

        if symbol_filter.strip():
            sql += " AND COALESCE(NULLIF(symbol_from_folder, ''), 'Unknown') = ?"
            params.append(symbol_filter.strip())

        if status_filter.strip():
            sql += " AND COALESCE(NULLIF(parse_status, ''), 'Unknown') = ?"
            params.append(status_filter.strip())

        if direction_filter.strip():
            sql += " AND COALESCE(NULLIF(direction, ''), 'Unknown') = ?"
            params.append(direction_filter.strip())

        if timeframe_filter.strip():
            sql += " AND COALESCE(NULLIF(timeframe, ''), 'Unknown') = ?"
            params.append(timeframe_filter.strip())

        sql += """
            ORDER BY
                COALESCE(NULLIF(symbol_from_folder, ''), 'Unknown'),
                CAST(ea_number AS INTEGER),
                CAST(strategy_id AS TEXT),
                file_name
            LIMIT ?
        """
        params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        records: List[Dict[str, Any]] = []

        for row in rows:
            records.append(
                {
                    "file_name": row["file_name"],
                    "folder_symbol": row["symbol_from_folder"],
                    "filename_symbol": row["symbol_from_filename"],
                    "ea_number": row["ea_number"],
                    "strategy_id": row["strategy_id"],
                    "direction": row["direction"],
                    "timeframe": row["timeframe"],
                    "extension": row["extension"],
                    "status": row["parse_status"],
                    "error": row["parse_error"],
                    "file_path": row["file_path"],
                }
            )

        return records

    def distribution(self, column: str, alias: str) -> List[Tuple[str, int]]:
        allowed = {
            "symbol_from_folder",
            "parse_status",
            "direction",
            "timeframe",
        }
        if column not in allowed or not self.table_exists():
            return []

        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT
                    COALESCE(NULLIF({column}, ''), 'Unknown') AS {alias},
                    COUNT(*) AS count
                FROM ea_file_inventory
                GROUP BY COALESCE(NULLIF({column}, ''), 'Unknown')
                ORDER BY count DESC, {alias} ASC;
                """
            ).fetchall()

        return [(str(row[alias]), int(row["count"])) for row in rows]

    def symbol_distribution(self) -> List[Tuple[str, int]]:
        return self.distribution("symbol_from_folder", "symbol")

    def status_distribution(self) -> List[Tuple[str, int]]:
        return self.distribution("parse_status", "status")

    def direction_distribution(self) -> List[Tuple[str, int]]:
        return self.distribution("direction", "direction")

    def timeframe_distribution(self) -> List[Tuple[str, int]]:
        return self.distribution("timeframe", "timeframe")


# ============================================================
# MAIN WIDGET
# ============================================================

class EAInventoryWidget(tk.Frame):
    """
    EA Inventory Dashboard.

    Features:
    - Mac/Windows-safe dark controls.
    - Excel-like sortable table.
    - Click column header to sort.
    - ea_number and strategy_id are sorted numerically.
    - Full filter system: symbol, status, direction, timeframe.
    - Filter panel is scrollable so every filter remains usable.
    """

    BREAK_FULL = 1380
    BREAK_DESKTOP = 1100
    BREAK_TABLET = 850

    NUMERIC_COLUMNS = {"ea_number", "strategy_id"}

    def __init__(self, parent: tk.Widget, db_path: Optional[Path] = None):
        super().__init__(parent, bg=BG)

        if db_path is None:
            root = find_quant_root(Path(__file__))
            db_path = root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db"

        self.db_path = db_path
        self.db = EAInventoryDBService(self.db_path)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Not Loaded")
        self.layout_var = tk.StringVar(value="Layout: initializing")
        self.filter_var = tk.StringVar(value="Filters: All")

        self.active_symbol_filter = ""
        self.active_status_filter = ""
        self.active_direction_filter = ""
        self.active_timeframe_filter = ""

        self.current_layout = ""
        self.current_orient = ""
        self.resize_after_id: Optional[str] = None
        self.lock_sash_after_layout = True

        self.rows_cache: List[Dict[str, Any]] = []
        self.item_to_record: Dict[str, Dict[str, Any]] = {}
        self.selected_file_path: Optional[Path] = None

        self.sort_column = "ea_number"
        self.sort_reverse = False

        self.metric_cards: Dict[str, ClickCard] = {}
        self.detail_labels: Dict[str, tk.Label] = {}

        self._setup_styles()
        self._build_dashboard()

        self.bind("<Configure>", self._on_resize)
        self.after(100, self.refresh)
        self.after(250, self.apply_responsive_layout)

    # -----------------------------
    # Style
    # -----------------------------

    def _setup_styles(self) -> None:
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "EA.Treeview",
            background=CARD_2,
            foreground=TEXT,
            fieldbackground=CARD_2,
            rowheight=31,
            font=FONT_SMALL,
            borderwidth=0,
            relief="flat",
        )

        style.configure(
            "EA.Treeview.Heading",
            background=CARD,
            foreground=MUTED,
            font=FONT_SMALL,
            borderwidth=0,
            relief="flat",
        )

        style.map(
            "EA.Treeview",
            background=[("selected", "#16345E")],
            foreground=[("selected", TEXT)],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=CARD,
            troughcolor=CARD_2,
            bordercolor=BORDER,
            arrowcolor=MUTED,
            darkcolor=CARD,
            lightcolor=CARD,
        )

        style.configure(
            "Horizontal.TScrollbar",
            background=CARD,
            troughcolor=CARD_2,
            bordercolor=BORDER,
            arrowcolor=MUTED,
            darkcolor=CARD,
            lightcolor=CARD,
        )

    # -----------------------------
    # Build
    # -----------------------------

    def _build_dashboard(self) -> None:
        self._build_header()
        self._build_metrics()
        self._build_toolbar()
        self._build_paned_area()

    def _build_header(self) -> None:
        self.header = tk.Frame(self, bg=BG)
        self.header.pack(fill="x", pady=(0, 10))

        left = tk.Frame(self.header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        title_row = tk.Frame(left, bg=BG)
        title_row.pack(anchor="w", fill="x")

        tk.Label(
            title_row,
            text="EA Inventory",
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE,
        ).pack(side="left")

        tk.Label(
            title_row,
            text="/ Infrastructure Storage",
            bg=BG,
            fg=BLUE,
            font=FONT_XS,
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        tk.Label(
            left,
            text="Read-only EA file inventory from QUANT_SYSTEM.db",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(6, 0))

        tk.Label(
            left,
            textvariable=self.filter_var,
            bg=BG,
            fg=BLUE,
            font=FONT_XS,
        ).pack(anchor="w", pady=(4, 0))

        right = tk.Frame(self.header, bg=BG)
        right.pack(side="right", anchor="ne")

        tk.Label(
            right,
            textvariable=self.layout_var,
            bg=BG,
            fg=MUTED,
            font=FONT_XS,
        ).pack(side="left", padx=(0, 12))

        status_box = tk.Frame(
            right,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=7,
        )
        status_box.pack(side="right")

        tk.Label(status_box, text="●", bg=CARD, fg=GREEN, font=FONT_XS).pack(side="left", padx=(0, 8))
        tk.Label(status_box, textvariable=self.status_var, bg=CARD, fg=TEXT, font=FONT_XS).pack(side="left")

    def _build_metrics(self) -> None:
        self.metrics_host = tk.Frame(self, bg=BG)
        self.metrics_host.pack(fill="x", pady=(0, 10))

        self.metric_cards["total"] = ClickCard(
            self.metrics_host,
            "TOTAL EA FILES",
            "0",
            BLUE,
            command=self.clear_all_filters,
        )
        self.metric_cards["valid"] = ClickCard(
            self.metrics_host,
            "VALID",
            "0",
            GREEN,
            command=lambda: self.apply_status_filter("valid"),
        )
        self.metric_cards["warning"] = ClickCard(
            self.metrics_host,
            "WARNINGS",
            "0",
            YELLOW,
            command=lambda: self.apply_status_filter("warning"),
        )
        self.metric_cards["invalid"] = ClickCard(
            self.metrics_host,
            "INVALID",
            "0",
            RED,
            command=lambda: self.apply_status_filter("invalid"),
        )

    def _build_toolbar(self) -> None:
        self.toolbar = tk.Frame(
            self,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=10,
        )
        self.toolbar.pack(fill="x", pady=(0, 10))

        self.search_box = tk.Frame(
            self.toolbar,
            bg=CARD_2,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

        tk.Label(
            self.search_box,
            text="Search",
            bg=CARD_2,
            fg=MUTED,
            font=FONT_XS,
        ).pack(side="left", padx=(12, 8))

        self.search_entry = tk.Entry(
            self.search_box,
            textvariable=self.search_var,
            bg=CARD_2,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_SMALL,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _event: self.refresh())

        self.btn_filter = ActionButton(
            self.toolbar,
            "Apply Filter",
            self.refresh,
            width=112,
            bg=BLUE_DARK,
            fg=TEXT,
            border=BLUE,
        )
        self.btn_clear = ActionButton(self.toolbar, "Clear Filters", self.clear_all_filters, width=112)
        self.btn_refresh = ActionButton(self.toolbar, "Refresh", self.refresh, width=90)
        self.btn_open = ActionButton(self.toolbar, "Open File", self.open_selected_file, width=96)
        self.btn_export = ActionButton(self.toolbar, "Export CSV", self.export_csv, width=100)

    def _build_paned_area(self) -> None:
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

        self.paned = tk.PanedWindow(
            self.body,
            orient=tk.HORIZONTAL,
            bg=BG,
            sashwidth=8,
            sashrelief="raised",
            bd=0,
            showhandle=True,
            handlesize=14,
            opaqueresize=True,
        )
        self.paned.pack(fill="both", expand=True)

        self.table_panel = tk.Frame(
            self.paned,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=10,
            pady=10,
        )

        self.inspector_outer = tk.Frame(
            self.paned,
            bg=BG,
            width=360,
        )
        self.inspector_outer.pack_propagate(False)

        self._build_table()
        self._build_scrollable_inspector()

        self.paned.add(self.table_panel, minsize=460)
        self.paned.add(self.inspector_outer, minsize=300)

    def _build_table(self) -> None:
        table_header = tk.Frame(self.table_panel, bg=CARD)
        table_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            table_header,
            text="EA Table",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(side="left")

        tk.Label(
            table_header,
            text="Click column headers to sort. EA number sorts numerically.",
            bg=CARD,
            fg=MUTED,
            font=FONT_XS,
        ).pack(side="left", padx=(14, 0))

        self.table_count_label = tk.Label(
            table_header,
            text="0 rows",
            bg=CARD,
            fg=MUTED,
            font=FONT_XS,
        )
        self.table_count_label.pack(side="right")

        table_container = tk.Frame(self.table_panel, bg=CARD_2)
        table_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(
            table_container,
            style="EA.Treeview",
            show="headings",
        )
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.y_scroll = ttk.Scrollbar(
            table_container,
            orient="vertical",
            command=self.tree.yview,
            style="Vertical.TScrollbar",
        )
        self.y_scroll.grid(row=0, column=1, sticky="ns")

        self.x_scroll = ttk.Scrollbar(
            table_container,
            orient="horizontal",
            command=self.tree.xview,
            style="Horizontal.TScrollbar",
        )
        self.x_scroll.grid(row=1, column=0, sticky="ew")

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        self.tree.configure(
            yscrollcommand=self.y_scroll.set,
            xscrollcommand=self.x_scroll.set,
        )

        self.columns_full = [
            "file_name",
            "folder_symbol",
            "filename_symbol",
            "ea_number",
            "strategy_id",
            "direction",
            "timeframe",
            "extension",
            "status",
        ]

        self.columns_desktop = [
            "file_name",
            "folder_symbol",
            "ea_number",
            "strategy_id",
            "direction",
            "timeframe",
            "status",
        ]

        self.columns_compact = [
            "file_name",
            "folder_symbol",
            "ea_number",
            "status",
        ]

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected_file())

    def _build_scrollable_inspector(self) -> None:
        self.inspector_canvas = tk.Canvas(
            self.inspector_outer,
            bg=BG,
            highlightthickness=0,
            bd=0,
        )
        self.inspector_scrollbar = ttk.Scrollbar(
            self.inspector_outer,
            orient="vertical",
            command=self.inspector_canvas.yview,
            style="Vertical.TScrollbar",
        )
        self.inspector_content = tk.Frame(self.inspector_canvas, bg=BG)

        self.inspector_window = self.inspector_canvas.create_window(
            (0, 0),
            window=self.inspector_content,
            anchor="nw",
        )

        self.inspector_canvas.configure(yscrollcommand=self.inspector_scrollbar.set)

        self.inspector_canvas.pack(side="left", fill="both", expand=True)
        self.inspector_scrollbar.pack(side="right", fill="y")

        self.inspector_content.bind("<Configure>", self._update_inspector_scroll_region)
        self.inspector_canvas.bind("<Configure>", self._update_inspector_canvas_width)

        self._build_filter_cards()

    def _update_inspector_scroll_region(self, _event=None) -> None:
        self.inspector_canvas.configure(scrollregion=self.inspector_canvas.bbox("all"))

    def _update_inspector_canvas_width(self, event=None) -> None:
        if event is None:
            return
        self.inspector_canvas.itemconfigure(self.inspector_window, width=event.width)

    def _build_filter_cards(self) -> None:
        self.symbol_card, self.symbol_tree = self._filter_card(
            parent=self.inspector_content,
            title="Symbol Filter",
            clear_command=self.clear_symbol_filter,
            columns=("symbol", "count"),
            height=9,
            on_select=self.on_symbol_select,
        )

        self.status_card, self.status_tree = self._filter_card(
            parent=self.inspector_content,
            title="Status Filter",
            clear_command=self.clear_status_filter,
            columns=("status", "count"),
            height=5,
            on_select=self.on_status_select,
        )

        self.direction_card, self.direction_tree = self._filter_card(
            parent=self.inspector_content,
            title="Direction Filter",
            clear_command=self.clear_direction_filter,
            columns=("direction", "count"),
            height=5,
            on_select=self.on_direction_select,
        )

        self.timeframe_card, self.timeframe_tree = self._filter_card(
            parent=self.inspector_content,
            title="Timeframe Filter",
            clear_command=self.clear_timeframe_filter,
            columns=("timeframe", "count"),
            height=5,
            on_select=self.on_timeframe_select,
        )

        self.details_card = tk.Frame(
            self.inspector_content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=12,
        )

        tk.Label(
            self.details_card,
            text="Selected EA",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(anchor="w")

        for key in [
            "file_name",
            "folder_symbol",
            "ea_number",
            "strategy_id",
            "direction",
            "timeframe",
            "status",
            "file_path",
        ]:
            row = tk.Frame(self.details_card, bg=CARD)
            row.pack(fill="x", pady=(6, 0))

            tk.Label(
                row,
                text=key,
                bg=CARD,
                fg=MUTED,
                font=FONT_XS,
                width=14,
                anchor="w",
            ).pack(side="left")

            label = tk.Label(
                row,
                text="-",
                bg=CARD,
                fg=TEXT,
                font=FONT_XS,
                anchor="w",
                justify="left",
            )
            label.pack(side="left", fill="x", expand=True)

            self.detail_labels[key] = label

    def _filter_card(
        self,
        parent: tk.Widget,
        title: str,
        clear_command: Callable[[], None],
        columns: Tuple[str, str],
        height: int,
        on_select: Callable[..., None],
    ) -> Tuple[tk.Frame, ttk.Treeview]:
        card = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=12,
            pady=12,
        )

        header = tk.Frame(card, bg=CARD)
        header.pack(fill="x", pady=(0, 8))

        tk.Label(
            header,
            text=title,
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(side="left")

        ActionButton(
            header,
            "Clear",
            clear_command,
            width=64,
            height=26,
        ).pack(side="right")

        tree = ttk.Treeview(
            card,
            style="EA.Treeview",
            show="headings",
            height=height,
        )
        tree.pack(fill="both", expand=True)

        tree["columns"] = list(columns)
        tree.heading(columns[0], text=columns[0])
        tree.heading(columns[1], text=columns[1])
        tree.column(columns[0], width=170, anchor="w", stretch=True)
        tree.column(columns[1], width=70, anchor="e", stretch=False)
        tree.bind("<<TreeviewSelect>>", on_select)

        return card, tree

    # -----------------------------
    # Responsive Layout
    # -----------------------------

    def _on_resize(self, _event=None) -> None:
        if self.resize_after_id is not None:
            self.after_cancel(self.resize_after_id)
        self.resize_after_id = self.after(120, self.apply_responsive_layout)

    def apply_responsive_layout(self) -> None:
        width = self.winfo_width()

        if width >= self.BREAK_FULL:
            layout = "full"
        elif width >= self.BREAK_DESKTOP:
            layout = "desktop"
        elif width >= self.BREAK_TABLET:
            layout = "tablet"
        else:
            layout = "compact"

        if layout != self.current_layout:
            self.current_layout = layout
            self.layout_var.set(f"Layout: {layout}")

            self._layout_metrics(layout)
            self._layout_toolbar(layout)
            self._layout_inspector(layout)
            self._configure_table_columns(layout)
            self._set_orientation(layout)

            self.lock_sash_after_layout = True

        if self.lock_sash_after_layout:
            self.after(80, self._set_sash_position)
            self.after(500, self._unlock_sash)

    def _unlock_sash(self) -> None:
        self.lock_sash_after_layout = False

    def _layout_metrics(self, layout: str) -> None:
        for card in self.metric_cards.values():
            card.pack_forget()

        if layout in ("full", "desktop", "tablet"):
            keys = ["total", "valid", "warning", "invalid"]
            for key in keys:
                self.metric_cards[key].pack(side="left", fill="x", expand=True, padx=(0, 10))
        else:
            for key in ["total", "valid"]:
                self.metric_cards[key].pack(fill="x", pady=(0, 8))

    def _layout_toolbar(self, layout: str) -> None:
        for widget in [
            self.search_box,
            self.btn_filter,
            self.btn_clear,
            self.btn_refresh,
            self.btn_open,
            self.btn_export,
        ]:
            widget.pack_forget()

        if layout in ("full", "desktop"):
            self.search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_filter.pack(side="left", padx=(0, 8))
            self.btn_clear.pack(side="left", padx=(0, 8))
            self.btn_refresh.pack(side="left", padx=(0, 8))
            self.btn_open.pack(side="left", padx=(0, 8))
            self.btn_export.pack(side="right")

        elif layout == "tablet":
            self.search_box.pack(fill="x", pady=(0, 8))
            self.btn_filter.pack(side="left", padx=(0, 8))
            self.btn_clear.pack(side="left", padx=(0, 8))
            self.btn_refresh.pack(side="left", padx=(0, 8))
            self.btn_open.pack(side="left", padx=(0, 8))
            self.btn_export.pack(side="left")

        else:
            self.search_box.pack(fill="x", pady=(0, 8))
            self.btn_filter.pack(side="left", padx=(0, 6))
            self.btn_clear.pack(side="left", padx=(0, 6))
            self.btn_refresh.pack(side="left", padx=(0, 6))

    def _layout_inspector(self, layout: str) -> None:
        for widget in [
            self.symbol_card,
            self.status_card,
            self.direction_card,
            self.timeframe_card,
            self.details_card,
        ]:
            widget.pack_forget()

        if layout in ("full", "desktop"):
            for widget in [
                self.symbol_card,
                self.status_card,
                self.direction_card,
                self.timeframe_card,
                self.details_card,
            ]:
                widget.pack(fill="x", pady=(0, 10))

        elif layout == "tablet":
            for widget in [
                self.symbol_card,
                self.status_card,
                self.direction_card,
                self.timeframe_card,
                self.details_card,
            ]:
                widget.pack(fill="x", pady=(0, 10))

        else:
            for widget in [
                self.symbol_card,
                self.status_card,
                self.direction_card,
                self.timeframe_card,
                self.details_card,
            ]:
                widget.pack(fill="x", pady=(0, 8))

    def _set_orientation(self, layout: str) -> None:
        desired = tk.HORIZONTAL if layout in ("full", "desktop") else tk.VERTICAL
        orient_name = "horizontal" if desired == tk.HORIZONTAL else "vertical"

        if self.current_orient == orient_name:
            return

        self.current_orient = orient_name
        self.paned.configure(orient=desired)

    def _set_sash_position(self) -> None:
        try:
            if self.current_layout in ("full", "desktop"):
                width = max(self.paned.winfo_width(), 1)
                self.paned.sash_place(0, int(width * 0.72), 0)
            else:
                height = max(self.paned.winfo_height(), 1)
                self.paned.sash_place(0, 0, int(height * 0.62))
        except Exception:
            pass

    def _configure_table_columns(self, layout: str) -> None:
        if layout == "full":
            columns = self.columns_full
            widths = {
                "file_name": 340,
                "folder_symbol": 110,
                "filename_symbol": 120,
                "ea_number": 90,
                "strategy_id": 120,
                "direction": 90,
                "timeframe": 90,
                "extension": 80,
                "status": 90,
            }

        elif layout in ("desktop", "tablet"):
            columns = self.columns_desktop
            widths = {
                "file_name": 330,
                "folder_symbol": 110,
                "ea_number": 90,
                "strategy_id": 120,
                "direction": 90,
                "timeframe": 90,
                "status": 90,
            }

        else:
            columns = self.columns_compact
            widths = {
                "file_name": 300,
                "folder_symbol": 110,
                "ea_number": 90,
                "status": 90,
            }

        self.tree["columns"] = columns

        for col in columns:
            heading = col
            if col == self.sort_column:
                heading = f"{col} {'↓' if self.sort_reverse else '↑'}"

            self.tree.heading(
                col,
                text=heading,
                command=lambda c=col: self.sort_by_column(c),
            )
            self.tree.column(col, width=widths[col], minwidth=70, anchor="w", stretch=True)

        self._reload_tree_from_cache()

    # -----------------------------
    # Data
    # -----------------------------

    def refresh(self) -> None:
        try:
            total = self.db.count()
            valid = self.db.count("parse_status = 'valid'")
            warning = self.db.count("parse_status = 'warning'")
            invalid = self.db.count("parse_status = 'invalid'")

            self.metric_cards["total"].set_value(total, "all files")
            self.metric_cards["valid"].set_value(valid, percent(valid, total))
            self.metric_cards["warning"].set_value(warning, percent(warning, total))
            self.metric_cards["invalid"].set_value(invalid, percent(invalid, total))

            self.rows_cache = self.db.fetch_records(
                search=self.search_var.get().strip(),
                symbol_filter=self.active_symbol_filter,
                status_filter=self.active_status_filter,
                direction_filter=self.active_direction_filter,
                timeframe_filter=self.active_timeframe_filter,
            )

            self._sort_cache()
            self._reload_tree_from_cache()
            self._reload_all_filter_trees()
            self._update_filter_label()

            self.status_var.set("Loaded")

        except Exception as exc:
            self.status_var.set("Error")
            messagebox.showerror("EA Inventory Error", str(exc))

    def _reload_tree_from_cache(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_to_record.clear()

        columns = list(self.tree["columns"])

        for record in self.rows_cache:
            values = [self._short(record.get(col), 140) for col in columns]
            item = self.tree.insert("", "end", values=tuple(values))
            self.item_to_record[item] = record

        self.table_count_label.configure(text=f"{len(self.rows_cache)} rows")

    def _reload_all_filter_trees(self) -> None:
        self._reload_filter_tree(
            self.symbol_tree,
            self.db.symbol_distribution(),
            self.active_symbol_filter,
        )
        self._reload_filter_tree(
            self.status_tree,
            self.db.status_distribution(),
            self.active_status_filter,
        )
        self._reload_filter_tree(
            self.direction_tree,
            self.db.direction_distribution(),
            self.active_direction_filter,
        )
        self._reload_filter_tree(
            self.timeframe_tree,
            self.db.timeframe_distribution(),
            self.active_timeframe_filter,
        )

    def _reload_filter_tree(
        self,
        tree: ttk.Treeview,
        data: List[Tuple[str, int]],
        active_value: str,
    ) -> None:
        for item in tree.get_children():
            tree.delete(item)

        for name, count in data:
            label = name
            if name == active_value:
                label = f"● {name}"
            tree.insert("", "end", values=(label, count))

    # -----------------------------
    # Sorting
    # -----------------------------

    def sort_by_column(self, column: str) -> None:
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False

        self._sort_cache()
        self._configure_table_columns(self.current_layout or "full")

    def _sort_cache(self) -> None:
        col = self.sort_column

        if col in self.NUMERIC_COLUMNS:
            self.rows_cache.sort(
                key=lambda row: safe_int(row.get(col)),
                reverse=self.sort_reverse,
            )
        else:
            self.rows_cache.sort(
                key=lambda row: str(row.get(col) or "").lower(),
                reverse=self.sort_reverse,
            )

    # -----------------------------
    # Filters
    # -----------------------------

    def on_symbol_select(self, _event=None) -> None:
        value = self._selected_filter_value(self.symbol_tree)
        if value:
            self.apply_symbol_filter(value)

    def on_status_select(self, _event=None) -> None:
        value = self._selected_filter_value(self.status_tree)
        if value:
            self.apply_status_filter(value)

    def on_direction_select(self, _event=None) -> None:
        value = self._selected_filter_value(self.direction_tree)
        if value:
            self.apply_direction_filter(value)

    def on_timeframe_select(self, _event=None) -> None:
        value = self._selected_filter_value(self.timeframe_tree)
        if value:
            self.apply_timeframe_filter(value)

    def _selected_filter_value(self, tree: ttk.Treeview) -> str:
        item = tree.focus()
        if not item:
            return ""

        values = tree.item(item, "values")
        if not values:
            return ""

        return str(values[0]).replace("● ", "").strip()

    def apply_symbol_filter(self, symbol: str) -> None:
        self.active_symbol_filter = symbol
        self.refresh()

    def clear_symbol_filter(self) -> None:
        self.active_symbol_filter = ""
        self.refresh()

    def apply_status_filter(self, status: str) -> None:
        self.active_status_filter = status
        self.refresh()

    def clear_status_filter(self) -> None:
        self.active_status_filter = ""
        self.refresh()

    def apply_direction_filter(self, direction: str) -> None:
        self.active_direction_filter = direction
        self.refresh()

    def clear_direction_filter(self) -> None:
        self.active_direction_filter = ""
        self.refresh()

    def apply_timeframe_filter(self, timeframe: str) -> None:
        self.active_timeframe_filter = timeframe
        self.refresh()

    def clear_timeframe_filter(self) -> None:
        self.active_timeframe_filter = ""
        self.refresh()

    def clear_all_filters(self) -> None:
        self.active_symbol_filter = ""
        self.active_status_filter = ""
        self.active_direction_filter = ""
        self.active_timeframe_filter = ""
        self.search_var.set("")
        self.refresh()

    def _update_filter_label(self) -> None:
        parts = [
            self.active_symbol_filter or "All symbols",
            self.active_status_filter or "All status",
            self.active_direction_filter or "All directions",
            self.active_timeframe_filter or "All timeframes",
        ]
        self.filter_var.set("Filters: " + " / ".join(parts))

    # -----------------------------
    # Selection + Actions
    # -----------------------------

    def on_select(self, _event=None) -> None:
        item = self.tree.focus()
        record = self.item_to_record.get(item)

        if not record:
            self.selected_file_path = None
            return

        file_path = record.get("file_path")
        self.selected_file_path = Path(str(file_path)) if file_path else None

        for key, label in self.detail_labels.items():
            label.configure(text=self._short(record.get(key), 38))

    def open_selected_file(self) -> None:
        if self.selected_file_path is None:
            messagebox.showwarning("No file selected", "Select an EA row first.")
            return

        open_path(self.selected_file_path)

    def export_csv(self) -> None:
        if not self.rows_cache:
            messagebox.showwarning("No data", "No EA inventory rows loaded.")
            return

        path = filedialog.asksaveasfilename(
            title="Export EA Inventory",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
        )

        if not path:
            return

        columns = list(self.rows_cache[0].keys())

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.rows_cache)

        messagebox.showinfo("Export Complete", f"Exported:\n{path}")

    def _short(self, value: Any, max_len: int = 120) -> str:
        if value is None:
            return ""

        text = str(value).replace("\n", " ").replace("\r", " ").strip()

        if len(text) <= max_len:
            return text

        return text[: max_len - 3] + "..."


def main() -> None:
    root = tk.Tk()
    root.title("QUANT OS - EA Inventory")
    root.geometry("1450x850")
    root.minsize(760, 620)
    root.configure(bg=BG)

    widget = EAInventoryWidget(root)
    widget.pack(fill="both", expand=True, padx=18, pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
