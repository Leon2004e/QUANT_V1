# ============================================================
# CODE_REGISTRY
# script_id: code_registry_widget
# script_name: code_registry_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Widget
# purpose: Code Registry Widget for QUANT_SYSTEM.db Building Block
# inputs: CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry
# outputs: Tkinter widget panel
# upstream_data: code_registry
# downstream_data: main.py
# dependencies: tkinter, sqlite3, pathlib, os, subprocess, sys
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-17
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, widget, code-registry, management-workspace
# notes: Read-only widget. Does not create or modify database tables.
# ============================================================

from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any, List, Tuple

import tkinter as tk
from tkinter import ttk, messagebox


CODE_REGISTRY = {
    "script_id": "code_registry_widget",
    "script_name": "code_registry_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Widget",
    "purpose": "Code Registry Widget for QUANT_SYSTEM.db Building Block",
    "inputs": "CONTROL_PLANE/Database/QUANT_SYSTEM.db -> code_registry",
    "outputs": "Tkinter widget panel",
    "upstream_data": "code_registry",
    "downstream_data": "main.py",
    "dependencies": "tkinter, sqlite3, pathlib, os, subprocess, sys",
    "schedule": "manual",
    "version": "v1.0.0",
    "last_reviewed": "2026-06-17",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,widget,code-registry,management-workspace",
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


def open_path(path: Path) -> None:
    if not path.exists():
        messagebox.showerror("File not found", str(path))
        return

    try:
        if sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False)
        elif os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
    except Exception as exc:
        messagebox.showerror("Open Error", str(exc))


class CodeRegistryDBService:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def table_exists(self, table: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT 1
                FROM sqlite_master
                WHERE type = 'table'
                  AND name = ?
                LIMIT 1;
                """,
                (table,),
            ).fetchone()

        return row is not None

    def count(self, where: str | None = None) -> int:
        if not self.table_exists("code_registry"):
            return 0

        sql = "SELECT COUNT(*) AS n FROM code_registry"

        if where:
            sql += f" WHERE {where}"

        with self.connect() as conn:
            row = conn.execute(sql).fetchone()

        return int(row["n"])

    def fetch_code_objects(self, search: str = "", limit: int = 500) -> Tuple[List[str], List[Tuple[Any, ...]]]:
        if not self.table_exists("code_registry"):
            return [], []

        columns = [
            "script_id",
            "script_name",
            "layer",
            "domain",
            "status",
            "version",
            "scan_status",
            "registry_source",
            "relative_path",
            "file_path",
        ]

        existing_columns = self.get_columns("code_registry")
        selected_columns = [col for col in columns if col in existing_columns]

        if not selected_columns:
            return [], []

        sql = "SELECT " + ", ".join([f'"{col}"' for col in selected_columns]) + " FROM code_registry WHERE 1=1"
        params: List[Any] = []

        if search:
            searchable = [
                col for col in selected_columns
                if col in {
                    "script_id",
                    "script_name",
                    "layer",
                    "domain",
                    "status",
                    "version",
                    "scan_status",
                    "registry_source",
                    "relative_path",
                    "file_path",
                }
            ]

            if searchable:
                sql += " AND ("
                sql += " OR ".join([f'CAST("{col}" AS TEXT) LIKE ?' for col in searchable])
                sql += ")"
                params.extend([f"%{search}%"] * len(searchable))

        if "layer" in selected_columns and "domain" in selected_columns and "script_id" in selected_columns:
            sql += ' ORDER BY "layer", "domain", "script_id"'
        elif "script_id" in selected_columns:
            sql += ' ORDER BY "script_id"'

        sql += " LIMIT ?"
        params.append(limit)

        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()

        return selected_columns, [tuple(row[col] for col in selected_columns) for row in rows]

    def get_columns(self, table: str) -> List[str]:
        if not self.table_exists(table):
            return []

        with self.connect() as conn:
            rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()

        return [str(row["name"]) for row in rows]

    def layer_distribution(self) -> List[Tuple[str, int]]:
        if not self.table_exists("code_registry"):
            return []

        if "layer" not in self.get_columns("code_registry"):
            return []

        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    layer,
                    COUNT(*) AS count
                FROM code_registry
                GROUP BY layer
                ORDER BY count DESC, layer
                """
            ).fetchall()

        return [(str(row["layer"]), int(row["count"])) for row in rows]


