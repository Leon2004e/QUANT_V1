"""
# ============================================================
# CODE_REGISTRY
# ============================================================
# script_id: quant_system_db_dashboard
# script_name: QUANT_SYSTEM DB Dashboard
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management_Workspace
# asset_type: Dashboard
# purpose: Displays all QUANT_SYSTEM.db tables including code_registry, strategies, portfolios, accounts, deployments, events and audit logs
# inputs:
#   - CONTROL_PLANE/Database/QUANT_SYSTEM.db
# outputs:
#   - Dashboard UI
# upstream_data:
#   - QUANT_SYSTEM.db
# downstream_data:
#   - Management Workspace
#   - Code Registry Overview
#   - Control Plane Overview
# dependencies:
#   - tkinter
#   - pathlib
#   - sqlite3
#   - datetime
#   - subprocess
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-15
# business_criticality: high
# environment: desktop
# registry_group: frontend_dashboard
# author: Leon Everts
# reviewer: ChatGPT
# created_date: 2026-06-15
# tags:
#   - frontend
#   - dashboard
#   - quant-system-db
#   - code-registry
# notes:
#   - Read-only dashboard for QUANT_SYSTEM.db.
#   - Shows complete database structure and all tables.
#   - Includes code_registry view if table exists.
#   - Does not write to the database.
# ============================================================
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional, Tuple


CODE_REGISTRY: Dict[str, Any] = {
    "script_id": "quant_system_db_dashboard",
    "script_name": "QUANT_SYSTEM DB Dashboard",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management_Workspace",
    "asset_type": "Dashboard",
    "purpose": "Displays all QUANT_SYSTEM.db tables including code_registry, strategies, portfolios, accounts, deployments, events and audit logs",
    "inputs": ["CONTROL_PLANE/Database/QUANT_SYSTEM.db"],
    "outputs": ["Dashboard UI"],
    "upstream_data": ["QUANT_SYSTEM.db"],
    "downstream_data": ["Management Workspace", "Code Registry Overview", "Control Plane Overview"],
    "dependencies": ["tkinter", "pathlib", "sqlite3", "datetime", "subprocess"],
    "schedule": "manual",
    "version": "v1.0.0",
    "last_reviewed": "2026-06-15",
    "business_criticality": "high",
    "environment": "desktop",
    "registry_group": "frontend_dashboard",
    "author": "Leon Everts",
    "reviewer": "ChatGPT",
    "created_date": "2026-06-15",
    "tags": ["frontend", "dashboard", "quant-system-db", "code-registry"],
    "notes": [
        "Read-only dashboard for QUANT_SYSTEM.db.",
        "Shows complete database structure and all tables.",
        "Includes code_registry view if table exists.",
        "Does not write to the database.",
    ],
}


APP_TITLE = "QUANT SYSTEM DB DASHBOARD"
APP_SUBTITLE = "Control Plane · QUANT_SYSTEM.db · Read-Only Viewer"


COLOR_BG = "#F4F6F8"
COLOR_PANEL = "#FFFFFF"
COLOR_HEADER = "#111827"
COLOR_TEXT = "#111827"
COLOR_MUTED = "#6B7280"
COLOR_BORDER = "#D1D5DB"
COLOR_ACCENT = "#2563EB"
COLOR_OK = "#059669"
COLOR_WARN = "#D97706"
COLOR_ERROR = "#DC2626"
COLOR_TABLE_HEADER = "#E5E7EB"


def log_info(message: str) -> None:
    print(f"[INFO] {message}")


def log_ok(message: str) -> None:
    print(f"[OK] {message}")


def log_warn(message: str) -> None:
    print(f"[WARN] {message}")


def log_error(message: str) -> None:
    print(f"[ERROR] {message}")


def find_quant_root(start: Path) -> Path:
    """
    Find QUANT OS root.

    Expected root contains:
    - CONTROL_PLANE/
    - MANAGEMENT_LAYER/ optional
    - FRONTEND_LAYER/ optional
    """
    current = start.resolve()

    for path in [current, *current.parents]:
        control_plane = path / "CONTROL_PLANE"
        if control_plane.exists() and control_plane.is_dir():
            return path

    raise FileNotFoundError(
        "QUANT OS root not found. Expected folder: CONTROL_PLANE/"
    )


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
        "QUANT_SYSTEM.db not found. Expected CONTROL_PLANE/Database/QUANT_SYSTEM.db"
    )


def quote_identifier(identifier: str) -> str:
    safe = identifier.replace('"', '""')
    return f'"{safe}"'


def read_only_connection(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


class QuantSystemDBDashboard(ttk.Frame):
    def __init__(self, parent: tk.Widget, repository: Any = None, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)

        self.repository = repository
        self.quant_root: Optional[Path] = None
        self.db_path: Optional[Path] = None

        self.tables: List[str] = []
        self.table_counts: Dict[str, int] = {}
        self.current_table: Optional[str] = None
        self.current_columns: List[str] = []
        self.current_rows: List[Dict[str, Any]] = []
        self.filtered_rows: List[Dict[str, Any]] = []

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.table_filter_var = tk.StringVar(value="All Tables")

        self.kpi_vars: Dict[str, tk.StringVar] = {
            "tables": tk.StringVar(value="0"),
            "rows": tk.StringVar(value="0"),
            "db_size": tk.StringVar(value="0 MB"),
            "scripts": tk.StringVar(value="0"),
            "events": tk.StringVar(value="0"),
            "modified": tk.StringVar(value="-"),
        }

        self._setup_style()
        self._build_layout()
        self.refresh_data()

    def _setup_style(self) -> None:
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Root.TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL, relief="flat")
        style.configure("Header.TFrame", background=COLOR_HEADER)
        style.configure(
            "Header.TLabel",
            background=COLOR_HEADER,
            foreground="white",
            font=("Arial", 18, "bold"),
        )
        style.configure(
            "SubHeader.TLabel",
            background=COLOR_HEADER,
            foreground="#D1D5DB",
            font=("Arial", 10),
        )
        style.configure(
            "Title.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_TEXT,
            font=("Arial", 12, "bold"),
        )
        style.configure(
            "Text.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_TEXT,
            font=("Arial", 10),
        )
        style.configure(
            "Muted.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_MUTED,
            font=("Arial", 9),
        )
        style.configure(
            "KPI.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_TEXT,
            font=("Arial", 18, "bold"),
        )
        style.configure(
            "KPIName.TLabel",
            background=COLOR_PANEL,
            foreground=COLOR_MUTED,
            font=("Arial", 9),
        )
        style.configure(
            "Accent.TButton",
            font=("Arial", 10, "bold"),
            padding=(12, 6),
        )
        style.configure(
            "Treeview",
            background="white",
            foreground=COLOR_TEXT,
            rowheight=26,
            fieldbackground="white",
            bordercolor=COLOR_BORDER,
            borderwidth=1,
            font=("Arial", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=COLOR_TABLE_HEADER,
            foreground=COLOR_TEXT,
            font=("Arial", 9, "bold"),
        )

    def _build_layout(self) -> None:
        self.configure(style="Root.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_kpis()
        self._build_main_area()
        self._build_footer()

    def _build_header(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(18, 14))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title = ttk.Label(header, text=APP_TITLE, style="Header.TLabel")
        title.grid(row=0, column=0, sticky="w")

        subtitle = ttk.Label(header, text=APP_SUBTITLE, style="SubHeader.TLabel")
        subtitle.grid(row=1, column=0, sticky="w", pady=(4, 0))

        button_frame = ttk.Frame(header, style="Header.TFrame")
        button_frame.grid(row=0, column=1, rowspan=2, sticky="e")

        refresh_btn = ttk.Button(
            button_frame,
            text="Refresh DB",
            command=self.refresh_data,
            style="Accent.TButton",
        )
        refresh_btn.grid(row=0, column=0, padx=(0, 8))

        scan_btn = ttk.Button(
            button_frame,
            text="Run Code Scanner",
            command=self.run_code_registry_scanner,
            style="Accent.TButton",
        )
        scan_btn.grid(row=0, column=1)

    def _build_kpis(self) -> None:
        wrapper = ttk.Frame(self, style="Root.TFrame", padding=(14, 12))
        wrapper.grid(row=1, column=0, sticky="ew")

        for i in range(6):
            wrapper.columnconfigure(i, weight=1)

        kpis = [
            ("Tables", "tables"),
            ("Total Rows", "rows"),
            ("DB Size", "db_size"),
            ("Registered Codes", "scripts"),
            ("System Events", "events"),
            ("Last Modified", "modified"),
        ]

        for idx, (label, key) in enumerate(kpis):
            card = ttk.Frame(wrapper, style="Panel.TFrame", padding=(14, 10))
            card.grid(row=0, column=idx, sticky="nsew", padx=5)
            card.columnconfigure(0, weight=1)

            ttk.Label(card, text=label, style="KPIName.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(card, textvariable=self.kpi_vars[key], style="KPI.TLabel").grid(
                row=1, column=0, sticky="w", pady=(5, 0)
            )

    def _build_main_area(self) -> None:
        container = ttk.Frame(self, style="Root.TFrame", padding=(14, 0, 14, 8))
        container.grid(row=2, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)

        self._build_search_bar(container)

        self.paned = ttk.PanedWindow(container, orient=tk.HORIZONTAL)
        self.paned.grid(row=1, column=0, sticky="nsew")

        self.nav_panel = ttk.Frame(self.paned, style="Panel.TFrame", padding=10)
        self.table_panel = ttk.Frame(self.paned, style="Panel.TFrame", padding=10)
        self.details_panel = ttk.Frame(self.paned, style="Panel.TFrame", padding=10)

        self.paned.add(self.nav_panel, weight=1)
        self.paned.add(self.table_panel, weight=4)
        self.paned.add(self.details_panel, weight=2)

        self._build_navigation()
        self._build_table()
        self._build_details()

    def _build_search_bar(self, parent: ttk.Frame) -> None:
        search = ttk.Frame(parent, style="Panel.TFrame", padding=(10, 8))
        search.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        search.columnconfigure(1, weight=1)

        ttk.Label(search, text="Search", style="Text.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )

        entry = ttk.Entry(search, textvariable=self.search_var)
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        entry.bind("<KeyRelease>", lambda event: self.apply_filter())

        clear_btn = ttk.Button(search, text="Clear", command=self.clear_search)
        clear_btn.grid(row=0, column=2, sticky="e")

    def _build_navigation(self) -> None:
        self.nav_panel.columnconfigure(0, weight=1)
        self.nav_panel.rowconfigure(1, weight=1)

        ttk.Label(self.nav_panel, text="Database Tables", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        nav_frame = ttk.Frame(self.nav_panel, style="Panel.TFrame")
        nav_frame.grid(row=1, column=0, sticky="nsew")
        nav_frame.columnconfigure(0, weight=1)
        nav_frame.rowconfigure(0, weight=1)

        self.nav_tree = ttk.Treeview(
            nav_frame,
            columns=("rows",),
            show="tree headings",
            selectmode="browse",
        )
        self.nav_tree.heading("#0", text="Table")
        self.nav_tree.heading("rows", text="Rows")
        self.nav_tree.column("#0", width=190, stretch=True)
        self.nav_tree.column("rows", width=70, stretch=False, anchor="e")

        nav_scroll_y = ttk.Scrollbar(
            nav_frame, orient="vertical", command=self.nav_tree.yview
        )
        self.nav_tree.configure(yscrollcommand=nav_scroll_y.set)

        self.nav_tree.grid(row=0, column=0, sticky="nsew")
        nav_scroll_y.grid(row=0, column=1, sticky="ns")

        self.nav_tree.bind("<<TreeviewSelect>>", self.on_table_select)

        ttk.Label(
            self.nav_panel,
            text="Select a table to inspect rows, schema and details.",
            style="Muted.TLabel",
            wraplength=260,
        ).grid(row=2, column=0, sticky="ew", pady=(8, 0))

    def _build_table(self) -> None:
        self.table_panel.columnconfigure(0, weight=1)
        self.table_panel.rowconfigure(2, weight=1)

        top = ttk.Frame(self.table_panel, style="Panel.TFrame")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        top.columnconfigure(0, weight=1)

        self.table_title_var = tk.StringVar(value="No table selected")
        ttk.Label(top, textvariable=self.table_title_var, style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )

        self.summary_var = tk.StringVar(value="0 rows")
        ttk.Label(top, textvariable=self.summary_var, style="Muted.TLabel").grid(
            row=1, column=0, sticky="w", pady=(2, 0)
        )

        self.table_frame = ttk.Frame(self.table_panel, style="Panel.TFrame")
        self.table_frame.grid(row=2, column=0, sticky="nsew")
        self.table_frame.columnconfigure(0, weight=1)
        self.table_frame.rowconfigure(0, weight=1)

        self.data_tree = ttk.Treeview(
            self.table_frame,
            show="headings",
            selectmode="browse",
        )

        y_scroll = ttk.Scrollbar(
            self.table_frame, orient="vertical", command=self.data_tree.yview
        )
        x_scroll = ttk.Scrollbar(
            self.table_frame, orient="horizontal", command=self.data_tree.xview
        )

        self.data_tree.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
        )

        self.data_tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.data_tree.bind("<<TreeviewSelect>>", self.on_row_select)

    def _build_details(self) -> None:
        self.details_panel.columnconfigure(0, weight=1)
        self.details_panel.rowconfigure(2, weight=1)

        ttk.Label(self.details_panel, text="Details", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8)
        )

        self.detail_title_var = tk.StringVar(value="No row selected")
        ttk.Label(
            self.details_panel,
            textvariable=self.detail_title_var,
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        detail_frame = ttk.Frame(self.details_panel, style="Panel.TFrame")
        detail_frame.grid(row=2, column=0, sticky="nsew")
        detail_frame.columnconfigure(0, weight=1)
        detail_frame.rowconfigure(0, weight=1)

        self.details_text = tk.Text(
            detail_frame,
            wrap="word",
            bg="white",
            fg=COLOR_TEXT,
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
        )

        detail_scroll = ttk.Scrollbar(
            detail_frame, orient="vertical", command=self.details_text.yview
        )
        self.details_text.configure(yscrollcommand=detail_scroll.set)

        self.details_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll.grid(row=0, column=1, sticky="ns")

        ttk.Label(
            self.details_panel,
            text="Visual Flow",
            style="Title.TLabel",
        ).grid(row=3, column=0, sticky="w", pady=(10, 4))

        self.flow_text = tk.Text(
            self.details_panel,
            height=8,
            wrap="word",
            bg="#F9FAFB",
            fg=COLOR_TEXT,
            relief="solid",
            borderwidth=1,
            font=("Arial", 9),
        )
        self.flow_text.grid(row=4, column=0, sticky="ew")
        self.flow_text.insert("1.0", "INPUTS\n↓\nSCRIPT / TABLE\n↓\nOUTPUTS")
        self.flow_text.configure(state="disabled")

    def _build_footer(self) -> None:
        footer = ttk.Frame(self, style="Root.TFrame", padding=(14, 4, 14, 8))
        footer.grid(row=3, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        status = ttk.Label(
            footer,
            textvariable=self.status_var,
            foreground=COLOR_MUTED,
            background=COLOR_BG,
            font=("Arial", 9),
        )
        status.grid(row=0, column=0, sticky="w")

    def refresh_data(self) -> None:
        try:
            self.quant_root = find_quant_root(Path(__file__))
            self.db_path = get_quant_system_db_path(self.quant_root)

            self.tables = self.load_tables()
            self.table_counts = {table: self.count_rows(table) for table in self.tables}

            self.update_kpis()
            self.update_navigation()

            if self.tables:
                preferred = "code_registry" if "code_registry" in self.tables else self.tables[0]
                self.select_table(preferred)

            self.status_var.set(f"Loaded: {self.db_path}")
            log_ok("Dashboard data refreshed.")

        except Exception as exc:
            self.status_var.set(f"Error: {exc}")
            log_error(str(exc))
            messagebox.showerror("Dashboard Error", str(exc))

    def load_data(self, table_name: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        if self.db_path is None:
            raise RuntimeError("Database path not initialized.")

        with read_only_connection(self.db_path) as conn:
            cursor = conn.execute(f"SELECT * FROM {quote_identifier(table_name)}")
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            data = [dict(row) for row in rows]

        return columns, data

    def load_tables(self) -> List[str]:
        if self.db_path is None:
            raise RuntimeError("Database path not initialized.")

        with read_only_connection(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name;
                """
            )
            return [row["name"] for row in cursor.fetchall()]

    def count_rows(self, table_name: str) -> int:
        if self.db_path is None:
            return 0

        try:
            with read_only_connection(self.db_path) as conn:
                cursor = conn.execute(
                    f"SELECT COUNT(*) AS count FROM {quote_identifier(table_name)}"
                )
                return int(cursor.fetchone()["count"])
        except Exception:
            return 0

    def update_kpis(self) -> None:
        total_rows = sum(self.table_counts.values())
        scripts = self.table_counts.get("code_registry", 0)
        events = self.table_counts.get("system_events", 0)

        db_size = "-"
        modified = "-"

        if self.db_path and self.db_path.exists():
            size_mb = self.db_path.stat().st_size / (1024 * 1024)
            db_size = f"{size_mb:.2f} MB"
            modified_ts = datetime.fromtimestamp(self.db_path.stat().st_mtime)
            modified = modified_ts.strftime("%Y-%m-%d %H:%M")

        self.kpi_vars["tables"].set(str(len(self.tables)))
        self.kpi_vars["rows"].set(str(total_rows))
        self.kpi_vars["db_size"].set(db_size)
        self.kpi_vars["scripts"].set(str(scripts))
        self.kpi_vars["events"].set(str(events))
        self.kpi_vars["modified"].set(modified)

    def update_navigation(self) -> None:
        for item in self.nav_tree.get_children():
            self.nav_tree.delete(item)

        groups = {
            "Registry": ["code_registry"],
            "Control Plane": [
                "strategies",
                "portfolios",
                "portfolio_members",
                "accounts",
                "deployments",
                "risk_limits",
                "governance_rules",
            ],
            "Events & Audit": ["system_events", "audit_logs"],
            "System": ["schema_migrations"],
            "Other": [],
        }

        assigned = set()
        for group, table_names in groups.items():
            parent = self.nav_tree.insert("", "end", text=group, values=("",), open=True)
            for table in table_names:
                if table in self.tables:
                    assigned.add(table)
                    self.nav_tree.insert(
                        parent,
                        "end",
                        iid=f"table::{table}",
                        text=table,
                        values=(self.table_counts.get(table, 0),),
                    )

        other_parent = None
        for table in self.tables:
            if table not in assigned:
                if other_parent is None:
                    other_parent = self.nav_tree.insert(
                        "", "end", text="Other", values=("",), open=True
                    )
                self.nav_tree.insert(
                    other_parent,
                    "end",
                    iid=f"table::{table}",
                    text=table,
                    values=(self.table_counts.get(table, 0),),
                )

    def select_table(self, table_name: str) -> None:
        iid = f"table::{table_name}"

        if self.nav_tree.exists(iid):
            self.nav_tree.selection_set(iid)
            self.nav_tree.focus(iid)

        self.current_table = table_name
        self.current_columns, self.current_rows = self.load_data(table_name)
        self.apply_filter()
        self.update_schema_details()

    def on_table_select(self, event: tk.Event) -> None:
        selection = self.nav_tree.selection()
        if not selection:
            return

        iid = selection[0]
        if not iid.startswith("table::"):
            return

        table_name = iid.replace("table::", "", 1)
        self.select_table(table_name)

    def clear_search(self) -> None:
        self.search_var.set("")
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search_var.get().strip().lower()

        if not query:
            self.filtered_rows = list(self.current_rows)
        else:
            filtered = []
            for row in self.current_rows:
                text = " ".join(str(value).lower() for value in row.values())
                if query in text:
                    filtered.append(row)
            self.filtered_rows = filtered

        self.update_table()

    def update_table(self) -> None:
        self.data_tree.delete(*self.data_tree.get_children())
        self.data_tree["columns"] = self.current_columns

        for column in self.current_columns:
            self.data_tree.heading(
                column,
                text=column,
                command=lambda col=column: self.sort_by_column(col),
            )
            width = max(110, min(260, len(column) * 12))
            self.data_tree.column(column, width=width, minwidth=80, stretch=True)

        for idx, row in enumerate(self.filtered_rows):
            values = [self.format_cell(row.get(column)) for column in self.current_columns]
            self.data_tree.insert("", "end", iid=str(idx), values=values)

        table_name = self.current_table or "No table selected"
        self.table_title_var.set(table_name)
        self.summary_var.set(
            f"{len(self.filtered_rows)} visible rows · {len(self.current_rows)} total rows"
        )

        self.detail_title_var.set("No row selected")
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", "Select a row to inspect details.")
        self.details_text.configure(state="disabled")

    def sort_by_column(self, column: str) -> None:
        try:
            self.filtered_rows.sort(key=lambda row: str(row.get(column, "")).lower())
            self.update_table()
        except Exception as exc:
            log_warn(f"Sort failed: {exc}")

    def on_row_select(self, event: tk.Event) -> None:
        selection = self.data_tree.selection()
        if not selection:
            return

        try:
            index = int(selection[0])
            row = self.filtered_rows[index]
            self.update_details(row)
        except Exception as exc:
            log_warn(f"Could not update details: {exc}")

    def update_details(self, row: Dict[str, Any]) -> None:
        title = self.current_table or "Row"
        self.detail_title_var.set(f"{title} row details")

        lines = []
        for key, value in row.items():
            lines.append(f"{key}:")
            lines.append(f"  {self.pretty_value(value)}")
            lines.append("")

        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", "end")
        self.details_text.insert("1.0", "\n".join(lines))
        self.details_text.configure(state="disabled")

        self.update_visual_flow(row)

    def update_schema_details(self) -> None:
        if not self.current_table or self.db_path is None:
            return

        try:
            with read_only_connection(self.db_path) as conn:
                cursor = conn.execute(
                    f"PRAGMA table_info({quote_identifier(self.current_table)})"
                )
                schema_rows = cursor.fetchall()

            schema_lines = [f"Schema: {self.current_table}", ""]
            for row in schema_rows:
                schema_lines.append(
                    f"- {row['name']} | {row['type']} | pk={row['pk']} | notnull={row['notnull']}"
                )

            self.details_text.configure(state="normal")
            self.details_text.delete("1.0", "end")
            self.details_text.insert("1.0", "\n".join(schema_lines))
            self.details_text.configure(state="disabled")

        except Exception as exc:
            log_warn(f"Schema details failed: {exc}")

    def update_visual_flow(self, row: Dict[str, Any]) -> None:
        inputs = row.get("inputs", "")
        outputs = row.get("outputs", "")
        name = row.get("script_name") or row.get("script_id") or self.current_table or "OBJECT"

        flow = f"INPUTS\n{self.pretty_value(inputs)}\n\n↓\n\n{name}\n\n↓\n\nOUTPUTS\n{self.pretty_value(outputs)}"

        self.flow_text.configure(state="normal")
        self.flow_text.delete("1.0", "end")
        self.flow_text.insert("1.0", flow)
        self.flow_text.configure(state="disabled")

    def run_code_registry_scanner(self) -> None:
        try:
            if self.quant_root is None:
                self.quant_root = find_quant_root(Path(__file__))

            scanner_path = (
                self.quant_root
                / "MANAGEMENT_LAYER"
                / "Code_Registry"
                / "scan_code_registry.py"
            )

            if not scanner_path.exists():
                messagebox.showwarning(
                    "Scanner not found",
                    f"Scanner not found:\n{scanner_path}",
                )
                return

            log_info(f"Running scanner: {scanner_path}")

            result = subprocess.run(
                [sys.executable, str(scanner_path)],
                cwd=str(self.quant_root),
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                messagebox.showerror(
                    "Scanner failed",
                    result.stderr or result.stdout or "Unknown scanner error",
                )
                return

            messagebox.showinfo("Scanner completed", result.stdout[-2000:])
            self.refresh_data()

        except Exception as exc:
            messagebox.showerror("Scanner Error", str(exc))

    @staticmethod
    def format_cell(value: Any) -> str:
        if value is None:
            return ""

        text = str(value)

        if len(text) > 160:
            return text[:157] + "..."

        return text

    @staticmethod
    def pretty_value(value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("[") or stripped.startswith("{"):
                try:
                    parsed = __import__("json").loads(stripped)
                    return __import__("json").dumps(parsed, indent=2, ensure_ascii=False)
                except Exception:
                    return value
            return value

        return str(value)


def refresh_data() -> None:
    raise RuntimeError("refresh_data() is available on QuantSystemDBDashboard instance.")


def load_data() -> None:
    raise RuntimeError("load_data() is available on QuantSystemDBDashboard instance.")


def update_table() -> None:
    raise RuntimeError("update_table() is available on QuantSystemDBDashboard instance.")


def update_details() -> None:
    raise RuntimeError("update_details() is available on QuantSystemDBDashboard instance.")


def build_panel(parent: tk.Widget, repository: Any = None, **kwargs: Any) -> QuantSystemDBDashboard:
    return QuantSystemDBDashboard(parent, repository=repository, **kwargs)


def main() -> None:
    root = tk.Tk()
    root.title(APP_TITLE)
    root.minsize(1100, 700)

    app = build_panel(root)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    main()