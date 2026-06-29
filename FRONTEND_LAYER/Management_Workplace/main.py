# ============================================================
# CODE_REGISTRY
# script_id: quant_system_db_main
# script_name: main.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Main Page
# purpose: Responsive main container for QUANT_SYSTEM.db Building Block widgets
# inputs: Widget files from widgets folder
# outputs: Desktop UI container
# upstream_data: ea_inventory_widget.py, code_registry_widget.py
# downstream_data: Management Workspace
# dependencies: tkinter, pathlib, importlib
# schedule: manual
# version: v3.0.0
# last_reviewed: 2026-06-18
# business_criticality: medium
# environment: desktop
# registry_group: frontend_main_pages
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, management-workspace, quant-system-db, main-container, responsive
# notes: Responsive Mac/Windows-safe main container. No native tk.Button.
# ============================================================

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable, Dict, Optional, Type

import tkinter as tk
from tkinter import messagebox


CODE_REGISTRY = {
    "script_id": "quant_system_db_main",
    "script_name": "main.py",
    "owner": "Leon Everts",
    "status": "active",
    "layer": "Frontend",
    "domain": "Management Workspace",
    "asset_type": "Tkinter Main Page",
    "purpose": "Responsive main container for QUANT_SYSTEM.db Building Block widgets",
    "inputs": "Widget files from widgets folder",
    "outputs": "Desktop UI container",
    "upstream_data": "ea_inventory_widget.py, code_registry_widget.py",
    "downstream_data": "Management Workspace",
    "dependencies": "tkinter, pathlib, importlib",
    "schedule": "manual",
    "version": "v3.0.0",
    "last_reviewed": "2026-06-18",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_main_pages",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,management-workspace,quant-system-db,main-container,responsive",
    "notes": "Responsive Mac/Windows-safe main container. No native tk.Button.",
}


APP_TITLE = "QUANT OS - QUANT_SYSTEM.db"

# Design System Tokens
BG = "#05080D"
TOPBAR = "#070B12"
SIDEBAR = "#0B111B"
PANEL = "#0E1623"
CARD = "#111827"
CARD_SOFT = "#0A1019"
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

FONT_TITLE = ("Helvetica", 24, "bold")
FONT_H1 = ("Helvetica", 17, "bold")
FONT_H2 = ("Helvetica", 12, "bold")
FONT_MAIN = ("Helvetica", 11)
FONT_SMALL = ("Helvetica", 10)
FONT_XS = ("Helvetica", 9)


def find_quant_root(start: Path) -> Path:
    current = start.resolve()
    for path in [current, *current.parents]:
        if (path / "CONTROL_PLANE").exists():
            return path
    raise FileNotFoundError("QUANT OS root not found. Expected CONTROL_PLANE folder.")


