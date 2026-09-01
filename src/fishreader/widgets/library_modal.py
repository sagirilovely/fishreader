"""Library modal: disguised as an "Open recent files" picker."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from fishreader.library import Candidate

DIM = "#6e7681"


class _BookItem(ListItem):
    """One library entry: filename (primary) + format/size (secondary)."""

    def __init__(self, cand: Candidate, current: bool):
        secondary = f"{cand.fmt.upper()} · {cand.size} bytes"
        if current:
            secondary += " · current"
        super().__init__(
            Label(cand.display_name),
            Label(secondary, classes="secondary"),
        )
        self.book_id = cand.id


class LibraryModal(ModalScreen[str | None]):
    """Open recent files — the book switcher (pure English chrome)."""

    CSS = """
    #lib-shell {
        width: 1fr;
        height: 1fr;
        align: center middle;
        background: #0d1117 80%;
    }
    #lib-box {
        width: 70;
        height: 16;
        background: #161b22;
        border: round #30363d;
        padding: 0 1;
    }
    #lib-title { height: 1; color: #8b949e; }
    #lib-list { height: 1fr; }
    .secondary { color: #6e7681; }
    #lib-hint { height: 1; color: #8b949e; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "close"),
        Binding("q", "cancel", "cancel"),
    ]

    def __init__(self, candidates: list[Candidate], current_id: str | None = None):
        super().__init__()
        self._candidates = candidates
        self._current_id = current_id

    def compose(self):
        items = [
            _BookItem(c, current=(c.id == self._current_id))
            for c in self._candidates
        ]
        with Vertical(id="lib-shell"):
            with Vertical(id="lib-box"):
                yield Static("Open recent files", id="lib-title")
                yield ListView(*items, id="lib-list")
                yield Static(
                    "arrow keys select · enter open · esc cancel",
                    id="lib-hint",
                )

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event) -> None:
        item: _BookItem = event.item
        self.dismiss(item.book_id)