# ============================================================
# CODE_REGISTRY
# script_id: code_registry_widget
# script_name: code_registry_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Widget
# purpose: Responsive Code Registry Dashboard for QUANT_SYSTEM.db
# inputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry
# outputs: Tkinter widget panel
# upstream_data: code_registry
# downstream_data: main.py
# dependencies: tkinter, ttk, sqlite3, pathlib, os, subprocess, sys, csv
# schedule: manual
# version: v3.3.0
# last_reviewed: 2026-06-18
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, widget, code-registry, management-workspace, responsive-dashboard
# notes: Stable responsive version. Clickable layer chart filters the registry table. Always named code_registry_widget.py. Mac/Windows safe. No native tk.Button.
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


# ============================================================
# DESIGN TOKENS
# ============================================================

# Bloomberg / Terminal Style Tokens
BG = "#020403"
PANEL = "#050505"
CARD = "#0A0A0A"
CARD_2 = "#101010"
CARD_3 = "#151515"
BORDER = "#333333"
BORDER_SOFT = "#1A1A1A"

TEXT = "#F2F2F2"
MUTED = "#9B9B9B"
DIM = "#6F6F6F"

ORANGE = "#F5A623"
BLUE = "#2D7DFF"
BLUE_DARK = "#111111"
GREEN = "#00C853"
YELLOW = "#FFD600"
RED = "#FF1744"
PURPLE = "#8B5CF6"
CYAN = "#00E5FF"
GRAY = "#6F6F6F"

FONT_TITLE = ("Helvetica", 20, "bold")
FONT_H1 = ("Helvetica", 14, "bold")
FONT_H2 = ("Helvetica", 10, "bold")
FONT_MAIN = ("Helvetica", 9)
FONT_SMALL = ("Helvetica", 8)
FONT_XS = ("Helvetica", 8)


CODE_REGISTRY = {
    "script_id": "code_registry_widget",
    "script_name": "code_registry_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Widget",
    "purpose": "Responsive Code Registry Dashboard for QUANT_SYSTEM.db",
    "inputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry",
    "outputs": "Tkinter widget panel",
    "upstream_data": "code_registry",
    "downstream_data": "main.py",
    "dependencies": "tkinter, ttk, sqlite3, pathlib, os, subprocess, sys, csv",
    "schedule": "manual",
    "version": "v3.3.0",
    "last_reviewed": "2026-06-18",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,widget,code-registry,management-workspace,responsive-dashboard",
    "notes": "Stable responsive version. Clickable layer chart filters the registry table. Always named code_registry_widget.py. Mac/Windows safe. No native tk.Button.",
}


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


def percent(part: int, total: int) -> str:
    if total <= 0:
        return "0.0%"
    return f"{part / total * 100:.1f}%"


# ============================================================
# CUSTOM MAC/WINDOWS SAFE BUTTON
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
        active_bg: str = "#1A1A1A",
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


# ============================================================
# DATABASE SERVICE
# ============================================================

