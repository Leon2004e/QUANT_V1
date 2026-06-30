# ============================================================
# CODE_REGISTRY
# script_id: quant_system_db_main
# script_name: main.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Frontend Workspace Launcher
# asset_type: Tkinter Standalone Launcher
# purpose: Shows only workspaces at startup; expands widgets after workspace click
# inputs: Workspace folders and widget files inside FRONTEND_LAYER
# outputs: Desktop launcher UI + independent widget windows
# dependencies: tkinter, pathlib, subprocess, sys, importlib
# version: v5.0.0
# last_reviewed: 2026-06-30
# notes: Widgets are not visible at startup. They appear only after selecting a workspace.
# ============================================================

from __future__ import annotations

import importlib.util
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

import tkinter as tk
from tkinter import messagebox


APP_TITLE = "QUANT OS - FRONTEND WORKSPACES"

BG = "#010101"
TOPBAR = "#050505"
SIDEBAR = "#070707"
CARD = "#101010"
BORDER = "#303030"
BORDER_SOFT = "#1E1E1E"
TEXT = "#F2F2F2"
MUTED = "#9B9B9B"
DIM = "#6A6A6A"
BLACK = "#000000"
ORANGE = "#F5A623"
GREEN = "#00D060"
GREEN_DARK = "#008C3A"
RED = "#FF1744"

FONT_TITLE = ("Helvetica", 14, "bold")
FONT_MAIN = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_MONO = ("Menlo", 10)
FONT_MONO_SMALL = ("Menlo", 9)
FONT_MONO_XS = ("Menlo", 8)


@dataclass(frozen=True)
class WidgetSpec:
    label: str
    filename: str
    class_name: str
    title: str


@dataclass(frozen=True)
class WorkspaceSpec:
    label: str
    folder: str
    widgets: List[WidgetSpec]


def find_quant_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists() or (path / "FRONTEND_LAYER").exists():
            return path
    return current.parent


def detect_widget_class(widget_file: Path, preferred_class: str) -> str:
    """
    Uses the preferred class if available. Otherwise returns the first tkinter-like
    widget class found in the file. This keeps main.py robust if class names change.
    """
    try:
        spec = importlib.util.spec_from_file_location(widget_file.stem, widget_file)
        if spec is None or spec.loader is None:
            return preferred_class
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, preferred_class):
            return preferred_class
        for name, value in module.__dict__.items():
            if isinstance(value, type) and name.lower().endswith("widget"):
                return name
    except Exception:
        return preferred_class
    return preferred_class


WORKSPACES: List[WorkspaceSpec] = [
    WorkspaceSpec("EXECUTIVE WORKSPACE", "Executive_Workplace", []),
    WorkspaceSpec("PORTFOLIO WORKSPACE", "Portfolio_Workspace", []),
    WorkspaceSpec("STRATEGY WORKSPACE", "Strategy_Workspace", []),
    WorkspaceSpec("RESEARCH WORKSPACE", "Reseach_Workspace", []),
    WorkspaceSpec("LIVE TRADING WORKSPACE", "Live_Trading_Workplace", []),
    WorkspaceSpec("RISK WORKSPACE", "Risk_Workspace", []),
    WorkspaceSpec(
        "MANAGEMENT WORKSPACE",
        "Management_Workplace",
        [
            WidgetSpec("EA INVENTORY", "ea_inventory_widget.py", "EAInventoryWidget", "EA Inventory"),
            WidgetSpec("CODE REGISTRY", "code_registry_widget.py", "CodeRegistryWidget", "Code Registry"),
            WidgetSpec("TREE WIDGET", "tree_widget.py", "TreeWidget", "Tree Widget"),
        ],
    ),
]


