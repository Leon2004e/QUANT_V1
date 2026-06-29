# ============================================================
# CODE_REGISTRY
# script_id: tree_dashboard_widget
# script_name: tree_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Dashboard Widget
# purpose: Responsive QUANT OS File Tree Dashboard with visual object classification and clear marking
# inputs: Local QUANT OS project folder
# outputs: Tkinter dashboard panel, clipboard text
# upstream_data: local filesystem
# downstream_data: main.py / manual usage
# dependencies: tkinter, ttk, pathlib, os, subprocess, sys, datetime
# schedule: manual
# version: v1.1.0
# last_reviewed: 2026-06-20
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-20
# tags: frontend, widget, file-tree, system-explorer, management-workspace, dashboard
# notes: Console removed. Strong visual classification and marking.
# ============================================================

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


BG = "#05080D"
CARD = "#111827"
CARD_2 = "#0E1623"
BORDER = "#263449"
BORDER_SOFT = "#1B2738"

TEXT = "#F4F7FB"
MUTED = "#9AA7B8"
BLUE = "#3B82F6"
BLUE_DARK = "#0B4EDB"
GREEN = "#22C55E"
YELLOW = "#FACC15"
RED = "#EF4444"
PURPLE = "#8B5CF6"
CYAN = "#22D3EE"
ORANGE = "#F97316"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_H2 = ("Helvetica", 11, "bold")
FONT_SMALL = ("Helvetica", 9)
FONT_XS = ("Helvetica", 8)
FONT_TREE = ("Helvetica", 10, "bold")

CODE_REGISTRY = {
    "script_id": "tree_dashboard_widget",
    "script_name": "tree_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Dashboard Widget",
    "purpose": "Responsive QUANT OS File Tree Dashboard with visual object classification and clear marking.",
    "inputs": "Local QUANT OS project folder",
    "outputs": "Tkinter dashboard panel, clipboard text",
    "upstream_data": "local filesystem",
    "downstream_data": "main.py / manual usage",
    "dependencies": "tkinter, ttk, pathlib, os, subprocess, sys, datetime",
    "schedule": "manual",
    "version": "v1.1.0",
    "last_reviewed": "2026-06-20",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-20",
    "tags": "frontend,widget,file-tree,system-explorer,management-workspace,dashboard",
    "notes": "Console removed. Strong visual classification and marking.",
}

IGNORE_NAMES = {
    ".git", "__pycache__", ".DS_Store", ".venv", "venv", "env", "node_modules",
    ".idea", ".vscode", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".ipynb_checkpoints",
}

ROOT_MARKERS = {
    "CONTROL_PLANE", "QUANT_SYSTEM.db", "Data_Center", "Strategy_Center",
    "Portfolio_Center", "Management_Layer", "FRONTEND_LAYER", "BACKEND_LAYER",
    "INFRASTRUCTURE_LAYER", "README.md", "requirements.txt",
}

CODE_FOLDER_NAMES = {
    "widgets", "Dashboard", "src", "scripts", "utils", "core", "services", "engines",
    "FRONTEND_LAYER", "BACKEND_LAYER", "Strategy_Center", "Portfolio_Center",
    "Risk_Center", "Execution_Center",
}

DATA_FOLDER_NAMES = {
    "Data_Center", "Data", "Database", "Databases", "outputs", "input", "inputs",
    "exports", "logs", "Reports", "Backtest_Trades_Data", "CONTROL_PLANE",
    "Storage", "1_Pipeline", "2_Baseline", "3_Research", "4_Production", "5_Catalog",
}

MANAGEMENT_FOLDER_NAMES = {
    "Management_Layer", "Management_Workplace", "Documentation", "System_Info",
    "Layer_Guides", "SOPs", "AI_Prompts", "Decision_Log", "Roadmap", "GOVERNANCE_LAYER",
}

CODE_EXTENSIONS = {
    ".py", ".ipynb", ".mq5", ".mq4", ".js", ".ts", ".html", ".css",
    ".json", ".yaml", ".yml", ".toml", ".sh",
}

