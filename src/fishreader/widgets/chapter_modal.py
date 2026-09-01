"""Chapter modal: a disguised table of contents for jumping to a chapter."""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

from fishreader.models import Chapter
from fishreader.textlayout import display_width

_MAX_TITLE_WIDTH = 58


def _truncate(title: str, max_width: int = _MAX_TITLE_WIDTH) -> str:
    """Truncate by display width so long chapter names fit the picker."""
    if display_width(title) <= max_width:
        return title
    cut = 0
    while cut < len(title) and display_width(title[: cut + 1]) <= max_width - 1:
        cut += 1
    return title[: max(1, cut)] + "…"


class _ChapterItem(ListItem):
    def __init__(self, chapter: Chapter, current: bool):
        primary = f"{chapter.index + 1:03d} · {_truncate(chapter.title or '(untitled)')}"
        secondary = "current" if current else ""
        super().__init__(
            Label(primary),
            Label(secondary, classes="secondary"),
        )
        self.chapter_index = chapter.index


class ChapterModal(ModalScreen[int | None]):
    """Table of contents — jump to any chapter (English chrome only)."""

    CSS = """
    #toc-shell {
        width: 1fr;
        height: 1fr;
        align: center middle;
        background: #0d1117 80%;
    }
    #toc-box {
        width: 74;
        height: 18;
        background: #161b22;
        border: round #30363d;
        padding: 0 1;
    }
    #toc-title { height: 1; color: #8b949e; }
    #toc-list { height: 1fr; }
    .secondary { color: #6e7681; }
    #toc-hint { height: 1; color: #8b949e; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "close"),
        Binding("q", "cancel", "cancel"),
    ]

    def __init__(self, chapters: list[Chapter], current_index: int = 0):
        super().__init__()
        self._chapters = chapters
        if chapters:
            self._current_index = max(0, min(current_index, len(chapters) - 1))
        else:
            self._current_index = 0
        self._list: ListView | None = None

    def compose(self):
        items = [
            _ChapterItem(c, c.index == self._current_index) for c in self._chapters
        ]
        with Vertical(id="toc-shell"):
            with Vertical(id="toc-box"):
                yield Static("table of contents", id="toc-title")
                self._list = ListView(*items, id="toc-list")
                yield self._list
                yield Static(
                    "arrow keys select · enter jump · esc cancel",
                    id="toc-hint",
                )

    def on_mount(self) -> None:
        """Highlight and center the current chapter, not the first one."""
        if self._list is None or not self._list.children:
            return
        self._list.index = self._current_index
        target = self._list.children[self._current_index]
        # after refresh: sizes are final only once the first layout ran
        self.call_after_refresh(
            self._list.scroll_to_center, target, False  # animate=False
        )

    def action_cancel(self) -> None:
        self.dismiss(None)

    def on_list_view_selected(self, event) -> None:
        item: _ChapterItem = event.item
        self.dismiss(item.chapter_index)