def load_widget_class(widget_file: Path, class_name: str) -> Type[tk.Frame]:
    if not widget_file.exists():
        raise FileNotFoundError(f"Widget file not found: {widget_file}")

    spec = importlib.util.spec_from_file_location(widget_file.stem, widget_file)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load import spec for: {widget_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    widget_class = getattr(module, class_name, None)
    if widget_class is None:
        raise ImportError(f"Class {class_name} not found in {widget_file}")

    return widget_class


class ClickableFrame(tk.Frame):
    """Mac/Windows safe button replacement using Frame + Label."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        bg: str = CARD_SOFT,
        fg: str = TEXT,
        active_bg: str = "#172338",
        border: str = BORDER,
        width: int = 130,
        height: int = 40,
        font=FONT_SMALL,
        anchor: str = "center",
        padx: int = 12,
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
            font=font,
            anchor=anchor,
            padx=padx,
            cursor="hand2",
        )
        self.label.pack(fill="both", expand=True)

        for w in (self, self.label):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _click(self, _event=None) -> None:
        self.command()

    def _enter(self, _event=None) -> None:
        self.configure(bg=self.active_bg)
        self.label.configure(bg=self.active_bg)

    def _leave(self, _event=None) -> None:
        self.configure(bg=self.normal_bg)
        self.label.configure(bg=self.normal_bg)

    def set_colors(self, bg: str, fg: str, border: Optional[str] = None) -> None:
        self.normal_bg = bg
        self.configure(bg=bg)
        if border is not None:
            self.configure(highlightbackground=border)
        self.label.configure(bg=bg, fg=fg)


class NavItem(tk.Frame):
    def __init__(self, parent: tk.Widget, text: str, command: Callable[[], None]):
        super().__init__(parent, bg=SIDEBAR, height=48, cursor="hand2")
        self.pack_propagate(False)
        self.command = command
        self.active = False

        self.label = tk.Label(
            self,
            text=text,
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_MAIN,
            anchor="w",
            padx=16,
            cursor="hand2",
        )
        self.label.pack(fill="both", expand=True)

        for w in (self, self.label):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _click(self, _event=None) -> None:
        self.command()

    def _enter(self, _event=None) -> None:
        if not self.active:
            self.configure(bg=PANEL)
            self.label.configure(bg=PANEL)

    def _leave(self, _event=None) -> None:
        if not self.active:
            self.configure(bg=SIDEBAR)
            self.label.configure(bg=SIDEBAR)

    def set_active(self, active: bool) -> None:
        self.active = active
        bg = BLUE_DARK if active else SIDEBAR
        fg = TEXT if active else MUTED
        self.configure(bg=bg)
        self.label.configure(bg=bg, fg=fg)


class PlaceholderWidget(tk.Frame):
    def __init__(self, parent: tk.Widget, title: str, message: str):
        super().__init__(parent, bg=BG)

        card = tk.Frame(
            self,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=28,
            pady=24,
        )
        card.pack(fill="both", expand=True, padx=18, pady=18)

        tk.Label(card, text=title, bg=CARD, fg=TEXT, font=FONT_H1).pack(anchor="w")

        tk.Label(
            card,
            text=message,
            bg=CARD,
            fg=MUTED,
            font=FONT_MAIN,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))


class QuantSystemDBMain(tk.Tk):
    BREAK_FULL = 1450
    BREAK_DESKTOP = 1150
    BREAK_TABLET = 820

    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1550x900")
        self.minsize(760, 620)
        self.configure(bg=BG)

        self.current_dir = Path(__file__).resolve().parent
        self.widgets_dir = self.current_dir / "widgets"
        self.quant_root = find_quant_root(Path(__file__))

        self.active_view = "overview"
        self.current_layout = ""
        self.resize_after_id: Optional[str] = None

        self.nav_items: Dict[str, NavItem] = {}
        self.overview_cards: Dict[str, tk.Frame] = {}

        self._build_shell()
        self.bind("<Configure>", self._on_resize)
        self.after(100, self.show_overview)
        self.after(200, self.apply_responsive_layout)

    # -----------------------------
    # Shell
    # -----------------------------

    def _build_shell(self) -> None:
        self.root_grid = tk.Frame(self, bg=BG)
        self.root_grid.pack(fill="both", expand=True)

        self.topbar = tk.Frame(
            self.root_grid,
            bg=TOPBAR,
            height=46,
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
        )
        self.topbar.pack(side="top", fill="x")
        self.topbar.pack_propagate(False)

        self.main_row = tk.Frame(self.root_grid, bg=BG)
        self.main_row.pack(side="top", fill="both", expand=True)

        self.sidebar = tk.Frame(
            self.main_row,
            bg=SIDEBAR,
            width=282,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.workspace_shell = tk.Frame(self.main_row, bg=BG)
        self.workspace_shell.pack(side="left", fill="both", expand=True)

        self.status_bar = tk.Frame(
            self.root_grid,
            bg=PANEL,
            height=44,
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
        )
        self.status_bar.pack(side="bottom", fill="x")
        self.status_bar.pack_propagate(False)

        self._build_topbar()
        self._build_sidebar()
        self._build_workspace()
        self._build_statusbar()

    def _build_topbar(self) -> None:
        tk.Label(
            self.topbar,
            text="QUANT OS",
            bg=TOPBAR,
            fg=TEXT,
            font=FONT_H2,
        ).pack(side="left", padx=(18, 8))

        tk.Label(
            self.topbar,
            text="v3.0",
            bg=TOPBAR,
            fg=BLUE,
            font=FONT_XS,
        ).pack(side="left")

        tk.Label(
            self.topbar,
            text="MANAGEMENT WORKSPACE",
            bg=TOPBAR,
            fg=BLUE,
            font=FONT_SMALL,
        ).pack(side="left", padx=(24, 0))

        self.topbar_status = tk.Label(
            self.topbar,
            text="MODE: WIDGET CONTAINER",
            bg=TOPBAR,
            fg=GREEN,
            font=FONT_SMALL,
        )
        self.topbar_status.pack(side="right", padx=(0, 18))

    def _build_sidebar(self) -> None:
        self.sidebar_header = tk.Frame(self.sidebar, bg=SIDEBAR)
        self.sidebar_header.pack(fill="x", padx=24, pady=(28, 22))

        tk.Label(
            self.sidebar_header,
            text="QUANT OS",
            bg=SIDEBAR,
            fg=TEXT,
            font=("Helvetica", 23, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.sidebar_header,
            text="MANAGEMENT WORKSPACE",
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_XS,
        ).pack(anchor="w", pady=(6, 0))

        self._line(self.sidebar, padx=24, pady=(0, 24))

        tk.Label(
            self.sidebar,
            text="QUANT_SYSTEM.db",
            bg=SIDEBAR,
            fg=BLUE,
            font=FONT_SMALL,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        self._nav("overview", "⌂   Overview", self.show_overview)
        self._nav("ea_inventory", "◉   EA Inventory", self.show_ea_inventory)
        self._nav("code_registry", "</>  Code Registry", self.show_code_registry)

        self.sidebar_spacer = tk.Frame(self.sidebar, bg=SIDEBAR)
        self.sidebar_spacer.pack(fill="both", expand=True)

        self._line(self.sidebar, padx=24, pady=(0, 20))

        self.sidebar_mode = tk.Frame(self.sidebar, bg=SIDEBAR)
        self.sidebar_mode.pack(fill="x", padx=24, pady=(0, 26))

        tk.Label(
            self.sidebar_mode,
            text="MODE",
            bg=SIDEBAR,
            fg=DIM,
            font=FONT_XS,
        ).pack(anchor="w")

        tk.Label(
            self.sidebar_mode,
            text="Widget Container",
            bg=SIDEBAR,
            fg=GREEN,
            font=FONT_H2,
        ).pack(anchor="w", pady=(8, 0))

        tk.Label(
            self.sidebar_mode,
            text="No direct DB writes",
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_XS,
        ).pack(anchor="w", pady=(5, 0))

    def _nav(self, key: str, text: str, command: Callable[[], None]) -> None:
        item = NavItem(self.sidebar, text, command)
        item.pack(fill="x", padx=18, pady=4)
        self.nav_items[key] = item

    def _build_workspace(self) -> None:
        self.workspace = tk.Frame(
            self.workspace_shell,
            bg=BG,
            highlightbackground=BORDER_SOFT,
            highlightthickness=1,
        )
        self.workspace.pack(fill="both", expand=True, padx=0, pady=0)

        self.header = tk.Frame(self.workspace, bg=BG)
        self.header.pack(fill="x", padx=34, pady=(30, 16))

        self.header_left = tk.Frame(self.header, bg=BG)
        self.header_left.pack(side="left", fill="x", expand=True)

        self.title_label = tk.Label(
            self.header_left,
            text="QUANT_SYSTEM.db Overview",
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE,
        )
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            self.header_left,
            text="Current Building Block Widgets",
            bg=BG,
            fg=MUTED,
            font=FONT_MAIN,
        )
        self.subtitle_label.pack(anchor="w", pady=(6, 0))

        self.header_right = tk.Frame(self.header, bg=BG)
        self.header_right.pack(side="right", anchor="ne")

        self.view_badge = tk.Label(
            self.header_right,
            text="READY",
            bg=PANEL,
            fg=GREEN,
            font=FONT_SMALL,
            padx=14,
            pady=6,
        )
        self.view_badge.pack(side="right")

        self._line(self.workspace, padx=34, pady=(0, 24))

        self.panel_host = tk.Frame(self.workspace, bg=BG)
        self.panel_host.pack(fill="both", expand=True, padx=34, pady=(0, 26))

    def _build_statusbar(self) -> None:
        tk.Label(
            self.status_bar,
            text="QUANT OS Management Workspace",
            bg=PANEL,
            fg=MUTED,
            font=FONT_XS,
        ).pack(side="left", padx=20)

        tk.Label(
            self.status_bar,
            text="Database:",
            bg=PANEL,
            fg=DIM,
            font=FONT_XS,
        ).pack(side="left", padx=(210, 6))

        tk.Label(
            self.status_bar,
            text="QUANT_SYSTEM.db",
            bg=PANEL,
            fg=TEXT,
            font=FONT_XS,
        ).pack(side="left")

        tk.Label(
            self.status_bar,
            text="Connected",
            bg=PANEL,
            fg=GREEN,
            font=FONT_XS,
        ).pack(side="left", padx=(8, 0))

        self.status_right = tk.Label(
            self.status_bar,
            text="Ready",
            bg=PANEL,
            fg=GREEN,
            font=FONT_XS,
        )
        self.status_right.pack(side="right", padx=20)

    def _line(self, parent: tk.Widget, padx: int, pady: tuple) -> None:
        tk.Frame(parent, bg=BORDER_SOFT, height=1).pack(fill="x", padx=padx, pady=pady)

    # -----------------------------
    # Responsive
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

        if layout == self.current_layout:
            return

        self.current_layout = layout

        if layout in ("full", "desktop"):
            self.sidebar.configure(width=282)
            self.sidebar.pack(side="left", fill="y")
            self.topbar_status.configure(text="MODE: WIDGET CONTAINER")
        elif layout == "tablet":
            self.sidebar.configure(width=220)
            self.sidebar.pack(side="left", fill="y")
            self.topbar_status.configure(text="TABLET LAYOUT")
        else:
            self.sidebar.pack_forget()
            self.topbar_status.configure(text="COMPACT LAYOUT")

        if self.active_view == "overview":
            self.show_overview(rebuild_only=True)

    # -----------------------------
    # View control
    # -----------------------------

    def set_active(self, key: str) -> None:
        self.active_view = key
        for nav_key, item in self.nav_items.items():
            item.set_active(nav_key == key)

    def clear_panel(self) -> None:
        for child in self.panel_host.winfo_children():
            child.destroy()

    # -----------------------------
    # Overview
    # -----------------------------

    def show_overview(self, rebuild_only: bool = False) -> None:
        self.set_active("overview")
        self.clear_panel()

        self.title_label.configure(text="QUANT_SYSTEM.db Overview")
        self.subtitle_label.configure(text="Current Building Block Widgets")
        self.view_badge.configure(text="OVERVIEW", fg=BLUE)
        self.status_right.configure(text="Overview")

        width = self.winfo_width()
        compact = width < self.BREAK_TABLET

        grid = tk.Frame(self.panel_host, bg=BG)
        grid.pack(fill="both", expand=True)

        cards = [
            {
                "key": "ea",
                "title": "EA Inventory",
                "subtitle": "Physical EA file inventory from Infrastructure Storage.",
                "status": "Widget available",
                "color": GREEN,
                "accent": BLUE,
                "command": self.show_ea_inventory,
            },
            {
                "key": "code",
                "title": "Code Registry",
                "subtitle": "Registered Python scripts and code objects.",
                "status": "Widget available",
                "color": GREEN,
                "accent": GREEN,
                "command": self.show_code_registry,
            },
            {
                "key": "next",
                "title": "Next Widgets",
                "subtitle": "Portfolio, Account, Broker and Events later.",
                "status": "Not built yet",
                "color": YELLOW,
                "accent": YELLOW,
                "command": None,
            },
            {
                "key": "principle",
                "title": "System Principle",
                "subtitle": "main.py only loads widgets. Widgets own their own data views.",
                "status": "Container only",
                "color": YELLOW,
                "accent": PURPLE,
                "command": None,
            },
        ]

        if compact:
            for i, spec in enumerate(cards):
                self._overview_card(grid, spec).grid(row=i, column=0, sticky="nsew", padx=0, pady=(0, 12))
                grid.grid_rowconfigure(i, weight=1)
            grid.grid_columnconfigure(0, weight=1)
        else:
            for i, spec in enumerate(cards):
                row = i // 2
                col = i % 2
                self._overview_card(grid, spec).grid(row=row, column=col, sticky="nsew", padx=10, pady=10)

            grid.grid_columnconfigure(0, weight=1, uniform="overview")
            grid.grid_columnconfigure(1, weight=1, uniform="overview")
            grid.grid_rowconfigure(0, weight=1, uniform="overview")
            grid.grid_rowconfigure(1, weight=1, uniform="overview")

    def _overview_card(self, parent: tk.Widget, spec: Dict[str, object]) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=24,
            pady=22,
        )

        top = tk.Frame(card, bg=CARD)
        top.pack(fill="both", expand=True)

        accent = tk.Frame(top, bg=str(spec["accent"]), width=4)
        accent.pack(side="left", fill="y", padx=(0, 18))

        content = tk.Frame(top, bg=CARD)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(
            content,
            text=str(spec["title"]),
            bg=CARD,
            fg=TEXT,
            font=FONT_H1,
        ).pack(anchor="w")

        tk.Label(
            content,
            text=str(spec["subtitle"]),
            bg=CARD,
            fg=MUTED,
            font=FONT_MAIN,
            wraplength=520,
            justify="left",
        ).pack(anchor="w", pady=(12, 0))

        tk.Label(
            content,
            text=str(spec["status"]),
            bg=CARD,
            fg=str(spec["color"]),
            font=FONT_H2,
        ).pack(anchor="w", pady=(18, 0))

        command = spec.get("command")
        if command is not None:
            ClickableFrame(
                content,
                text="Open Widget",
                command=command,  # type: ignore[arg-type]
                bg=CARD_SOFT,
                fg=BLUE,
                active_bg="#172338",
                border=BLUE,
                width=140,
                height=38,
            ).pack(anchor="w", pady=(22, 0))

        return card

    # -----------------------------
    # Widgets
    # -----------------------------

    def show_ea_inventory(self) -> None:
        self.set_active("ea_inventory")
        self.clear_panel()

        self.title_label.configure(text="EA Inventory")
        self.subtitle_label.configure(text="Frontend widget module")
        self.view_badge.configure(text="EA INVENTORY", fg=BLUE)
        self.status_right.configure(text="EA Inventory")

        try:
            widget_file = self.widgets_dir / "ea_inventory_widget.py"
            widget_class = load_widget_class(widget_file, "EAInventoryWidget")
            widget = widget_class(self.panel_host)
            widget.pack(fill="both", expand=True)

        except Exception as exc:
            messagebox.showerror("EA Inventory Widget Error", str(exc))
            PlaceholderWidget(
                self.panel_host,
                "EA Inventory Widget Error",
                str(exc),
            ).pack(fill="both", expand=True)

    def show_code_registry(self) -> None:
        self.set_active("code_registry")
        self.clear_panel()

        self.title_label.configure(text="Code Registry")
        self.subtitle_label.configure(text="Frontend widget module")
        self.view_badge.configure(text="CODE REGISTRY", fg=GREEN)
        self.status_right.configure(text="Code Registry")

        try:
            widget_file = self.widgets_dir / "code_registry_widget.py"
            widget_class = load_widget_class(widget_file, "CodeRegistryWidget")
            widget = widget_class(self.panel_host)
            widget.pack(fill="both", expand=True)

        except Exception as exc:
            messagebox.showerror("Code Registry Widget Error", str(exc))
            PlaceholderWidget(
                self.panel_host,
                "Code Registry Widget Error",
                str(exc),
            ).pack(fill="both", expand=True)


def main() -> None:
    app = QuantSystemDBMain()
    app.mainloop()


if __name__ == "__main__":
    main()