DATA_EXTENSIONS = {
    ".csv", ".xlsx", ".xls", ".parquet", ".db", ".sqlite", ".sqlite3",
    ".jsonl", ".txt", ".log",
}

DOC_EXTENSIONS = {".md", ".pdf", ".docx", ".pptx"}


def find_quant_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for path in [current, *current.parents]:
        try:
            names = {p.name for p in path.iterdir()}
        except Exception:
            continue
        if names.intersection(ROOT_MARKERS):
            return path
    return current


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


def safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except Exception:
        return str(path)


def is_ignored(path: Path) -> bool:
    return path.name in IGNORE_NAMES


def get_children(path: Path) -> List[Path]:
    try:
        children = [p for p in path.iterdir() if not is_ignored(p)]
        return sorted(children, key=lambda p: (not p.is_dir(), p.name.lower()))
    except Exception:
        return []


def format_size(size_bytes: int) -> str:
    if size_bytes <= 0:
        return "-"
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(size_bytes)
    for unit in units:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size if path.is_file() else 0
    except Exception:
        return 0


def directory_size(path: Path, max_files: int = 15000) -> int:
    total = 0
    scanned = 0
    try:
        for item in path.rglob("*"):
            if scanned >= max_files:
                break
            if is_ignored(item):
                continue
            if item.is_file():
                try:
                    total += item.stat().st_size
                    scanned += 1
                except Exception:
                    pass
    except Exception:
        pass
    return total


def modified_time(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return "-"


def count_items(root: Path, max_items: int = 50000) -> Tuple[int, int, int]:
    folders = 0
    files = 0
    scanned = 0
    try:
        for item in root.rglob("*"):
            if scanned >= max_items:
                break
            if is_ignored(item):
                continue
            if item.is_dir():
                folders += 1
            elif item.is_file():
                files += 1
            scanned += 1
    except Exception:
        pass
    return folders + files, folders, files


def copy_text_to_clipboard(widget: tk.Widget, text: str) -> None:
    widget.clipboard_clear()
    widget.clipboard_append(text)
    widget.update()


def classify_path(path: Path) -> str:
    suffix = path.suffix.lower()

    if path.is_dir():
        return "folder"

    if suffix in CODE_EXTENSIONS:
        return "code_file"
    if suffix in DATA_EXTENSIONS:
        return "data_file"
    if suffix in DOC_EXTENSIONS:
        return "doc_file"
    return "file"


def path_symbol(path: Path) -> str:
    category = classify_path(path)
    symbols = {
        "folder": "◇ DIR",
        "code_file": "λ CODE" if path.suffix.lower() == ".py" else "⚙ CODE",
        "data_file": "▣ DATA",
        "doc_file": "□ DOC",
        "file": "· FILE",
    }
    return symbols.get(category, "· FILE")


def item_type(path: Path) -> str:
    labels = {
        "folder": "Folder",
        "code_file": "Code File",
        "data_file": "Data File",
        "doc_file": "Document",
        "file": "File",
    }
    return labels.get(classify_path(path), "File")


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
            parent, bg=bg, width=width, height=height,
            highlightbackground=border, highlightthickness=1, cursor="hand2",
        )
        self.pack_propagate(False)
        self.command = command
        self.normal_bg = bg
        self.active_bg = active_bg
        self.label = tk.Label(self, text=text, bg=bg, fg=fg, font=FONT_SMALL, cursor="hand2")
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


class FileTreeService:
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve()

    def stats(self) -> Dict[str, Any]:
        total, folders, files = count_items(self.root_path)
        return {"total": total, "folders": folders, "files": files, "size": directory_size(self.root_path)}

    def children(self, path: Path) -> List[Path]:
        return get_children(path)

    def tree_text(self, marked_paths: Optional[Set[Path]] = None) -> str:
        marked_paths = marked_paths or set()
        lines: List[str] = []

        def walk(folder: Path, depth: int) -> None:
            prefix = "    " * depth
            mark = "[MARKED] " if folder in marked_paths else ""
            lines.append(f"{prefix}{mark}{path_symbol(folder)} {folder.name}/")
            for child in self.children(folder):
                child_mark = "[MARKED] " if child in marked_paths else ""
                if child.is_dir():
                    walk(child, depth + 1)
                else:
                    lines.append(f"{'    ' * (depth + 1)}{child_mark}{path_symbol(child)} {child.name}")

        walk(self.root_path, 0)
        return "\n".join(lines)


