# ============================================================
# CODE_REGISTRY
# script_id: quant_system_db_main
# script_name: main.py
# owner: Leon Everts
# status: active
# layer: Frontend
# domain: Management Workspace
# asset_type: Tkinter Main Page
# purpose: Main container for QUANT_SYSTEM.db Building Block widgets
# inputs: Widget files from widgets folder
# outputs: Desktop UI container
# upstream_data: ea_inventory_widget.py, code_registry_widget.py
# downstream_data: Management Workspace
# dependencies: tkinter, pathlib, importlib
# schedule: manual
# version: v2.2.0
# last_reviewed: 2026-06-17
# business_criticality: medium
# environment: desktop
# registry_group: frontend_main_pages
# author: Leon Everts
# reviewer: Leon Everts
# created_date: 2026-06-17
# tags: frontend, management-workspace, quant-system-db, main-container
# notes: Main page only displays widgets. It does not query or modify database tables directly.
# ============================================================

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable, Dict, Type

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
    "purpose": "Main container for QUANT_SYSTEM.db Building Block widgets",
    "inputs": "Widget files from widgets folder",
    "outputs": "Desktop UI container",
    "upstream_data": "ea_inventory_widget.py, code_registry_widget.py",
    "downstream_data": "Management Workspace",
    "dependencies": "tkinter, pathlib, importlib",
    "schedule": "manual",
    "version": "v2.2.0",
    "last_reviewed": "2026-06-17",
    "business_criticality": "medium",
    "environment": "desktop",
    "registry_group": "frontend_main_pages",
    "author": "Leon Everts",
    "reviewer": "Leon Everts",
    "created_date": "2026-06-17",
    "tags": "frontend,management-workspace,quant-system-db,main-container",
    "notes": "Main page only displays widgets. It does not query or modify database tables directly.",
}


APP_TITLE = "QUANT OS - QUANT_SYSTEM.db"

BG = "#080B10"
SIDEBAR = "#0D1118"
PANEL = "#111722"
PANEL_2 = "#151D2A"
BORDER = "#263244"
TEXT = "#E8EDF5"
MUTED = "#8F9BAD"
BLUE = "#4F8CFF"
GREEN = "#27D17F"
YELLOW = "#F5B84B"
RED = "#FF5C5C"

FONT_TITLE = ("Segoe UI", 22, "bold")
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


def load_widget_class(widget_file: Path, class_name: str) -> Type[tk.Frame]:
    if not widget_file.exists():
        raise FileNotFoundError(f"Widget file not found: {widget_file}")

    module_name = widget_file.stem
    spec = importlib.util.spec_from_file_location(module_name, widget_file)

    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load import spec for: {widget_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    widget_class = getattr(module, class_name, None)

    if widget_class is None:
        raise ImportError(f"Class {class_name} not found in {widget_file}")

    return widget_class


class PlaceholderWidget(tk.Frame):
    def __init__(self, parent: tk.Widget, title: str, message: str):
        super().__init__(parent, bg=BG)

        card = tk.Frame(
            self,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=28,
            pady=26,
        )
        card.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=FONT_H1).pack(anchor="w")
        tk.Label(card, text=message, bg=PANEL, fg=MUTED, font=FONT_MAIN, wraplength=900, justify="left").pack(
            anchor="w",
            pady=(10, 0),
        )