class CodeRegistryDBService:
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
                WHERE type='table' AND name='code_registry'
                LIMIT 1;
                """
            ).fetchone()

        return row is not None

    def count(self, where: Optional[str] = None) -> int:
        if not self.table_exists():
            return 0

        sql = "SELECT COUNT(*) AS n FROM code_registry"
        if where:
            sql += " WHERE " + where

        with self.connect() as conn:
            row = conn.execute(sql).fetchone()

        return int(row["n"]) if row else 0

    def get_rows(self, search: str = "", layer_filter: str = "", limit: int = 5000) -> List[sqlite3.Row]:
        if not self.table_exists():
            return []

        cols = [
            "script_id",
            "script_name",
            "layer",
            "domain",
            "status",
            "version",
            "last_reviewed",
            "scan_status",
            "registry_source",
            "owner",
            "purpose",
            "relative_path",
            "file_path",
            "business_criticality",
            "environment",
            "registry_group",
            "notes",
        ]

        sql = f"""
            SELECT {", ".join(cols)}
            FROM code_registry
            WHERE 1=1
        """

        params: List[Any] = []

        if search.strip():
            s = f"%{search.strip()}%"
            sql += """
                AND (
                    script_id LIKE ?
                    OR script_name LIKE ?
                    OR layer LIKE ?
                    OR domain LIKE ?
                    OR status LIKE ?
                    OR version LIKE ?
                    OR scan_status LIKE ?
                    OR registry_source LIKE ?
                    OR owner LIKE ?
                    OR purpose LIKE ?
                    OR relative_path LIKE ?
                    OR file_path LIKE ?
                    OR business_criticality LIKE ?
                    OR environment LIKE ?
                    OR registry_group LIKE ?
                    OR notes LIKE ?
                )
            """
            params.extend([s] * 16)

        if layer_filter.strip():
            sql += " AND COALESCE(NULLIF(layer, ''), 'Unknown') = ?"
            params.append(layer_filter.strip())

        sql += " ORDER BY layer, domain, script_name LIMIT ?"
        params.append(limit)

        with self.connect() as conn:
            return conn.execute(sql, params).fetchall()

    def layer_distribution(self) -> List[Tuple[str, int]]:
        if not self.table_exists():
            return []

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(layer, ''), 'Unknown') AS layer, COUNT(*) AS n
                FROM code_registry
                GROUP BY COALESCE(NULLIF(layer, ''), 'Unknown')
                ORDER BY n DESC, layer;
                """
            ).fetchall()

        return [(str(row["layer"]), int(row["n"])) for row in rows]


# ============================================================
# MAIN WIDGET
# ============================================================

