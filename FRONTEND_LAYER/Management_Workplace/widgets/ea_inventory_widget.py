# ============================================================
# CODE_REGISTRY
# script_id: ea_inventory_widget
# script_name: ea_inventory_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Widget
# purpose: EA Inventory Widget for QUANT_SYSTEM.db Building Block
# inputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory
# outputs: Tkinter widget panel
# upstream_data: ea_file_inventory
# downstream_data: main.py
# dependencies: tkinter, sqlite3, pathlib
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-17
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, widget, ea-inventory, management-workspace
# notes: Read-only widget. Does not create or modify database tables.
# ============================================================

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, List, Tuple

import tkinter as tk
from tkinter import ttk, messagebox


CODE_REGISTRY = {
    "script_id": "ea_inventory_widget",
    "script_name": "ea_inventory_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Widget",
    "purpose": "EA Inventory Widget for QUANT_SYSTEM.db Building Block",
    "inputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> ea_file_inventory",
    "outputs": "Tkinter widget panel",
    "upstream_data": "ea_file_inventory",
    "downstream_data": "main.py",
    "dependencies": "tkinter, sqlite3, pathlib",
    "schedule": "manual",
    "version": "v1.0.0",
    "last_reviewed": "2026-06-17",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,widget,ea-inventory,management-workspace",
    "notes": "Read-only widget. Does not create or modify database tables.",
}


BG = "#080B10"
PANEL = "#111722"
PANEL_2 = "#151D2A"
BORDER = "#263244"
TEXT = "#E8EDF5"
MUTED = "#8F9BAD"
BLUE = "#4F8CFF"
GREEN = "#27D17F"
RED = "#FF5C5C"
YELLOW = "#F5B84B"

FONT_H1 = ("Segoe UI", 16, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MAIN = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)


def find_quant_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists() and (path / "INFRASTRUCTURE_LAYER").exists():
            return path
    raise FileNotFoundError("QUANT OS root not found.")


