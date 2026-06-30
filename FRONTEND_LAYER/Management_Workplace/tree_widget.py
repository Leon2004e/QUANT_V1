# ============================================================
# CODE_REGISTRY
# script_id: tree_widget
# script_name: tree_widget.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Widget
# purpose: File Tree Dashboard Widget for QUANT OS project structure
# inputs: Quant project root folder
# outputs: Tkinter widget panel, copied tree paths/text
# upstream_data: local filesystem
# downstream_data: main.py
# dependencies: tkinter, ttk, pathlib, os, subprocess, sys
# schedule: manual
# version: v1.0.0
# last_reviewed: 2026-06-30
# business_criticality: medium
# environment: desktop
# registry_group: frontend_widgets
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-30
# tags: frontend, widget, tree, management-workspace, dashboard
# notes: Bloomberg/terminal style Tkinter dashboard version of Tree.py. Same core functions without Textual dependency.
# ============================================================

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


# ============================================================
# DESIGN TOKENS
# ============================================================

BG = "#020403"
PANEL = "#070707"
CARD = "#101010"
CARD_2 = "#151515"
CARD_3 = "#050505"
BORDER = "#2A2A2A"
BORDER_SOFT = "#1A1A1A"

TEXT = "#F2F2F2"
MUTED = "#9B9B9B"
DIM = "#6F6F6F"

BLUE = "#F5A623"
GREEN = "#00C853"
YELLOW = "#FFD600"
RED = "#FF1744"
PURPLE = "#B56CFF"
CYAN = "#2D7DFF"

FONT_TITLE = ("Helvetica", 20, "bold")
FONT_H1 = ("Helvetica", 13, "bold")
FONT_H2 = ("Helvetica", 10, "bold")
FONT_MAIN = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_XS = ("Helvetica", 8)

IGNORE = {
    ".git", "__pycache__", ".DS_Store", ".venv", "venv",
    "node_modules", ".idea", ".vscode", ".pytest_cache", ".mypy_cache",
}

CODE_REGISTRY = {
    "script_id": "tree_widget",
    "script_name": "tree_widget.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Widget",
    "purpose": "File Tree Dashboard Widget for QUANT OS project structure",
    "inputs": "Quant project root folder",
    "outputs": "Tkinter widget panel, copied tree paths/text",
    "upstream_data": "local filesystem",
    "downstream_data": "main.py",
    "dependencies": "tkinter, ttk, pathlib, os, subprocess, sys",
    "schedule": "manual",
    "version": "v1.1.0",
    "last_reviewed": "2026-06-30",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_widgets",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-30",
    "tags": "frontend,widget,tree,management-workspace,dashboard",
    "notes": "Bloomberg/terminal style Tkinter dashboard version of Tree.py. Same core functions without Textual dependency.",
}


# ============================================================
# HELPERS
# ============================================================

def find_quant_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists():
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


# ============================================================
# CUSTOM MAC/WINDOWS SAFE BUTTON
# ============================================================

class ActionButton(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        width: int = 138,
        height: int = 34,
        bg: str = CARD_2,
        fg: str = TEXT,
        border: str = BORDER,
        active_bg: str = "#1A1A1A",
    ):
        super().__init__(parent, bg=bg, width=width, height=height, highlightbackground=border, highlightthickness=1)
        self.command = command
        self.bg_normal = bg
        self.bg_active = active_bg
        self.pack_propagate(False)

        self.label = tk.Label(self, text=text, bg=bg, fg=fg, font=FONT_SMALL, cursor="hand2")
        self.label.pack(fill="both", expand=True)

        for widget in (self, self.label):
            widget.bind("<Enter>", self._enter)
            widget.bind("<Leave>", self._leave)
            widget.bind("<Button-1>", self._click)

    def _enter(self, _event: tk.Event) -> None:
        self.configure(bg=self.bg_active)
        self.label.configure(bg=self.bg_active)

    def _leave(self, _event: tk.Event) -> None:
        self.configure(bg=self.bg_normal)
        self.label.configure(bg=self.bg_normal)

    def _click(self, _event: tk.Event) -> None:
        self.command()


# ============================================================
# TREE DASHBOARD WIDGET
# ============================================================