class NavButton(tk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        index: str,
        indent: int = 0,
        active_getter: Optional[Callable[[], bool]] = None,
    ) -> None:
        super().__init__(
            parent,
            bg=SIDEBAR,
            height=34,
            cursor="hand2",
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
        )
        self.pack_propagate(False)
        self.command = command
        self.active_getter = active_getter
        self.indent = indent

        self.label = tk.Label(
            self,
            text=f"{index}  {text}",
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_MONO_XS,
            anchor="w",
            padx=10 + indent,
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
        self.configure(bg=ORANGE, highlightbackground=ORANGE)
        self.label.configure(bg=ORANGE, fg=BLACK)

    def _leave(self, _event=None) -> None:
        if self.active_getter and self.active_getter():
            self.configure(bg=CARD, highlightbackground=ORANGE_DARK)
            self.label.configure(bg=CARD, fg=ORANGE)
            return
        self.configure(bg=SIDEBAR, highlightbackground=BORDER_SOFT)
        self.label.configure(bg=SIDEBAR, fg=MUTED)

    def refresh_state(self) -> None:
        self._leave()


class QuantWorkspaceLauncher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("285x870")
        self.minsize(285, 650)
        self.maxsize(285, 1400)
        self.configure(bg=BG)

        self.current_dir = Path(__file__).resolve().parent
        self.quant_root = find_quant_root(Path(__file__))
        self.frontend_dir = self._resolve_frontend_dir()
        self.active_workspace: Optional[str] = None
        self.workspace_buttons: List[NavButton] = []
        self.running_processes: Dict[str, subprocess.Popen] = {}

        self._build_container()
        self.protocol("WM_DELETE_WINDOW", self._close_launcher_only)

    def _resolve_frontend_dir(self) -> Path:
        if self.current_dir.name == "FRONTEND_LAYER":
            return self.current_dir
        if (self.quant_root / "FRONTEND_LAYER").exists():
            return self.quant_root / "FRONTEND_LAYER"
        return self.current_dir

    def _build_container(self) -> None:
        self.container = tk.Frame(
            self,
            bg=SIDEBAR,
            width=285,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.container.pack(fill="both", expand=True)
        self.container.pack_propagate(False)

        self._build_header()
        self._line(pady=(0, 8))
        self._section("WORKSPACES")

        self.workspace_area = tk.Frame(self.container, bg=SIDEBAR)
        self.workspace_area.pack(fill="x", padx=0, pady=0)
        self._render_workspace_list()

        self._line(pady=(10, 8))
        self._section("SYSTEM")
        self._metric("MODE", "WORKSPACE TREE", ORANGE)
        self._metric("START VIEW", "WORKSPACES ONLY", GREEN)
        self._metric("PAGES", "SEPARATE", GREEN)
        self._metric("WRITE", "DISABLED", RED)

        spacer = tk.Frame(self.container, bg=SIDEBAR)
        spacer.pack(fill="both", expand=True)

        self._line(pady=(0, 8))
        self._section("ROOT")
        tk.Label(
            self.container,
            text=str(self.quant_root),
            bg=SIDEBAR,
            fg=DIM,
            font=FONT_MONO_XS,
            wraplength=250,
            justify="left",
        ).pack(anchor="w", padx=10, pady=(0, 12))

    def _build_header(self) -> None:
        top = tk.Frame(self.container, bg=TOPBAR, height=30)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="QUANT OS", bg=TOPBAR, fg=ORANGE, font=FONT_MONO_XS).pack(side="left", padx=(10, 6))
        tk.Label(top, text="FRONTEND", bg=GREEN_DARK, fg=TEXT, font=FONT_MONO_XS, padx=8, pady=2).pack(side="right", padx=8)

        header = tk.Frame(self.container, bg=SIDEBAR)
        header.pack(fill="x", padx=10, pady=(12, 8))

        tk.Label(header, text="WORKSPACE LAUNCHER", bg=SIDEBAR, fg=ORANGE, font=FONT_MONO_SMALL).pack(anchor="w")
        tk.Label(header, text="START: ONLY WORKSPACES", bg=SIDEBAR, fg=MUTED, font=FONT_MONO_XS).pack(anchor="w", pady=(4, 0))
        tk.Label(header, text="click workspace -> show widgets", bg=SIDEBAR, fg=DIM, font=FONT_MONO_XS).pack(anchor="w", pady=(4, 0))

    def _render_workspace_list(self) -> None:
        for child in self.workspace_area.winfo_children():
            child.destroy()
        self.workspace_buttons.clear()

        for workspace_index, workspace in enumerate(WORKSPACES, start=1):
            prefix = "▾" if self.active_workspace == workspace.label else "▸"
            button = NavButton(
                self.workspace_area,
                f"{prefix} {workspace.label}",
                lambda ws=workspace: self.toggle_workspace(ws),
                f"{workspace_index:02d}",
                active_getter=lambda label=workspace.label: self.active_workspace == label,
            )
            button.pack(fill="x", padx=8, pady=2)
            self.workspace_buttons.append(button)

            if self.active_workspace == workspace.label:
                self._render_workspace_widgets(workspace, workspace_index)

    def _render_workspace_widgets(self, workspace: WorkspaceSpec, workspace_index: int) -> None:
        workspace_path = self.frontend_dir / workspace.folder

        if not workspace.widgets:
            tk.Label(
                self.workspace_area,
                text="      no widgets assigned",
                bg=SIDEBAR,
                fg=DIM,
                font=FONT_MONO_XS,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(0, 4))
            return

        for widget_index, widget in enumerate(workspace.widgets, start=1):
            widget_path = workspace_path / widget.filename
            state = "●" if widget_path.exists() else "○"
            NavButton(
                self.workspace_area,
                f"{state} {widget.label}",
                lambda ws=workspace, w=widget: self.open_widget(ws, w),
                f"{workspace_index}.{widget_index}",
                indent=14,
            ).pack(fill="x", padx=(18, 8), pady=2)

    def toggle_workspace(self, workspace: WorkspaceSpec) -> None:
        if self.active_workspace == workspace.label:
            self.active_workspace = None
        else:
            self.active_workspace = workspace.label
        self._render_workspace_list()

    def _section(self, text: str) -> None:
        tk.Label(self.container, text=text, bg=SIDEBAR, fg=ORANGE, font=FONT_MONO_XS).pack(anchor="w", padx=10, pady=(4, 6))

    def _line(self, pady: tuple[int, int]) -> None:
        tk.Frame(self.container, bg=BORDER_SOFT, height=1).pack(fill="x", padx=8, pady=pady)

    def _metric(self, left: str, right: str, color: str) -> None:
        row = tk.Frame(self.container, bg=SIDEBAR)
        row.pack(fill="x", padx=10, pady=2)
        tk.Label(row, text=left, bg=SIDEBAR, fg=DIM, font=FONT_MONO_XS).pack(side="left")
        tk.Label(row, text=right, bg=SIDEBAR, fg=color, font=FONT_MONO_XS).pack(side="right")

    def open_widget(self, workspace: WorkspaceSpec, widget: WidgetSpec) -> None:
        workspace_dir = self.frontend_dir / workspace.folder
        widget_file = workspace_dir / widget.filename

        if not widget_file.exists():
            messagebox.showerror("Widget nicht gefunden", f"Datei fehlt:\n{widget_file}")
            return

        class_name = detect_widget_class(widget_file, widget.class_name)

        launcher_code = textwrap.dedent(
            f"""
            import importlib.util
            import tkinter as tk
            from pathlib import Path
            from tkinter import messagebox

            widget_file = Path({str(widget_file)!r})
            class_name = {class_name!r}
            title = {widget.title!r}

            try:
                spec = importlib.util.spec_from_file_location(widget_file.stem, widget_file)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load import spec for: {{widget_file}}")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                widget_class = getattr(module, class_name)

                root = tk.Tk()
                root.title(title)
                root.geometry("1350x850")
                root.minsize(900, 650)
                root.configure(bg="#010101")

                widget_instance = widget_class(root)
                widget_instance.pack(fill="both", expand=True)
                root.mainloop()
            except Exception as exc:
                error_root = tk.Tk()
                error_root.withdraw()
                messagebox.showerror(f"{{title}} Error", str(exc))
                error_root.destroy()
            """
        )

        try:
            process = subprocess.Popen(
                [sys.executable, "-c", launcher_code],
                cwd=str(workspace_dir),
            )
            self.running_processes[widget.title] = process
        except Exception as exc:
            messagebox.showerror("Start Error", str(exc))

    def _close_launcher_only(self) -> None:
        # Widget windows run in separate processes and remain independent.
        self.destroy()


def main() -> None:
    app = QuantWorkspaceLauncher()
    app.mainloop()


if __name__ == "__main__":
    main()