class CodeRegistryWidget(tk.Frame):
    def __init__(self, parent: tk.Widget, db_path: Path | None = None):
        super().__init__(parent, bg=BG)

        if db_path is None:
            root = find_quant_root(Path(__file__))
            db_path = root / "CONTROL_PLANE" / "Database" / "QUANT_SYSTEM.db"

        self.db_path = db_path
        self.db = CodeRegistryDBService(self.db_path)

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.selected_file_path: Path | None = None

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

        tk.Label(left, text="Code Registry", bg=BG, fg=TEXT, font=FONT_H1).pack(anchor="w")
        tk.Label(
            left,
            text="Read-only registry of Python scripts and system code objects",
            bg=BG,
            fg=MUTED,
            font=FONT_MAIN,
        ).pack(anchor="w", pady=(2, 0))

        right = tk.Frame(header, bg=BG)
        right.pack(side="right")

        tk.Button(
            right,
            text="Open Selected",
            command=self.open_selected_file,
            bg=PANEL_2,
            fg=TEXT,
            activebackground=PANEL,
            relief="flat",
            padx=16,
            pady=8,
            font=FONT_MAIN,
        ).pack(side="left", padx=(0, 8))

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

        self.total_card = self._metric_card(metrics, "Total Code Objects", "0", BLUE)
        self.valid_card = self._metric_card(metrics, "Valid", "0", GREEN)
        self.warning_card = self._metric_card(metrics, "Warnings", "0", YELLOW)
        self.missing_card = self._metric_card(metrics, "Missing Registry", "0", RED)

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

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected_file())

        self.layer_tree = ttk.Treeview(right_panel)
        self.layer_tree.pack(fill="both", expand=True)

        self._set_columns(
            self.tree,
            [
                "script_name",
                "script_id",
                "layer",
                "domain",
                "status",
                "version",
                "scan_status",
                "registry_source",
                "relative_path",
            ],
            {
                "script_name": 220,
                "script_id": 220,
                "layer": 140,
                "domain": 180,
                "status": 100,
                "version": 90,
                "scan_status": 130,
                "registry_source": 130,
                "relative_path": 380,
            },
        )

        self._set_columns(
            self.layer_tree,
            ["layer", "count"],
            {"layer": 220, "count": 80},
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

    def _short(self, value: Any, max_len: int = 120) -> str:
        if value is None:
            return ""

        text = str(value).replace("\n", " ").replace("\r", " ")

        if len(text) > max_len:
            return text[: max_len - 3] + "..."

        return text

    def refresh(self) -> None:
        try:
            total = self.db.count()
            valid = self.db.count("scan_status = 'valid'")
            warning = self.db.count("scan_status = 'warning'")
            missing = self.db.count("scan_status = 'missing_registry'")

            self.total_card["value"].configure(text=str(total))
            self.valid_card["value"].configure(text=str(valid))
            self.warning_card["value"].configure(text=str(warning))
            self.missing_card["value"].configure(text=str(missing))

            self._clear_tree(self.tree)
            self._clear_tree(self.layer_tree)

            cols, rows = self.db.fetch_code_objects(search=self.search_var.get().strip())

            wanted_source_cols = [
                "script_name",
                "script_id",
                "layer",
                "domain",
                "status",
                "version",
                "scan_status",
                "registry_source",
                "relative_path",
            ]

            idx = [cols.index(col) for col in wanted_source_cols if col in cols]

            file_path_idx = cols.index("file_path") if "file_path" in cols else None

            for row in rows:
                values = [self._short(row[i]) for i in idx]
                item_id = self.tree.insert("", "end", values=values)

                if file_path_idx is not None:
                    self.tree.set(item_id, "relative_path", self._short(row[wanted_source_cols.index("relative_path") if "relative_path" in wanted_source_cols and "relative_path" in cols else idx[-1]]))

            for layer, count in self.db.layer_distribution():
                self.layer_tree.insert("", "end", values=(layer, count))

            self.status_var.set("Loaded")

        except Exception as exc:
            self.status_var.set("Error")
            messagebox.showerror("Code Registry Error", str(exc))

    def on_select(self, _event=None) -> None:
        item_id = self.tree.focus()
        if not item_id:
            self.selected_file_path = None
            return

        values = self.tree.item(item_id, "values")
        if not values:
            self.selected_file_path = None
            return

        script_id = str(values[1]) if len(values) > 1 else ""

        if not script_id:
            self.selected_file_path = None
            return

        try:
            with self.db.connect() as conn:
                row = conn.execute(
                    """
                    SELECT file_path
                    FROM code_registry
                    WHERE script_id = ?
                    LIMIT 1;
                    """,
                    (script_id,),
                ).fetchone()

            if row and row["file_path"]:
                self.selected_file_path = Path(str(row["file_path"]))
            else:
                self.selected_file_path = None

        except Exception:
            self.selected_file_path = None

    def open_selected_file(self) -> None:
        if self.selected_file_path is None:
            messagebox.showwarning("No file selected", "Select a code registry row first.")
            return

        open_path(self.selected_file_path)


def main() -> None:
    root = tk.Tk()
    root.title("Code Registry Widget")
    root.geometry("1350x760")
    root.configure(bg=BG)

    widget = CodeRegistryWidget(root)
    widget.pack(fill="both", expand=True, padx=18, pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