class CodeRegistryWidget(tk.Frame):
    """
    Stable responsive dashboard.

    Important:
    - PanedWindow is created once and never destroyed.
    - The user can resize table and inspector by dragging the sash.
    - Full/Desktop: table left, inspector right.
    - Tablet/Compact: table top, inspector bottom.
    """

    BREAK_FULL = 1380
    BREAK_DESKTOP = 1100
    BREAK_TABLET = 850

    def __init__(self, parent: tk.Widget, db_path: Optional[Path] = None):
        super().__init__(parent, bg=BG)

        if db_path is None:
            root = find_quant_root(Path(__file__))
            db_path = root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db"

        self.db_path = db_path
        self.db = CodeRegistryDBService(self.db_path)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Not Loaded")
        self.layout_var = tk.StringVar(value="Layout: initializing")
        self.layer_filter_var = tk.StringVar(value="Layer filter: All")
        self.active_layer_filter = ""

        self.selected_file_path: Optional[Path] = None
        self.rows_cache: List[Dict[str, Any]] = []
        self.item_to_record: Dict[str, Dict[str, Any]] = {}

        self.current_layout = ""
        self.current_orient = ""
        self.resize_after_id: Optional[str] = None

        self.metric_cards: Dict[str, Dict[str, tk.Label]] = {}
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
            "Code.Treeview",
            background=CARD_2,
            foreground=TEXT,
            fieldbackground=CARD_2,
            rowheight=31,
            font=FONT_SMALL,
            borderwidth=0,
            relief="flat",
        )

        style.configure(
            "Code.Treeview.Heading",
            background=CARD,
            foreground=MUTED,
            font=FONT_SMALL,
            borderwidth=0,
            relief="flat",
        )

        style.map(
            "Code.Treeview",
            background=[("selected", "#2A2A2A")],
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
            text="CODE REGISTRY",
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE,
        ).pack(side="left")

        tk.Label(
            title_row,
            text="/ MANAGEMENT WORKSPACE",
            bg=BG,
            fg=ORANGE,
            font=FONT_XS,
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        tk.Label(
            left,
            text="Read-only registry of Python scripts and code objects from QUANT_SYSTEM.db",
            bg=BG,
            fg=MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(6, 0))

        right = tk.Frame(self.header, bg=BG)
        right.pack(side="right", anchor="ne")

        tk.Label(
            right,
            textvariable=self.layer_filter_var,
            bg=BG,
            fg=ORANGE,
            font=FONT_XS,
        ).pack(side="left", padx=(0, 14))

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

        specs = [
            ("total", "TOTAL SCRIPTS", BLUE, "100% of registry"),
            ("valid", "VALID SCRIPTS", GREEN, "valid scan status"),
            ("warning", "WARNINGS", YELLOW, "warning scan status"),
            ("missing", "MISSING REGISTRY", RED, "missing registry data"),
            ("runtime", "RUNTIME DICTS", PURPLE, "runtime_dict source"),
        ]

        for key, title, color, subtitle in specs:
            card = tk.Frame(
                self.metrics_host,
                bg=CARD,
                highlightbackground=BORDER,
                highlightthickness=1,
                padx=16,
                pady=13,
                height=88,
            )
            card.pack_propagate(False)

            tk.Label(card, text=title, bg=CARD, fg=MUTED, font=FONT_XS).pack(anchor="w")

            value_label = tk.Label(
                card,
                text="0",
                bg=CARD,
                fg=TEXT,
                font=("Helvetica", 21, "bold"),
            )
            value_label.pack(anchor="w", pady=(6, 0))

            sub_label = tk.Label(
                card,
                text=subtitle,
                bg=CARD,
                fg=MUTED,
                font=FONT_XS,
            )
            sub_label.pack(anchor="w", pady=(3, 0))

            tk.Label(card, text="●", bg=CARD, fg=color, font=FONT_XS).place(relx=0.95, rely=0.47)

            self.metric_cards[key] = {
                "frame": card,
                "value": value_label,
                "sub": sub_label,
            }

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
            highlightbackground=ORANGE,
            highlightthickness=1,
        )

        tk.Label(
            self.search_box,
            text="Search",
            bg=ORANGE,
            fg="#000000",
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
            bg=ORANGE,
            fg="#000000",
            border=ORANGE,
        )
        self.btn_clear_layer = ActionButton(self.toolbar, "Clear Layer", self.clear_layer_filter, width=100)
        self.btn_refresh = ActionButton(self.toolbar, "Refresh", self.refresh, width=90)
        self.btn_open = ActionButton(self.toolbar, "Open Selected", self.open_selected_file, width=120)
        self.btn_export = ActionButton(self.toolbar, "Export CSV", self.export_csv, width=100)

    def _build_paned_area(self) -> None:
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)

        self.paned = tk.PanedWindow(
            self.body,
            orient=tk.HORIZONTAL,
            bg=BG,
            sashwidth=7,
            sashrelief="raised",
            bd=0,
            showhandle=True,
            handlesize=12,
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

        self.inspector_panel = tk.Frame(
            self.paned,
            bg=BG,
        )

        self._build_table()
        self._build_inspector()

        self.paned.add(self.table_panel, minsize=360)
        self.paned.add(self.inspector_panel, minsize=280)

    def _build_table(self) -> None:
        table_header = tk.Frame(self.table_panel, bg=CARD)
        table_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            table_header,
            text="REGISTRY TABLE",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(side="left")

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
            style="Code.Treeview",
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
            "script_name",
            "layer",
            "domain",
            "status",
            "version",
            "scan_status",
            "relative_path",
        ]

        self.columns_desktop = [
            "script_name",
            "layer",
            "status",
            "scan_status",
            "relative_path",
        ]

        self.columns_compact = [
            "script_name",
            "status",
            "scan_status",
        ]

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected_file())

    def _build_inspector(self) -> None:
        self.overview_card = tk.Frame(
            self.inspector_panel,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )

        tk.Label(
            self.overview_card,
            text="REGISTRY OVERVIEW",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(anchor="w")

        self.chart = tk.Canvas(
            self.overview_card,
            width=320,
            height=180,
            bg=CARD,
            highlightthickness=0,
        )
        self.chart.pack(fill="x", pady=(8, 0))

        self.details_card = tk.Frame(
            self.inspector_panel,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )

        tk.Label(
            self.details_card,
            text="DETAILS",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(anchor="w")

        for key in [
            "script_name",
            "layer",
            "domain",
            "status",
            "version",
            "scan_status",
            "owner",
            "last_reviewed",
            "relative_path",
        ]:
            row = tk.Frame(self.details_card, bg=CARD)
            row.pack(fill="x", pady=(6, 0))

            tk.Label(
                row,
                text=key,
                bg=CARD,
                fg=MUTED,
                font=FONT_XS,
                width=15,
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

        self.description_card = tk.Frame(
            self.inspector_panel,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14,
            pady=12,
        )

        tk.Label(
            self.description_card,
            text="DESCRIPTION",
            bg=CARD,
            fg=TEXT,
            font=FONT_H2,
        ).pack(anchor="w")

        self.description_label = tk.Label(
            self.description_card,
            text="Select a script to inspect purpose and file location.",
            bg=CARD,
            fg=MUTED,
            font=FONT_XS,
            wraplength=320,
            justify="left",
        )
        self.description_label.pack(anchor="w", pady=(10, 0))

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

        self.after(80, self._set_sash_position)
        self.after(120, self.draw_layer_chart)

    def _layout_metrics(self, layout: str) -> None:
        for data in self.metric_cards.values():
            data["frame"].pack_forget()

        if layout == "full":
            keys = ["total", "valid", "warning", "missing", "runtime"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 10))

        elif layout == "desktop":
            keys = ["valid", "warning", "missing", "runtime"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 10))

        elif layout == "tablet":
            keys = ["valid", "warning", "missing"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 8))

        else:
            keys = ["valid", "warning"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(fill="x", pady=(0, 8))

    def _layout_toolbar(self, layout: str) -> None:
        for widget in [
            self.search_box,
            self.btn_filter,
            self.btn_clear_layer,
            self.btn_refresh,
            self.btn_open,
            self.btn_export,
        ]:
            widget.pack_forget()

        if layout in ("full", "desktop"):
            self.search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_filter.pack(side="left", padx=(0, 8))
            self.btn_clear_layer.pack(side="left", padx=(0, 8))
            self.btn_refresh.pack(side="left", padx=(0, 8))
            self.btn_open.pack(side="left", padx=(0, 8))
            self.btn_export.pack(side="right")

        elif layout == "tablet":
            self.search_box.pack(fill="x", pady=(0, 8))
            self.btn_filter.pack(side="left", padx=(0, 8))
            self.btn_clear_layer.pack(side="left", padx=(0, 8))
            self.btn_refresh.pack(side="left", padx=(0, 8))
            self.btn_open.pack(side="left", padx=(0, 8))
            self.btn_export.pack(side="left")

        else:
            self.search_box.pack(fill="x", pady=(0, 8))
            self.btn_filter.pack(side="left", padx=(0, 6))
            self.btn_clear_layer.pack(side="left", padx=(0, 6))
            self.btn_refresh.pack(side="left", padx=(0, 6))

    def _layout_inspector(self, layout: str) -> None:
        for widget in [
            self.overview_card,
            self.details_card,
            self.description_card,
        ]:
            widget.pack_forget()

        if layout in ("full", "desktop"):
            self.overview_card.pack(fill="x", pady=(0, 10))
            self.details_card.pack(fill="x", pady=(0, 10))
            self.description_card.pack(fill="both", expand=True)

            self.chart.configure(width=320, height=180)
            self.description_label.configure(wraplength=320)

        elif layout == "tablet":
            self.overview_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.details_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.description_card.pack(side="left", fill="both", expand=True)

            self.chart.configure(width=260, height=150)
            self.description_label.configure(wraplength=250)

        else:
            self.overview_card.pack(fill="x", pady=(0, 8))
            self.details_card.pack(fill="x", pady=(0, 8))
            self.description_card.pack(fill="x")

            self.chart.configure(width=260, height=145)
            self.description_label.configure(wraplength=250)

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
                self.paned.sash_place(0, int(width * 0.68), 0)
            else:
                height = max(self.paned.winfo_height(), 1)
                self.paned.sash_place(0, 0, int(height * 0.58))
        except Exception:
            pass

    def _configure_table_columns(self, layout: str) -> None:
        if layout == "full":
            columns = self.columns_full
            widths = {
                "script_name": 220,
                "layer": 130,
                "domain": 170,
                "status": 90,
                "version": 80,
                "scan_status": 120,
                "relative_path": 360,
            }

        elif layout in ("desktop", "tablet"):
            columns = self.columns_desktop
            widths = {
                "script_name": 230,
                "layer": 130,
                "status": 90,
                "scan_status": 120,
                "relative_path": 320,
            }

        else:
            columns = self.columns_compact
            widths = {
                "script_name": 230,
                "status": 90,
                "scan_status": 120,
            }

        self.tree["columns"] = columns

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=widths[col], minwidth=70, anchor="w", stretch=True)

        self._reload_tree_from_cache()

    # -----------------------------
    # Data
    # -----------------------------

    def refresh(self) -> None:
        try:
            total = self.db.count()
            valid = self.db.count("scan_status = 'valid'")
            warning = self.db.count("scan_status = 'warning'")
            missing = self.db.count("scan_status = 'missing_registry'")
            runtime = self.db.count("registry_source = 'runtime_dict'")

            self.metric_cards["total"]["value"].configure(text=str(total))
            self.metric_cards["total"]["sub"].configure(text="100% of registry")

            self.metric_cards["valid"]["value"].configure(text=str(valid))
            self.metric_cards["valid"]["sub"].configure(text=percent(valid, total))

            self.metric_cards["warning"]["value"].configure(text=str(warning))
            self.metric_cards["warning"]["sub"].configure(text=percent(warning, total))

            self.metric_cards["missing"]["value"].configure(text=str(missing))
            self.metric_cards["missing"]["sub"].configure(text=percent(missing, total))

            self.metric_cards["runtime"]["value"].configure(text=str(runtime))
            self.metric_cards["runtime"]["sub"].configure(text="runtime_dict source")

            self.rows_cache = [dict(row) for row in self.db.get_rows(self.search_var.get().strip(), self.active_layer_filter)]

            self._reload_tree_from_cache()
            self.draw_layer_chart()
            self.status_var.set("Loaded")

        except Exception as exc:
            self.status_var.set("Error")
            messagebox.showerror("Code Registry Error", str(exc))

    def _reload_tree_from_cache(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.item_to_record.clear()

        columns = list(self.tree["columns"])

        for record in self.rows_cache:
            values = [self._short(record.get(col), 100) for col in columns]
            item = self.tree.insert("", "end", values=tuple(values))
            self.item_to_record[item] = record

        self.table_count_label.configure(text=f"{len(self.rows_cache)} rows")

    # -----------------------------
    # Chart + Selection
    # -----------------------------

    def draw_layer_chart(self) -> None:
        self.chart.delete("all")

        distribution = self.db.layer_distribution()
        total = sum(count for _, count in distribution)

        cw = max(int(self.chart.winfo_width()), 260)
        ch = max(int(self.chart.winfo_height()), 140)

        if total <= 0:
            self.chart.create_text(cw // 2, ch // 2, text="No data", fill=MUTED, font=FONT_MAIN)
            return

        colors = [BLUE, GREEN, YELLOW, PURPLE, CYAN, GRAY, RED]

        donut_size = min(112, ch - 34, max(85, cw // 2 - 24))
        x0 = 16
        y0 = max(18, (ch - donut_size) // 2)
        x1 = x0 + donut_size
        y1 = y0 + donut_size

        start = 90

        for index, (layer, count) in enumerate(distribution):
            extent = 360 * count / total
            color = colors[index % len(colors)]
            tag = self._layer_tag(layer)

            arc = self.chart.create_arc(
                x0,
                y0,
                x1,
                y1,
                start=start,
                extent=extent,
                fill=color,
                outline=CARD,
                tags=(tag, "layer_filter_item"),
            )
            self.chart.tag_bind(tag, "<Button-1>", lambda _event, selected_layer=layer: self.apply_layer_filter(selected_layer))
            self.chart.tag_bind(tag, "<Enter>", lambda _event: self.chart.configure(cursor="hand2"))
            self.chart.tag_bind(tag, "<Leave>", lambda _event: self.chart.configure(cursor=""))

            start += extent

        inner_pad = int(donut_size * 0.28)

        self.chart.create_oval(
            x0 + inner_pad,
            y0 + inner_pad,
            x1 - inner_pad,
            y1 - inner_pad,
            fill=CARD,
            outline=CARD,
        )

        center_text = self.active_layer_filter if self.active_layer_filter else str(total)
        center_sub = "Filtered" if self.active_layer_filter else "Scripts"

        self.chart.create_text(
            (x0 + x1) // 2,
            (y0 + y1) // 2 - 8,
            text=self._short(center_text, 10),
            fill=TEXT,
            font=("Helvetica", 14, "bold"),
        )

        self.chart.create_text(
            (x0 + x1) // 2,
            (y0 + y1) // 2 + 12,
            text=center_sub,
            fill=MUTED,
            font=FONT_XS,
        )

        legend_x = x1 + 24
        y = y0 + 2

        for index, (layer, count) in enumerate(distribution[:6]):
            color = colors[index % len(colors)]
            pct_text = count / total * 100
            tag = self._layer_tag(layer)

            is_active = layer == self.active_layer_filter
            text_color = TEXT if not self.active_layer_filter or is_active else DIM
            row_bg = "#1A1A1A" if is_active else CARD

            # clickable legend row background
            row = self.chart.create_rectangle(
                legend_x - 5,
                y,
                cw - 4,
                y + 20,
                fill=row_bg,
                outline=row_bg,
                tags=(tag, "layer_filter_item"),
            )

            self.chart.create_oval(
                legend_x,
                y + 5,
                legend_x + 9,
                y + 14,
                fill=color,
                outline=color,
                tags=(tag, "layer_filter_item"),
            )

            self.chart.create_text(
                legend_x + 18,
                y + 10,
                text=self._short(layer, 18),
                fill=text_color,
                anchor="w",
                font=FONT_XS,
                tags=(tag, "layer_filter_item"),
            )

            self.chart.create_text(
                cw - 8,
                y + 10,
                text=f"{count} ({pct_text:.1f}%)",
                fill=MUTED if not is_active else ORANGE,
                anchor="e",
                font=FONT_XS,
                tags=(tag, "layer_filter_item"),
            )

            self.chart.tag_bind(tag, "<Button-1>", lambda _event, selected_layer=layer: self.apply_layer_filter(selected_layer))
            self.chart.tag_bind(tag, "<Enter>", lambda _event: self.chart.configure(cursor="hand2"))
            self.chart.tag_bind(tag, "<Leave>", lambda _event: self.chart.configure(cursor=""))

            y += 21

        if self.active_layer_filter:
            clear_tag = "clear_layer_filter"
            self.chart.create_text(
                x0 + donut_size // 2,
                y1 + 18,
                text="Clear filter",
                fill=ORANGE,
                font=FONT_XS,
                tags=(clear_tag,),
            )
            self.chart.tag_bind(clear_tag, "<Button-1>", lambda _event: self.clear_layer_filter())
            self.chart.tag_bind(clear_tag, "<Enter>", lambda _event: self.chart.configure(cursor="hand2"))
            self.chart.tag_bind(clear_tag, "<Leave>", lambda _event: self.chart.configure(cursor=""))

    def _layer_tag(self, layer: str) -> str:
        safe = "".join(ch if ch.isalnum() else "_" for ch in str(layer))
        return f"layer_filter_{safe}"

    def apply_layer_filter(self, layer: str) -> None:
        self.active_layer_filter = str(layer)
        self.layer_filter_var.set(f"Layer filter: {self.active_layer_filter}")
        self.refresh()

    def clear_layer_filter(self) -> None:
        self.active_layer_filter = ""
        self.layer_filter_var.set("Layer filter: All")
        self.refresh()

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

        purpose = self._short(record.get("purpose"), 240)
        path = self._short(record.get("file_path"), 240)
        notes = self._short(record.get("notes"), 180)

        desc = f"{purpose}\n\nPath:\n{path}"

        if notes:
            desc += f"\n\nNotes:\n{notes}"

        self.description_label.configure(text=desc)

    # -----------------------------
    # Actions
    # -----------------------------

    def open_selected_file(self) -> None:
        if self.selected_file_path is None:
            messagebox.showwarning("No file selected", "Select a registry row first.")
            return

        open_path(self.selected_file_path)

    def export_csv(self) -> None:
        if not self.rows_cache:
            messagebox.showwarning("No data", "No registry rows loaded.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Code Registry",
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
    root.title("QUANT OS - Code Registry")
    root.geometry("1450x850")
    root.minsize(760, 620)
    root.configure(bg=BG)

    widget = CodeRegistryWidget(root)
    widget.pack(fill="both", expand=True, padx=18, pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