class EAInventoryDBService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def table_exists(self) -> bool:
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

    def count(self, where: str | None = None) -> int:
        if not self.table_exists():
            return 0

        sql = "SELECT COUNT(*) AS n FROM ea_file_inventory"
        if where:
            sql += f" WHERE {where}"

        with self.connect() as conn:
            row = conn.execute(sql).fetchone()

        return int(row["n"])

    def fetch_rows(self, search: str = "", limit: int = 800) -> Tuple[List[str], List[Tuple[Any, ...]]]:
        if not self.table_exists():
            return [], []

        columns = [
            "file_name",
            "symbol_from_folder",
            "symbol_from_filename",
            "ea_number",
            "strategy_id",
            "direction",
            "timeframe",
            "extension",
            "parse_status",
            "parse_error",
            "file_path",
        ]

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

        if search:
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
            params.extend([f"%{search}%"] * 8)

        sql += """
            ORDER BY parse_status, symbol_from_folder, ea_number, strategy_id
            LIMIT ?
        """
        params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return columns, [tuple(row[col] for col in columns) for row in rows]

    def symbol_distribution(self) -> List[Tuple[str, int]]:
        if not self.table_exists():
            return []

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    symbol_from_folder AS symbol,
                    COUNT(*) AS count
                FROM ea_file_inventory
                GROUP BY symbol_from_folder
                ORDER BY count DESC, symbol_from_folder
                """
            ).fetchall()

        return [(str(row["symbol"]), int(row["count"])) for row in rows]


class EAInventoryWidget(tk.Frame):
    def __init__(self, parent: tk.Widget, db_path: Path | None = None):
        super().__init__(parent, bg=BG)

        if db_path is None:
            root = find_quant_root(Path(__file__))
            db_path = root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db"

        self.db_path = db_path
        self.db = EAInventoryDBService(self.db_path)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")

        self._setup_style()
        self._build()
        self.refresh()

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "Treeview",
            background=PANEL,
            foreground=TEXT,
            fieldbackground=PANEL,
            rowheight=30,
            font=FONT_MAIN,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background=PANEL_2,
            foreground=TEXT,
            font=FONT_H2,
            borderwidth=0,
        )
        style.map(
            "Treeview",
            background=[("selected", "#22304A")],
            foreground=[("selected", TEXT)],
        )

    def _build(self) -> None:
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", pady=(0, 16))

        left = tk.Frame(header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text="EA Inventory", bg=BG, fg=TEXT, font=FONT_H1).pack(anchor="w")
        tk.Label(
            left,
            text="Read-only file inventory from Infrastructure Storage",
            bg=BG,
            fg=MUTED,
            font=FONT_MAIN,
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        tk.Button(
            right,
            text="Refresh",
            command=self.refresh,
            bg=PANEL_2,
            fg=TEXT,
            activebackground=PANEL,
            relief="flat",
            padx=16,
            pady=8,
            font=FONT_MAIN,
        ).pack(side="left", padx=(0, 8))

        tk.Label(right, textvariable=self.status_var, bg=BG, fg=GREEN, font=FONT_H2).pack(side="left")

        metrics = tk.Frame(self, bg=BG)
        metrics.pack(fill="x", pady=(0, 16))

        self.total_card = self._metric_card(metrics, "Total EA Files", "0", BLUE)
        self.valid_card = self._metric_card(metrics, "Valid", "0", GREEN)
        self.warning_card = self._metric_card(metrics, "Warnings", "0", YELLOW)
        self.invalid_card = self._metric_card(metrics, "Invalid", "0", RED)

        toolbar = tk.Frame(self, bg=BG)
        toolbar.pack(fill="x", pady=(0, 12))

        tk.Label(toolbar, text="Search", bg=BG, fg=MUTED, font=FONT_SMALL).pack(side="left", padx=(0, 8))

        entry = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            bg=PANEL,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_MAIN,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        entry.bind("<Return>", lambda _event: self.refresh())

        tk.Button(
            toolbar,
            text="Apply",
            command=self.refresh,
            bg=PANEL_2,
            fg=TEXT,
            activebackground=PANEL,
            relief="flat",
            padx=16,
            pady=8,
            font=FONT_MAIN,
        ).pack(side="left", padx=(8, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        left_panel = tk.Frame(body, bg=BG)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = tk.Frame(body, bg=BG, width=330)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)

        self.tree = ttk.Treeview(left_panel)
        self.tree.pack(side="left", fill="both", expand=True)

        y_scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.tree.yview)
        y_scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.symbol_tree = ttk.Treeview(right_panel)
        self.symbol_tree.pack(fill="both", expand=True)

        self._set_columns(
            self.tree,
            [
                "file_name",
                "folder_symbol",
                "filename_symbol",
                "ea_number",
                "strategy_id",
                "direction",
                "timeframe",
                "extension",
                "status",
                "error",
            ],
            {
                "file_name": 360,
                "folder_symbol": 120,
                "filename_symbol": 130,
                "ea_number": 90,
                "strategy_id": 130,
                "direction": 90,
                "timeframe": 90,
                "extension": 80,
                "status": 100,
                "error": 280,
            },
        )

        self._set_columns(
            self.symbol_tree,
            ["symbol", "count"],
            {"symbol": 180, "count": 80},
        )

    def _metric_card(self, parent: tk.Widget, title: str, value: str, color: str) -> dict:
        frame = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=18,
            pady=14,
        )
        frame.pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Label(frame, text=title, bg=PANEL, fg=MUTED, font=FONT_SMALL).pack(anchor="w")

        value_label = tk.Label(
            frame,
            text=value,
            bg=PANEL,
            fg=color,
            font=("Segoe UI", 24, "bold"),
        )
        value_label.pack(anchor="w", pady=(6, 0))

        return {"frame": frame, "value": value_label}

    def _set_columns(self, tree: ttk.Treeview, columns: List[str], widths: dict[str, int]) -> None:
        tree["columns"] = columns
        tree["show"] = "headings"

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=widths.get(col, 120), anchor="w", stretch=True)

    def _clear_tree(self, tree: ttk.Treeview) -> None:
        children = tree.get_children()
        if children:
            tree.delete(*children)

    def _short(self, value: Any, max_len: int = 140) -> str:
        if value is None:
            return ""

        text = str(value).replace("\n", " ").replace("\r", " ")

        if len(text) > max_len:
            return text[: max_len - 3] + "..."

        return text

    def refresh(self) -> None:
        try:
            total = self.db.count()
            valid = self.db.count("parse_status = 'valid'")
            warning = self.db.count("parse_status = 'warning'")
            invalid = self.db.count("parse_status = 'invalid'")

            self.total_card["value"].configure(text=str(total))
            self.valid_card["value"].configure(text=str(valid))
            self.warning_card["value"].configure(text=str(warning))
            self.invalid_card["value"].configure(text=str(invalid))

            self._clear_tree(self.tree)
            self._clear_tree(self.symbol_tree)

            cols, rows = self.db.fetch_rows(search=self.search_var.get().strip())

            wanted_cols = [
                "file_name",
                "symbol_from_folder",
                "symbol_from_filename",
                "ea_number",
                "strategy_id",
                "direction",
                "timeframe",
                "extension",
                "parse_status",
                "parse_error",
            ]

            idx = [cols.index(col) for col in wanted_cols if col in cols]

            for row in rows:
                values = [self._short(row[i]) for i in idx]
                self.tree.insert("", "end", values=values)

            for symbol, count in self.db.symbol_distribution():
                self.symbol_tree.insert("", "end", values=(symbol, count))

            self.status_var.set("Loaded")

        except Exception as exc:
            self.status_var.set("Error")
            messagebox.showerror("EA Inventory Error", str(exc))


def main() -> None:
    root = tk.Tk()
    root.title("EA Inventory Widget")
    root.geometry("1350x760")
    root.configure(bg=BG)

    widget = EAInventoryWidget(root)
    widget.pack(fill="both", expand=True, padx=18, pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