class QuantSystemDBMain(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title(APP_TITLE)
        self.geometry("1500x900")
        self.minsize(1200, 760)
        self.configure(bg=BG)

        self.current_dir = Path(__file__).resolve().parent
        self.widgets_dir = self.current_dir / "widgets"
        self.quant_root = find_quant_root(Path(__file__))

        self.active_view = "overview"
        self.nav_buttons: Dict[str, tk.Button] = {}

        self._build_ui()
        self.show_overview()

    def _build_ui(self) -> None:
        self.sidebar = tk.Frame(self, bg=SIDEBAR, width=270)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self._build_sidebar()
        self._build_header()
        self._build_panel_host()

    def _build_sidebar(self) -> None:
        header = tk.Frame(self.sidebar, bg=SIDEBAR)
        header.pack(fill="x", padx=22, pady=(30, 26))

        tk.Label(header, text="QUANT OS", bg=SIDEBAR, fg=TEXT, font=FONT_H1).pack(anchor="w")
        tk.Label(header, text="MANAGEMENT WORKSPACE", bg=SIDEBAR, fg=MUTED, font=FONT_SMALL).pack(
            anchor="w",
            pady=(2, 0),
        )

        tk.Label(
            self.sidebar,
            text="QUANT_SYSTEM.db",
            bg=SIDEBAR,
            fg=MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", padx=22, pady=(12, 8))

        self._nav_button("overview", "Overview", self.show_overview)
        self._nav_button("ea_inventory", "EA Inventory", self.show_ea_inventory)
        self._nav_button("code_registry", "Code Registry", self.show_code_registry)

        bottom = tk.Frame(self.sidebar, bg=SIDEBAR)
        bottom.pack(side="bottom", fill="x", padx=22, pady=24)

        tk.Label(bottom, text="MODE", bg=SIDEBAR, fg=MUTED, font=FONT_SMALL).pack(anchor="w")
        tk.Label(bottom, text="Widget Container", bg=SIDEBAR, fg=GREEN, font=FONT_H2).pack(anchor="w", pady=(8, 0))
        tk.Label(bottom, text="No direct DB writes", bg=SIDEBAR, fg=MUTED, font=FONT_SMALL).pack(anchor="w", pady=(4, 0))

    def _nav_button(self, key: str, text: str, command: Callable[[], None]) -> None:
        btn = tk.Button(
            self.sidebar,
            text=text,
            bg=SIDEBAR,
            fg=MUTED,
            activebackground=PANEL_2,
            activeforeground=TEXT,
            relief="flat",
            anchor="w",
            padx=18,
            pady=13,
            font=FONT_MAIN,
            command=command,
        )
        btn.pack(fill="x", padx=14, pady=3)
        self.nav_buttons[key] = btn

    def _build_header(self) -> None:
        self.header = tk.Frame(self.content, bg=BG)
        self.header.pack(fill="x", padx=36, pady=(28, 18))

        self.title_label = tk.Label(self.header, text="QUANT_SYSTEM.db", bg=BG, fg=TEXT, font=FONT_TITLE)
        self.title_label.pack(anchor="w")

        self.subtitle_label = tk.Label(
            self.header,
            text="Frontend Building Block · Widget Container",
            bg=BG,
            fg=MUTED,
            font=FONT_MAIN,
        )
        self.subtitle_label.pack(anchor="w", pady=(3, 0))

    def _build_panel_host(self) -> None:
        self.panel_host = tk.Frame(self.content, bg=BG)
        self.panel_host.pack(fill="both", expand=True, padx=36, pady=(0, 28))

    def set_active(self, key: str) -> None:
        self.active_view = key

        for nav_key, button in self.nav_buttons.items():
            if nav_key == key:
                button.configure(bg=PANEL_2, fg=TEXT)
            else:
                button.configure(bg=SIDEBAR, fg=MUTED)

    def clear_panel(self) -> None:
        for child in self.panel_host.winfo_children():
            child.destroy()

    def show_overview(self) -> None:
        self.set_active("overview")
        self.clear_panel()

        self.title_label.configure(text="QUANT_SYSTEM.db Overview")
        self.subtitle_label.configure(text="Current Building Block Widgets")

        grid = tk.Frame(self.panel_host, bg=BG)
        grid.pack(fill="both", expand=True)

        self._overview_card(
            grid,
            title="EA Inventory",
            subtitle="Physical EA file inventory from Infrastructure Storage",
            status="Widget available",
            color=BLUE,
            row=0,
            column=0,
            command=self.show_ea_inventory,
        )

        self._overview_card(
            grid,
            title="Code Registry",
            subtitle="Registered Python scripts and code objects",
            status="Widget available",
            color=GREEN,
            row=0,
            column=1,
            command=self.show_code_registry,
        )

        self._overview_card(
            grid,
            title="Next Widgets",
            subtitle="Portfolio, Account, Broker, Events later",
            status="Not built yet",
            color=MUTED,
            row=1,
            column=0,
            command=None,
        )

        self._overview_card(
            grid,
            title="System Principle",
            subtitle="main.py only loads widgets. Widgets own their own data views.",
            status="Container only",
            color=YELLOW,
            row=1,
            column=1,
            command=None,
        )

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

    def _overview_card(
        self,
        parent: tk.Widget,
        title: str,
        subtitle: str,
        status: str,
        color: str,
        row: int,
        column: int,
        command: Callable[[], None] | None,
    ) -> None:
        card = tk.Frame(
            parent,
            bg=PANEL,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=26,
            pady=24,
        )
        card.grid(row=row, column=column, sticky="nsew", padx=10, pady=10)

        tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=FONT_H1).pack(anchor="w")
        tk.Label(card, text=subtitle, bg=PANEL, fg=MUTED, font=FONT_MAIN).pack(anchor="w", pady=(8, 0))
        tk.Label(card, text=status, bg=PANEL, fg=color, font=FONT_H2).pack(anchor="w", pady=(18, 0))

        if command is not None:
            tk.Button(
                card,
                text="Open Widget",
                command=command,
                bg=PANEL_2,
                fg=TEXT,
                activebackground="#202A3A",
                activeforeground=TEXT,
                relief="flat",
                padx=16,
                pady=9,
                font=FONT_MAIN,
            ).pack(anchor="w", pady=(24, 0))

    def show_ea_inventory(self) -> None:
        self.set_active("ea_inventory")
        self.clear_panel()

        self.title_label.configure(text="EA Inventory")
        self.subtitle_label.configure(text="Frontend widget module")

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
