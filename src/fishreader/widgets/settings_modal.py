"""Settings modal: live-tweak reader & disguise options from the terminal.

Rows are supplied by the app: (section, key, label, options, value_labels).
Arrow keys select a row, left/right cycle its value, and every change is
applied instantly through the on_change callback (which also persists it to
fish.toml and re-renders).
"""

from __future__ import annotations

from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static

Row = tuple[str, str, str, list, dict]  # (section, key, label, options, value_labels)


class _SettingItem(ListItem):
    def __init__(self, label: str, value_text: str):
        self._label_text = label
        self.value_label = Label(self._compose_text(value_text))
        super().__init__(self.value_label)

    def _compose_text(self, value_text: str) -> str:
        return f"{self._label_text:<20}[#e3b341]{value_text}[/]"

    def set_value(self, text: str) -> None:
        self.value_label.update(self._compose_text(text))


class SettingsModal(ModalScreen[None]):
    """Disguised as a developer-settings popup; English chrome only."""

    CSS = """
    #settings-shell {
        width: 1fr;
        height: 1fr;
        align: center middle;
        background: #0d1117 80%;
    }
    #settings-box {
        width: 44;
        height: 12;
        background: #161b22;
        border: round #30363d;
        padding: 0 1;
    }
    #settings-title { height: 1; color: #8b949e; }
    #settings-list { height: 1fr; }
    #settings-list > .list-item { height: 1; }
    #settings-hint { height: 1; color: #8b949e; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "close"),
        Binding("q", "cancel", "cancel"),
        Binding("left", "prev_value", "previous value"),
        Binding("right", "next_value", "next value"),
    ]

    def __init__(
        self,
        rows: list[Row],
        values: dict[tuple[str, str], object],
        on_change,
    ):
        super().__init__()
        self._rows = rows
        self._values = dict(values)
        self._on_change = on_change
        self._list: ListView | None = None

    def _display(self, row: Row, value: object) -> str:
        _section, _key, _label, _options, value_labels = row
        return value_labels.get(value, str(value))

    def compose(self):
        with Vertical(id="settings-shell"):
            with Vertical(id="settings-box"):
                yield Static("settings", id="settings-title")
                items: list[_SettingItem] = []
                for row in self._rows:
                    section, key, _label, _options, _labels = row
                    current = self._values.get((section, key))
                    items.append(_SettingItem(row[2], self._display(row, current)))
                self._list = ListView(*items, id="settings-list")
                yield self._list
                yield Static(
                    "arrows select · ←/→ change · esc close (saved to fish.toml)",
                    id="settings-hint",
                )

    def _cycle(self, direction: int) -> None:
        if self._list is None or self._list.index is None:
            return
        idx = self._list.index
        row = self._rows[idx]
        section, key, _label, options, _labels = row
        current = self._values.get((section, key))
        try:
            pos = options.index(current)
        except ValueError:
            pos = 0  # current value not in the cycle (e.g. hand-edited) -> restart
        new_value = options[(pos + direction) % len(options)]
        if new_value == current:
            return
        self._values[(section, key)] = new_value
        item = self._list.children[idx]
        item.set_value(self._display(row, new_value))
        self._on_change(section, key, new_value)

    def action_next_value(self) -> None:
        self._cycle(+1)

    def action_prev_value(self) -> None:
        self._cycle(-1)

    def action_cancel(self) -> None:
        self.dismiss(None)
