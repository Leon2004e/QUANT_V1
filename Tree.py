#!/usr/bin/env python3

from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Tree, Button, Static
from textual.containers import Horizontal, Vertical
import pyperclip

IGNORE = {
    ".git", "__pycache__", ".DS_Store", ".venv", "venv",
    "node_modules", ".idea", ".vscode", ".pytest_cache", ".mypy_cache"
}

class FileTreeApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }

    #toolbar {
        height: auto;
        padding: 1 1 0 1;
        background: #111827;
    }

    .button-row {
        height: 3;
        margin-bottom: 1;
    }

    Button {
        width: 1fr;
        min-width: 18;
        height: 3;
        margin-right: 1;
        content-align: center middle;
        text-style: bold;
    }

    #status {
        height: 1;
        padding-left: 1;
        color: #9ca3af;
    }

    Tree {
        height: 1fr;
        padding: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("e", "expand_all", "Expand All"),
        ("z", "collapse_all", "Collapse All"),
        ("m", "toggle_mark", "Mark"),
        ("u", "clear_marks", "Clear Marks"),
        ("s", "copy_view", "Copy"),
        ("c", "copy_view", "Copy"),
        ("x", "copy_marked", "Copy Marked"),
        ("r", "refresh_tree", "Refresh"),
    ]

    def __init__(self):
        super().__init__()
        self.root_path = Path.cwd().resolve()
        self.marked_paths = set()

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="toolbar"):
            with Horizontal(classes="button-row"):
                yield Button("Alle Ordner öffnen  E", id="expand", variant="primary")
                yield Button("Alle Ordner schließen  Z", id="collapse", variant="primary")
                yield Button("Baum neu laden  R", id="refresh", variant="primary")

            with Horizontal(classes="button-row"):
                yield Button("Markieren  M", id="mark", variant="warning")
                yield Button("Markierte kopieren  X", id="copy-marked", variant="success")
                yield Button("Markierungen löschen  U", id="clear-marks", variant="warning")

            with Horizontal(classes="button-row"):
                yield Button("Ansicht kopieren  C / S", id="copy", variant="success")
                yield Button("Programm beenden  Q", id="quit", variant="error")

        yield Static("Ready", id="status")
        yield Tree(str(self.root_path.name), id="tree")
        yield Footer()

    def on_mount(self) -> None:
        self.load_tree()

    def is_ignored(self, path: Path) -> bool:
        return path.name in IGNORE

    def get_children(self, path: Path):
        try:
            items = [p for p in path.iterdir() if not self.is_ignored(p)]
            return sorted(items, key=lambda p: (not p.is_dir(), p.name.lower()))
        except Exception:
            return []

    def load_tree(self):
        tree = self.query_one("#tree", Tree)
        tree.clear()

        root = tree.root
        root.label = self.format_label(self.root_path)
        root.data = self.root_path
        root.expand()

        self.add_children(root, self.root_path)
        self.set_status("Tree loaded")

    def add_children(self, node, path: Path):
        for child in self.get_children(path):
            child_node = node.add(self.format_label(child), data=child)

            if child.is_dir():
                self.add_children(child_node, child)

    def format_label(self, path: Path) -> str:
        icon = "📁" if path.is_dir() else "📄"
        marker = "★ " if path in self.marked_paths else ""
        return f"{marker}{icon} {path.name}"

    def refresh_labels(self):
        tree = self.query_one("#tree", Tree)

        def walk(node):
            if isinstance(node.data, Path):
                node.label = self.format_label(node.data)

            for child in node.children:
                walk(child)

        walk(tree.root)

    def expand_node_recursive(self, node):
        node.expand()
        for child in node.children:
            self.expand_node_recursive(child)

    def collapse_node_recursive(self, node):
        for child in node.children:
            self.collapse_node_recursive(child)
        node.collapse()

    def action_expand_all(self):
        tree = self.query_one("#tree", Tree)
        self.expand_node_recursive(tree.root)
        self.set_status("Expanded all")

    def action_collapse_all(self):
        tree = self.query_one("#tree", Tree)
        self.collapse_node_recursive(tree.root)
        tree.root.expand()
        self.set_status("Collapsed all")

    def get_visible_text(self):
        tree = self.query_one("#tree", Tree)
        lines = []

        def walk(node, depth=0):
            lines.append("  " * depth + str(node.label))

            if node.is_expanded:
                for child in node.children:
                    walk(child, depth + 1)

        walk(tree.root)
        return "\n".join(lines)

    def action_copy_view(self):
        text = self.get_visible_text()
        pyperclip.copy(text)
        self.set_status("Copied current view")

    def action_save_view(self):
        self.action_copy_view()

    def action_toggle_mark(self):
        tree = self.query_one("#tree", Tree)
        node = tree.cursor_node

        if node is None or not isinstance(node.data, Path):
            self.set_status("No tree item selected")
            return

        path = node.data

        if path in self.marked_paths:
            self.marked_paths.remove(path)
            self.set_status(f"Unmarked {path.name}")
        else:
            self.marked_paths.add(path)
            self.set_status(f"Marked {path.name}")

        self.refresh_labels()

    def action_clear_marks(self):
        self.marked_paths.clear()
        self.refresh_labels()
        self.set_status("Cleared marks")

    def action_copy_marked(self):
        if not self.marked_paths:
            self.set_status("No marked items")
            return

        lines = [
            str(path.relative_to(self.root_path))
            for path in sorted(self.marked_paths, key=lambda p: str(p).lower())
        ]
        pyperclip.copy("\n".join(lines))
        self.set_status(f"Copied {len(lines)} marked item(s)")

    def action_refresh_tree(self):
        self.load_tree()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "expand":
            self.action_expand_all()

        elif button_id == "collapse":
            self.action_collapse_all()

        elif button_id == "mark":
            self.action_toggle_mark()

        elif button_id == "clear-marks":
            self.action_clear_marks()

        elif button_id == "copy-marked":
            self.action_copy_marked()

        elif button_id in {"copy", "save"}:
            self.action_copy_view()

        elif button_id == "refresh":
            self.action_refresh_tree()

        elif button_id == "quit":
            self.exit()

    def set_status(self, text: str):
        self.query_one("#status", Static).update(text)


if __name__ == "__main__":
    app = FileTreeApp()
    app.run()