class TreeDashboardWidget(tk.Frame):
    BREAK_FULL = 1380
    BREAK_DESKTOP = 1100
    BREAK_TABLET = 850

    def __init__(self, parent: tk.Widget, root_path: Optional[Path] = None):
        super().__init__(parent, bg=BG)
        self.root_path = (root_path or find_quant_root(Path.cwd())).resolve()
        self.service = FileTreeService(self.root_path)
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Loaded")
        self.layout_var = tk.StringVar(value="Layout: initializing")
        self.path_var = tk.StringVar(value=str(self.root_path))
        self.selected_path: Optional[Path] = self.root_path
        self.marked_paths: Set[Path] = set()
        self.node_to_path: Dict[str, Path] = {}
        self.current_layout = ""
        self.current_orient = ""
        self.resize_after_id: Optional[str] = None
        self.metric_cards: Dict[str, Dict[str, tk.Label]] = {}
        self.detail_labels: Dict[str, tk.Label] = {}

        self._setup_styles()
        self._build_dashboard()
        self.bind("<Configure>", self._on_resize)
        self.after(100, self.refresh_all)
        self.after(250, self.apply_responsive_layout)

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "TreeDash.Treeview", background=CARD_2, foreground=TEXT, fieldbackground=CARD_2,
            rowheight=34, font=FONT_TREE, borderwidth=0, relief="flat", indent=24,
        )
        style.configure(
            "TreeDash.Treeview.Heading", background=CARD, foreground=MUTED,
            font=FONT_SMALL, borderwidth=0, relief="flat",
        )
        style.map("TreeDash.Treeview", background=[("selected", "#1F3A5F")], foreground=[("selected", TEXT)])
        style.configure("Vertical.TScrollbar", background=CARD, troughcolor=CARD_2, bordercolor=BORDER, arrowcolor=MUTED)
        style.configure("Horizontal.TScrollbar", background=CARD, troughcolor=CARD_2, bordercolor=BORDER, arrowcolor=MUTED)

    def _build_dashboard(self) -> None:
        self._build_header()
        self._build_metrics()
        self._build_toolbar()
        self._build_body()
        self._build_footer()

    def _build_header(self) -> None:
        self.header = tk.Frame(self, bg=BG)
        self.header.pack(fill="x", pady=(0, 10))

        left = tk.Frame(self.header, bg=BG)
        left.pack(side="left", fill="x", expand=True)

        title_row = tk.Frame(left, bg=BG)
        title_row.pack(anchor="w", fill="x")
        tk.Label(title_row, text="System Tree", bg=BG, fg=TEXT, font=FONT_TITLE).pack(side="left")
        tk.Label(title_row, text="/ Management Workspace", bg=BG, fg=BLUE, font=FONT_XS).pack(side="left", padx=(12, 0), pady=(8, 0))
        tk.Label(
            left,
            text="Visual object tree for QUANT OS folders, code files, data files and management documents",
            bg=BG, fg=MUTED, font=FONT_SMALL,
        ).pack(anchor="w", pady=(6, 0))

        right = tk.Frame(self.header, bg=BG)
        right.pack(side="right", anchor="ne")
        tk.Label(right, textvariable=self.layout_var, bg=BG, fg=MUTED, font=FONT_XS).pack(side="left", padx=(0, 12))

        status_box = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=7)
        status_box.pack(side="right")
        tk.Label(status_box, text="●", bg=CARD, fg=GREEN, font=FONT_XS).pack(side="left", padx=(0, 8))
        tk.Label(status_box, textvariable=self.status_var, bg=CARD, fg=TEXT, font=FONT_XS).pack(side="left")

    def _build_metrics(self) -> None:
        self.metrics_host = tk.Frame(self, bg=BG)
        self.metrics_host.pack(fill="x", pady=(0, 10))
        specs = [
            ("total", "TOTAL ITEMS", BLUE, "folders + files"),
            ("folders", "FOLDERS", GREEN, "directory objects"),
            ("files", "FILES", CYAN, "file objects"),
            ("marked", "MARKED", YELLOW, "selected paths"),
            ("size", "ROOT SIZE", PURPLE, "scanned size"),
        ]
        for key, title, color, subtitle in specs:
            card = tk.Frame(self.metrics_host, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=16, pady=13, height=88)
            card.pack_propagate(False)
            tk.Label(card, text=title, bg=CARD, fg=MUTED, font=FONT_XS).pack(anchor="w")
            value_label = tk.Label(card, text="0", bg=CARD, fg=TEXT, font=("Helvetica", 21, "bold"))
            value_label.pack(anchor="w", pady=(6, 0))
            sub_label = tk.Label(card, text=subtitle, bg=CARD, fg=MUTED, font=FONT_XS)
            sub_label.pack(anchor="w", pady=(3, 0))
            tk.Label(card, text="●", bg=CARD, fg=color, font=FONT_XS).place(relx=0.95, rely=0.47)
            self.metric_cards[key] = {"frame": card, "value": value_label, "sub": sub_label}

    def _build_toolbar(self) -> None:
        self.toolbar = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=10)
        self.toolbar.pack(fill="x", pady=(0, 10))

        self.search_box = tk.Frame(self.toolbar, bg=CARD_2, highlightbackground=BORDER, highlightthickness=1)
        tk.Label(self.search_box, text="Search", bg=CARD_2, fg=MUTED, font=FONT_XS).pack(side="left", padx=(12, 8))
        self.search_entry = tk.Entry(
            self.search_box, textvariable=self.search_var, bg=CARD_2, fg=TEXT,
            insertbackground=TEXT, relief="flat", font=FONT_SMALL,
        )
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda _event: self.apply_search())

        self.btn_search = ActionButton(self.toolbar, "Find", self.apply_search, width=76, bg=BLUE_DARK, fg=TEXT, border=BLUE)
        self.btn_refresh = ActionButton(self.toolbar, "Refresh", self.refresh_all, width=88)
        self.btn_mark = ActionButton(self.toolbar, "Mark", self.toggle_mark_selected, width=78, border=YELLOW, fg=YELLOW)
        self.btn_copy_marked = ActionButton(self.toolbar, "Copy Marked", self.copy_marked, width=112)
        self.btn_copy_tree = ActionButton(self.toolbar, "Copy Tree", self.copy_tree, width=96)
        self.btn_open = ActionButton(self.toolbar, "Open", self.open_selected, width=76)
        self.btn_choose_root = ActionButton(self.toolbar, "Change Root", self.choose_root, width=112)
        self.btn_clear = ActionButton(self.toolbar, "Clear Marks", self.clear_marks, width=104, border=RED, fg=RED)

    def _build_body(self) -> None:
        self.body = tk.Frame(self, bg=BG)
        self.body.pack(fill="both", expand=True)
        self.paned = tk.PanedWindow(
            self.body, orient=tk.HORIZONTAL, bg=BG, sashwidth=7, sashrelief="raised",
            bd=0, showhandle=True, handlesize=12, opaqueresize=True,
        )
        self.paned.pack(fill="both", expand=True)
        self.left_panel = tk.Frame(self.paned, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=10, pady=10)
        self.right_panel = tk.Frame(self.paned, bg=BG)
        self._build_tree_panel()
        self._build_right_panel()
        self.paned.add(self.left_panel, minsize=460)
        self.paned.add(self.right_panel, minsize=300)

    def _build_tree_panel(self) -> None:
        table_header = tk.Frame(self.left_panel, bg=CARD)
        table_header.pack(fill="x", pady=(0, 8))
        tk.Label(table_header, text="Directory Tree", bg=CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        self.tree_count_label = tk.Label(table_header, text="0 items", bg=CARD, fg=MUTED, font=FONT_XS)
        self.tree_count_label.pack(side="right")

        path_box = tk.Frame(self.left_panel, bg=CARD_2, highlightbackground=BORDER_SOFT, highlightthickness=1, padx=10, pady=7)
        path_box.pack(fill="x", pady=(0, 8))
        tk.Label(path_box, text="Root", bg=CARD_2, fg=MUTED, font=FONT_XS).pack(side="left", padx=(0, 8))
        tk.Label(path_box, textvariable=self.path_var, bg=CARD_2, fg=TEXT, font=FONT_XS, anchor="w").pack(side="left", fill="x", expand=True)

        tree_container = tk.Frame(self.left_panel, bg=CARD_2)
        tree_container.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_container, style="TreeDash.Treeview", show="tree headings", columns=("type", "size", "modified"))
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("modified", text="Modified")
        self.tree.column("#0", width=430, minwidth=280, stretch=True)
        self.tree.column("type", width=150, minwidth=110, anchor="w")
        self.tree.column("size", width=100, minwidth=70, anchor="w")
        self.tree.column("modified", width=140, minwidth=110, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.y_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview, style="Vertical.TScrollbar")
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.x_scroll = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview, style="Horizontal.TScrollbar")
        self.x_scroll.grid(row=1, column=0, sticky="ew")
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)
        self.tree.configure(yscrollcommand=self.y_scroll.set, xscrollcommand=self.x_scroll.set)

        self.tree.tag_configure("folder", foreground=TEXT)
        self.tree.tag_configure("code_file", foreground="#7DD3FC")
        self.tree.tag_configure("data_file", foreground="#86EFAC")
        self.tree.tag_configure("doc_file", foreground=YELLOW)
        self.tree.tag_configure("file", foreground=MUTED)
        self.tree.tag_configure("marked", background="#4A3800", foreground="#FFF7AD")
        self.tree.tag_configure("marked_code", background="#103954", foreground="#CFFAFE")
        self.tree.tag_configure("marked_data", background="#123C21", foreground="#DCFCE7")
        self.tree.tag_configure("marked_management", background="#302052", foreground="#EDE9FE")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<<TreeviewOpen>>", self.on_tree_open)
        self.tree.bind("<Double-1>", lambda _event: self.open_selected())

    def _build_right_panel(self) -> None:
        self.inspector_card = tk.Frame(self.right_panel, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=12)
        tk.Label(self.inspector_card, text="Inspector", bg=CARD, fg=TEXT, font=FONT_H2).pack(anchor="w")
        for key in ["name", "category", "type", "relative_path", "size", "modified", "full_path"]:
            row = tk.Frame(self.inspector_card, bg=CARD)
            row.pack(fill="x", pady=(6, 0))
            tk.Label(row, text=key, bg=CARD, fg=MUTED, font=FONT_XS, width=14, anchor="w").pack(side="left")
            label = tk.Label(row, text="-", bg=CARD, fg=TEXT, font=FONT_XS, anchor="w", justify="left", wraplength=340)
            label.pack(side="left", fill="x", expand=True)
            self.detail_labels[key] = label

        self.legend_card = tk.Frame(self.right_panel, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=12)
        tk.Label(self.legend_card, text="Legend", bg=CARD, fg=TEXT, font=FONT_H2).pack(anchor="w")
        legend_rows = [
            ("◇ DIR", "All folders", TEXT),
            ("λ CODE", "Python/code file", "#7DD3FC"),
            ("⚙ CODE", "Config/code file", CYAN),
            ("▣ DATA", "CSV/DB/data file", "#86EFAC"),
            ("□ DOC", "Documentation file", YELLOW),
            ("!!! MARKED", "Marked item", ORANGE),
        ]
        for symbol, label_text, color in legend_rows:
            row = tk.Frame(self.legend_card, bg=CARD)
            row.pack(fill="x", pady=(5, 0))
            tk.Label(row, text=symbol, bg=CARD, fg=color, font=FONT_XS, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=label_text, bg=CARD, fg=MUTED, font=FONT_XS, anchor="w").pack(side="left", fill="x", expand=True)

        self.marked_card = tk.Frame(self.right_panel, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=14, pady=12)
        marked_header = tk.Frame(self.marked_card, bg=CARD)
        marked_header.pack(fill="x")
        tk.Label(marked_header, text="Marked Paths", bg=CARD, fg=TEXT, font=FONT_H2).pack(side="left")
        self.marked_count_label = tk.Label(marked_header, text="0 selected", bg=CARD, fg=MUTED, font=FONT_XS)
        self.marked_count_label.pack(side="right")
        self.marked_list = tk.Listbox(
            self.marked_card, bg=CARD_2, fg=YELLOW, selectbackground="#4A3800",
            selectforeground=TEXT, relief="flat", highlightthickness=1,
            highlightbackground=BORDER_SOFT, font=FONT_TREE, height=12,
        )
        self.marked_list.pack(fill="both", expand=True, pady=(8, 0))

    def _build_footer(self) -> None:
        self.footer = tk.Frame(self, bg=CARD, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=8)
        self.footer.pack(fill="x", pady=(10, 0))
        self.footer_label = tk.Label(
            self.footer,
            text="SYSTEM STATUS: OPERATIONAL | ACTIVE LAYER: FRONTEND | VERSION: v1.1.0",
            bg=CARD, fg=MUTED, font=FONT_XS, anchor="w",
        )
        self.footer_label.pack(side="left", fill="x", expand=True)

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
            self._layout_right_panel(layout)
            self._set_orientation(layout)

        self.after(80, self._set_sash_position)

    def _layout_metrics(self, layout: str) -> None:
        for data in self.metric_cards.values():
            data["frame"].pack_forget()
        if layout == "full":
            keys = ["total", "folders", "files", "marked", "size"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 10))
        elif layout == "desktop":
            keys = ["total", "folders", "files", "marked"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 10))
        elif layout == "tablet":
            keys = ["total", "folders", "files"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(side="left", fill="x", expand=True, padx=(0, 8))
        else:
            keys = ["total", "marked"]
            for key in keys:
                self.metric_cards[key]["frame"].pack(fill="x", pady=(0, 8))

    def _layout_toolbar(self, layout: str) -> None:
        widgets = [
            self.search_box, self.btn_search, self.btn_refresh, self.btn_mark,
            self.btn_copy_marked, self.btn_copy_tree, self.btn_open,
            self.btn_choose_root, self.btn_clear,
        ]
        for widget in widgets:
            widget.pack_forget()

        if layout in ("full", "desktop"):
            self.search_box.pack(side="left", fill="x", expand=True, padx=(0, 10))
            self.btn_search.pack(side="left", padx=(0, 8))
            self.btn_refresh.pack(side="left", padx=(0, 8))
            self.btn_mark.pack(side="left", padx=(0, 8))
            self.btn_copy_marked.pack(side="left", padx=(0, 8))
            self.btn_copy_tree.pack(side="left", padx=(0, 8))
            self.btn_open.pack(side="left", padx=(0, 8))
            self.btn_choose_root.pack(side="left", padx=(0, 8))
            self.btn_clear.pack(side="right")
        elif layout == "tablet":
            self.search_box.pack(fill="x", pady=(0, 8))
            for widget in widgets[1:7]:
                widget.pack(side="left", padx=(0, 8))
        else:
            self.search_box.pack(fill="x", pady=(0, 8))
            self.btn_search.pack(side="left", padx=(0, 6))
            self.btn_refresh.pack(side="left", padx=(0, 6))
            self.btn_mark.pack(side="left", padx=(0, 6))
            self.btn_copy_marked.pack(side="left", padx=(0, 6))

    def _layout_right_panel(self, layout: str) -> None:
        for widget in [self.inspector_card, self.legend_card, self.marked_card]:
            widget.pack_forget()
        if layout in ("full", "desktop"):
            self.inspector_card.pack(fill="x", pady=(0, 10))
            self.legend_card.pack(fill="x", pady=(0, 10))
            self.marked_card.pack(fill="both", expand=True)
        elif layout == "tablet":
            self.inspector_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.legend_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
            self.marked_card.pack(side="left", fill="both", expand=True)
        else:
            self.inspector_card.pack(fill="x", pady=(0, 8))
            self.legend_card.pack(fill="x", pady=(0, 8))
            self.marked_card.pack(fill="both", expand=True)

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
                self.paned.sash_place(0, int(width * 0.66), 0)
            else:
                height = max(self.paned.winfo_height(), 1)
                self.paned.sash_place(0, 0, int(height * 0.60))
        except Exception:
            pass

    def refresh_all(self) -> None:
        self.path_var.set(str(self.root_path))
        self.node_to_path.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        root_item = self.tree.insert(
            "", "end",
            text=self._display_name(self.root_path),
            values=(item_type(self.root_path), "-", modified_time(self.root_path)),
            open=True,
            tags=self._tags_for_path(self.root_path),
        )
        self.node_to_path[root_item] = self.root_path
        self._insert_children(root_item, self.root_path)

        stats = self.service.stats()
        self.metric_cards["total"]["value"].configure(text=str(stats["total"]))
        self.metric_cards["folders"]["value"].configure(text=str(stats["folders"]))
        self.metric_cards["files"]["value"].configure(text=str(stats["files"]))
        self.metric_cards["marked"]["value"].configure(text=str(len(self.marked_paths)))
        self.metric_cards["size"]["value"].configure(text=format_size(int(stats["size"])))
        self.tree_count_label.configure(text=f"{stats['total']} items")
        self.update_marked_list()
        self.update_inspector(self.root_path)
        self.status_var.set("Loaded")

    def _insert_children(self, parent_item: str, folder: Path) -> None:
        for child in self.service.children(folder):
            item = self.tree.insert(
                parent_item,
                "end",
                text=self._display_name(child),
                values=(item_type(child), format_size(file_size(child)), modified_time(child)),
                open=False,
                tags=self._tags_for_path(child),
            )
            self.node_to_path[item] = child

            if child.is_dir() and self.service.children(child):
                dummy = self.tree.insert(item, "end", text="Loading...", values=("", "", ""), tags=("file",))
                self.node_to_path[dummy] = child

    def on_tree_open(self, _event=None) -> None:
        item = self.tree.focus()
        path = self.node_to_path.get(item)
        if not path or not path.is_dir():
            return
        children = self.tree.get_children(item)
        if len(children) == 1 and self.tree.item(children[0], "text") == "Loading...":
            self.tree.delete(children[0])
            self._insert_children(item, path)

    def on_tree_select(self, _event=None) -> None:
        item = self.tree.focus()
        path = self.node_to_path.get(item)
        if not path:
            return
        self.selected_path = path
        self.update_inspector(path)
        self.footer_label.configure(
            text=f"SYSTEM STATUS: OPERATIONAL | SELECTED: {safe_relative(path, self.root_path)} | VERSION: v1.1.0"
        )

    def _display_name(self, path: Path) -> str:
        mark = "!!! MARKED !!!  " if path in self.marked_paths else ""
        return f"{mark}{path_symbol(path)}  {path.name}"

    def _tags_for_path(self, path: Path) -> Tuple[str, ...]:
        category = classify_path(path)

        if path not in self.marked_paths:
            return (category,)

        if category == "code_file":
            return (category, "marked_code")
        if category == "data_file":
            return (category, "marked_data")
        if category == "doc_file":
            return (category, "marked_management")

        return (category, "marked")

    def _refresh_visible_labels(self) -> None:
        for item, path in list(self.node_to_path.items()):
            try:
                self.tree.item(item, text=self._display_name(path), tags=self._tags_for_path(path))
            except Exception:
                pass

    def update_inspector(self, path: Path) -> None:
        size_value = format_size(directory_size(path)) if path.is_dir() else format_size(file_size(path))
        values = {
            "name": path.name,
            "category": path_symbol(path),
            "type": item_type(path),
            "relative_path": safe_relative(path, self.root_path),
            "size": size_value,
            "modified": modified_time(path),
            "full_path": str(path),
        }
        for key, label in self.detail_labels.items():
            label.configure(text=self._short(values.get(key, "-"), 90))

    def update_marked_list(self) -> None:
        self.marked_list.delete(0, tk.END)
        for path in sorted(self.marked_paths, key=lambda p: str(p).lower()):
            self.marked_list.insert(tk.END, f"!!! MARKED !!!  {path_symbol(path)}  {safe_relative(path, self.root_path)}")
        self.marked_count_label.configure(text=f"{len(self.marked_paths)} selected")
        self.metric_cards["marked"]["value"].configure(text=str(len(self.marked_paths)))

    def toggle_mark_selected(self) -> None:
        if self.selected_path is None:
            messagebox.showwarning("No selection", "Select a path first.")
            return
        path = self.selected_path
        if path in self.marked_paths:
            self.marked_paths.remove(path)
        else:
            self.marked_paths.add(path)
        self._refresh_visible_labels()
        self.update_marked_list()

    def clear_marks(self) -> None:
        self.marked_paths.clear()
        self._refresh_visible_labels()
        self.update_marked_list()

    def copy_marked(self) -> None:
        if not self.marked_paths:
            messagebox.showwarning("No marked paths", "No paths are marked.")
            return
        text = "\n".join(safe_relative(path, self.root_path) for path in sorted(self.marked_paths, key=lambda p: str(p).lower()))
        copy_text_to_clipboard(self, text)

    def copy_tree(self) -> None:
        text = self.service.tree_text(self.marked_paths)
        copy_text_to_clipboard(self, text)

    def open_selected(self) -> None:
        if self.selected_path is None:
            messagebox.showwarning("No selection", "Select a path first.")
            return
        open_path(self.selected_path)

    def choose_root(self) -> None:
        selected = filedialog.askdirectory(title="Choose QUANT OS root folder")
        if not selected:
            return
        self.root_path = Path(selected).resolve()
        self.service = FileTreeService(self.root_path)
        self.marked_paths.clear()
        self.selected_path = self.root_path
        self.refresh_all()

    def apply_search(self) -> None:
        query = self.search_var.get().strip().lower()
        if not query:
            return
        found = self._find_first_match(query)
        if found:
            self.tree.selection_set(found)
            self.tree.focus(found)
            self.tree.see(found)
            path = self.node_to_path.get(found)
            if path:
                self.selected_path = path
                self.update_inspector(path)
        else:
            messagebox.showinfo("Search", f"No match found for: {query}")

    def _find_first_match(self, query: str) -> Optional[str]:
        def walk(item: str) -> Optional[str]:
            path = self.node_to_path.get(item)
            if path and query in path.name.lower():
                return item
            if path and path.is_dir():
                self.tree.item(item, open=True)
                self.on_tree_open()
            for child in self.tree.get_children(item):
                result = walk(child)
                if result:
                    return result
            return None

        for root_item in self.tree.get_children():
            result = walk(root_item)
            if result:
                return result
        return None

    def _short(self, value: Any, max_len: int = 120) -> str:
        text = str(value).replace("\n", " ").replace("\r", " ").strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 3] + "..."


def main() -> None:
    root = tk.Tk()
    root.title("QUANT OS - System Tree")
    root.geometry("1450x850")
    root.minsize(760, 620)
    root.configure(bg=BG)

    widget = TreeDashboardWidget(root)
    widget.pack(fill="both", expand=True, padx=18, pady=18)

    root.mainloop()


if __name__ == "__main__":
    main()