class TreeWidget(tk.Frame):
    def __init__(self, parent: tk.Widget, root_path: Optional[Path | str] = None):
        super().__init__(parent, bg=BG)

        start = Path(root_path).resolve() if root_path else Path.cwd().resolve()
        self.root_path = find_quant_root(start)
        self.marked_paths: Set[Path] = set()
        self.path_by_iid: Dict[str, Path] = {}
        self.iid_by_path: Dict[Path, str] = {}
        self._iid_counter = 0

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.root_var = tk.StringVar(value=str(self.root_path))

        self._build_ui()
        self._bind_keys()
        self.load_tree()

    # ---------- UI ----------

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        header = tk.Frame(self, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 8))
        header.columnconfigure(0, weight=1)

        title_row = tk.Frame(header, bg=BG)
        title_row.grid(row=0, column=0, sticky="w")
        tk.Label(title_row, text="TREE DASHBOARD", bg=BG, fg=TEXT, font=FONT_TITLE).pack(side="left")
        tk.Label(title_row, text="  TERMINAL VIEW", bg=BLUE, fg="#000000", font=FONT_XS, padx=8, pady=3).pack(side="left", padx=(12, 0))
        tk.Label(header, text="Project filesystem tree · mark · copy · open · refresh", bg=BG, fg=MUTED, font=FONT_SMALL).grid(row=1, column=0, sticky="w", pady=(2, 0))

        metrics = tk.Frame(header, bg=BG)
        metrics.grid(row=0, column=1, rowspan=2, sticky="e")
        self.total_card = self._metric_card(metrics, "Items", "0")
        self.folder_card = self._metric_card(metrics, "Folders", "0")
        self.file_card = self._metric_card(metrics, "Files", "0")
        self.marked_card = self._metric_card(metrics, "Marked", "0")

        controls = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        controls.columnconfigure(1, weight=1)

        tk.Label(controls, text="Root", bg=PANEL, fg=MUTED, font=FONT_SMALL).grid(row=0, column=0, sticky="w", padx=(12, 6), pady=(10, 4))
        root_entry = tk.Entry(controls, textvariable=self.root_var, bg=CARD_3, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_SMALL)
        root_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=(10, 4), ipady=6)
        ActionButton(controls, "Change Root", self.change_root, width=116).grid(row=0, column=2, padx=(0, 10), pady=(10, 4))

        tk.Label(controls, text="Search", bg=PANEL, fg=MUTED, font=FONT_SMALL).grid(row=1, column=0, sticky="w", padx=(12, 6), pady=(4, 10))
        search_entry = tk.Entry(controls, textvariable=self.search_var, bg=CARD_3, fg=TEXT, insertbackground=TEXT, relief="flat", font=FONT_SMALL)
        search_entry.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=(4, 10), ipady=6)
        ActionButton(controls, "Apply Search", self.apply_search, width=116).grid(row=1, column=2, padx=(0, 10), pady=(4, 10))

        action_bar = tk.Frame(self, bg=BG)
        action_bar.grid(row=3, column=0, sticky="ew", padx=18, pady=(10, 8))

        actions = [
            ("Expand All  E", self.expand_all, CARD_2),
            ("Collapse All  Z", self.collapse_all, CARD_2),
            ("Refresh  R", self.refresh_tree, CARD_2),
            ("Mark / Unmark  M", self.toggle_mark, CARD_2),
            ("Clear Marks  U", self.clear_marks, CARD_2),
            ("Copy View  C", self.copy_view, CARD_2),
            ("Copy Marked  X", self.copy_marked, CARD_2),
            ("Open Selected", self.open_selected, CARD_2),
            ("New Folder", self.new_folder, CARD_2),
            ("Export Tree", self.export_tree, CARD_2),
        ]
        for idx, (label, command, color) in enumerate(actions):
            ActionButton(action_bar, label, command, width=132, bg=color if color != CARD_2 else CARD_2).grid(row=idx // 5, column=idx % 5, padx=(0, 8), pady=(0, 8), sticky="w")

        body = tk.Frame(self, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        body.grid(row=2, column=0, sticky="nsew", padx=18)
        body.columnconfigure(0, weight=1)
        body.rowconfigure(1, weight=1)

        body_header = tk.Frame(body, bg=PANEL)
        body_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        body_header.columnconfigure(0, weight=1)
        tk.Label(body_header, text="Filesystem Tree", bg=PANEL, fg=TEXT, font=FONT_H1).grid(row=0, column=0, sticky="w")
        tk.Label(body_header, textvariable=self.status_var, bg=PANEL, fg=MUTED, font=FONT_SMALL).grid(row=0, column=1, sticky="e")

        tree_frame = tk.Frame(body, bg=PANEL)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, columns=("type", "relpath"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("relpath", text="Relative Path")
        self.tree.column("#0", width=360, anchor="w")
        self.tree.column("type", width=90, anchor="w")
        self.tree.column("relpath", width=520, anchor="w")
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.tag_configure("folder", foreground=TEXT)
        self.tree.tag_configure("file", foreground=MUTED)
        self.tree.tag_configure("marked", foreground=BLUE)

        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        self._style_treeview()
        self.tree.bind("<Double-1>", lambda _event: self.open_selected())
        self.tree.bind("<Return>", lambda _event: self.open_selected())
        self.tree.bind("<space>", lambda _event: self.toggle_mark())

    def _metric_card(self, parent: tk.Widget, title: str, value: str) -> tk.Label:
        frame = tk.Frame(parent, bg=CARD, highlightbackground=BORDER_SOFT, highlightthickness=1, width=92, height=54)
        frame.pack(side="left", padx=(8, 0))
        frame.pack_propagate(False)
        tk.Label(frame, text=title, bg=CARD, fg=MUTED, font=FONT_XS).pack(anchor="w", padx=10, pady=(7, 0))
        value_label = tk.Label(frame, text=value, bg=CARD, fg=TEXT, font=FONT_H2)
        value_label.pack(anchor="w", padx=10, pady=(2, 0))
        return value_label

    def _style_treeview(self) -> None:
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=CARD_3, foreground=TEXT, fieldbackground=CARD_3, rowheight=26, borderwidth=0, font=FONT_SMALL)
        style.configure("Treeview.Heading", background=CARD, foreground=TEXT, relief="flat", font=FONT_H2)
        style.map("Treeview", background=[("selected", BLUE)], foreground=[("selected", "#000000")])

    def _bind_keys(self) -> None:
        self.bind_all("<KeyPress-e>", lambda _e: self.expand_all())
        self.bind_all("<KeyPress-z>", lambda _e: self.collapse_all())
        self.bind_all("<KeyPress-r>", lambda _e: self.refresh_tree())
        self.bind_all("<KeyPress-m>", lambda _e: self.toggle_mark())
        self.bind_all("<KeyPress-u>", lambda _e: self.clear_marks())
        self.bind_all("<KeyPress-c>", lambda _e: self.copy_view())
        self.bind_all("<KeyPress-s>", lambda _e: self.copy_view())
        self.bind_all("<KeyPress-x>", lambda _e: self.copy_marked())

    # ---------- Filesystem ----------

    def is_ignored(self, path: Path) -> bool:
        return path.name in IGNORE

    def get_children(self, path: Path) -> List[Path]:
        try:
            items = [p for p in path.iterdir() if not self.is_ignored(p)]
            return sorted(items, key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return []

    def _next_iid(self) -> str:
        self._iid_counter += 1
        return f"node_{self._iid_counter}"

    def load_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self.path_by_iid.clear()
        self.iid_by_path.clear()
        self._iid_counter = 0

        search = self.search_var.get().strip().lower()
        root_iid = self._insert_node("", self.root_path)
        self.tree.item(root_iid, open=True)
        self._add_children(root_iid, self.root_path, search)
        self._update_metrics()
        self.set_status("Tree loaded")

    def _add_children(self, parent_iid: str, path: Path, search: str = "") -> bool:
        visible_any = False
        for child in self.get_children(path):
            child_match = not search or search in child.name.lower() or search in str(child.relative_to(self.root_path)).lower()
            iid = self._insert_node(parent_iid, child)
            descendant_match = False
            if child.is_dir():
                descendant_match = self._add_children(iid, child, search)
            visible = child_match or descendant_match
            if search and not visible:
                self.tree.delete(iid)
                self.path_by_iid.pop(iid, None)
                self.iid_by_path.pop(child, None)
            else:
                if search:
                    self.tree.item(parent_iid, open=True)
                    self.tree.item(iid, open=True)
                visible_any = True
        return visible_any

    def _insert_node(self, parent_iid: str, path: Path) -> str:
        iid = self._next_iid()
        self.path_by_iid[iid] = path
        self.iid_by_path[path] = iid
        rel = "." if path == self.root_path else str(path.relative_to(self.root_path))
        kind = "Folder" if path.is_dir() else "File"
        tags = ("folder",) if path.is_dir() else ("file",)
        if path in self.marked_paths:
            tags = tags + ("marked",)
        self.tree.insert(parent_iid, "end", iid=iid, text=self.format_label(path), values=(kind, rel), tags=tags)
        return iid

    def format_label(self, path: Path) -> str:
        icon = "📁" if path.is_dir() else "📄"
        marker = "★ " if path in self.marked_paths else ""
        return f"{marker}{icon} {path.name}"

    def refresh_labels(self) -> None:
        for iid, path in list(self.path_by_iid.items()):
            if self.tree.exists(iid):
                tags = ("folder",) if path.is_dir() else ("file",)
                if path in self.marked_paths:
                    tags = tags + ("marked",)
                self.tree.item(iid, text=self.format_label(path), tags=tags)
        self._update_metrics()

    # ---------- Tree actions ----------

    def expand_all(self) -> None:
        self._set_open_recursive("", True)
        self.set_status("Expanded all")

    def collapse_all(self) -> None:
        self._set_open_recursive("", False)
        roots = self.tree.get_children("")
        for iid in roots:
            self.tree.item(iid, open=True)
        self.set_status("Collapsed all")

    def _set_open_recursive(self, iid: str, open_state: bool) -> None:
        for child in self.tree.get_children(iid):
            self.tree.item(child, open=open_state)
            self._set_open_recursive(child, open_state)

    def refresh_tree(self) -> None:
        existing_marks = {p for p in self.marked_paths if p.exists()}
        self.marked_paths = existing_marks
        self.load_tree()
        self.set_status("Tree refreshed")

    def apply_search(self) -> None:
        self.load_tree()
        text = self.search_var.get().strip()
        self.set_status(f"Search applied: {text}" if text else "Search cleared")

    def selected_path(self) -> Optional[Path]:
        selection = self.tree.selection()
        if not selection:
            self.set_status("No tree item selected")
            return None
        return self.path_by_iid.get(selection[0])

    def toggle_mark(self) -> None:
        path = self.selected_path()
        if path is None:
            return
        if path in self.marked_paths:
            self.marked_paths.remove(path)
            self.set_status(f"Unmarked {path.name}")
        else:
            self.marked_paths.add(path)
            self.set_status(f"Marked {path.name}")
        self.refresh_labels()

    def clear_marks(self) -> None:
        self.marked_paths.clear()
        self.refresh_labels()
        self.set_status("Cleared marks")

    def open_selected(self) -> None:
        path = self.selected_path()
        if path is None:
            return
        open_path(path)
        self.set_status(f"Opened {path.name}")

    def change_root(self) -> None:
        folder = filedialog.askdirectory(initialdir=str(self.root_path), title="Select Tree Root")
        if not folder:
            return
        self.root_path = Path(folder).resolve()
        self.root_var.set(str(self.root_path))
        self.marked_paths.clear()
        self.load_tree()
        self.set_status("Root changed")

    def new_folder(self) -> None:
        base = self.selected_path() or self.root_path
        if base.is_file():
            base = base.parent
        name = simpledialog.askstring("New Folder", "Folder name:")
        if not name:
            return
        target = base / name
        try:
            target.mkdir(parents=False, exist_ok=False)
        except Exception as exc:
            messagebox.showerror("New Folder failed", str(exc))
            return
        self.refresh_tree()
        self.set_status(f"Created folder {target.name}")

    # ---------- Copy / export ----------

    def copy_view(self) -> None:
        text = self.get_visible_text()
        self._copy_to_clipboard(text)
        self.set_status("Copied current view")

    def copy_marked(self) -> None:
        if not self.marked_paths:
            self.set_status("No marked items")
            return
        lines = [str(p.relative_to(self.root_path)) for p in sorted(self.marked_paths, key=lambda p: str(p).lower())]
        self._copy_to_clipboard("\n".join(lines))
        self.set_status(f"Copied {len(lines)} marked item(s)")

    def export_tree(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Export Tree",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("Markdown Files", "*.md"), ("All Files", "*.*")],
            initialfile="quant_os_tree.txt",
        )
        if not path:
            return
        try:
            Path(path).write_text(self.get_visible_text(), encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        self.set_status(f"Exported tree: {Path(path).name}")

    def get_visible_text(self) -> str:
        lines: List[str] = []

        def walk(iid: str, depth: int) -> None:
            text = self.tree.item(iid, "text")
            lines.append("  " * depth + str(text))
            if self.tree.item(iid, "open"):
                for child in self.tree.get_children(iid):
                    walk(child, depth + 1)

        for root_iid in self.tree.get_children(""):
            walk(root_iid, 0)
        return "\n".join(lines)

    def _copy_to_clipboard(self, text: str) -> None:
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()

    # ---------- Status / metrics ----------

    def _update_metrics(self) -> None:
        items = list(self.path_by_iid.values())
        folders = sum(1 for p in items if p.is_dir())
        files = sum(1 for p in items if p.is_file())
        self.total_card.configure(text=str(len(items)))
        self.folder_card.configure(text=str(folders))
        self.file_card.configure(text=str(files))
        self.marked_card.configure(text=str(len(self.marked_paths)))

    def set_status(self, text: str) -> None:
        self.status_var.set(text)


# Backward-compatible alias for different main.py import styles.
FileTreeWidget = TreeWidget


def create_widget(parent: tk.Widget, root_path: Optional[Path | str] = None) -> TreeWidget:
    return TreeWidget(parent, root_path=root_path)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("TREE DASHBOARD - Bloomberg Style")
    root.geometry("1280x820")
    root.configure(bg=BG)
    widget = TreeWidget(root)
    widget.pack(fill="both", expand=True)
    root.mainloop()
