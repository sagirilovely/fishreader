"""Main agent-log widget: auto-scrolling fake English feed."""

from __future__ import annotations

import random
from datetime import datetime

from rich.text import Text
from textual.timer import Timer
from textual.widgets import RichLog

from fishreader.fakefeed import FakeFeed

_LABEL_STYLE = {
    "INFO": "dim #8b949e",
    "WARN": "bold yellow",
    "OK": "bold green",
}


def _append_with_code_highlights(
    t: Text, text: str, default_style: str = "#e2e8f0", code_style: str = "bold #fbbf24"
) -> None:
    parts = text.split("`")
    for i, part in enumerate(parts):
        if not part:
            continue
        if i % 2 == 1:
            t.append(f"`{part}`", style=code_style)
        else:
            t.append(part, style=default_style)


class AgentLog(RichLog):
    """Scrolling log pane fed by a FakeFeed on a randomized schedule."""

    def __init__(
        self,
        feed: FakeFeed | None = None,
        min_interval: float = 0.8,
        max_interval: float = 1.5,
        color_levels: bool = True,
        **kwargs,
    ):
        super().__init__(highlight=False, markup=False, wrap=True, **kwargs)
        self._feed = feed or FakeFeed()
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.color_levels = color_levels
        self._timer: Timer | None = None
        self._rng = random.Random()
        self.entry_count = 0  # lines written, for tests/status

    @property
    def feed(self) -> FakeFeed:
        return self._feed

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> None:
        """Begin the randomized feed loop."""
        self.stop()
        self._schedule()

    def stop(self) -> None:
        if self._timer is not None:
            try:
                self._timer.stop()
            except Exception:
                pass
            self._timer = None

    def set_interval(self, min_interval: float, max_interval: float) -> None:
        self.min_interval = float(min_interval)
        self.max_interval = float(max_interval)

    # -- internals ------------------------------------------------------------

    def _schedule(self) -> None:
        delay = self._rng.uniform(self.min_interval, self.max_interval)
        self._timer = self.set_timer(delay, self._tick)

    def _tick(self) -> None:
        self._timer = None
        for label, line in self._feed.next():
            self.write_line(label, line, timestamped=False)
        self._schedule()

    def write_line(self, label: str, text: str, timestamped: bool = True) -> None:
        """Append one entry; the [LEVEL] tag or Agent badge is colored when theme allows."""
        if timestamped:
            ts = datetime.now().strftime("%H:%M:%S")
            line = f"{ts} [{label}] {text}"
        else:
            line = text

        if self.color_levels:
            rendered = Text()
            if line.startswith("Think: ") or line.startswith("Think · "):
                body = line.split(": ", 1)[1] if ": " in line else line.split(" · ", 1)[1]
                rendered.append("⚙ Think", style="bold #a78bfa")
                rendered.append(" · ", style="dim #6b7280")
                _append_with_code_highlights(rendered, body, default_style="#e2e8f0", code_style="bold #fbbf24")
            elif line.startswith("Bash: ") or line.startswith("Bash · "):
                body = line.split(": ", 1)[1] if ": " in line else line.split(" · ", 1)[1]
                rendered.append(">_ Bash", style="bold #34d399")
                rendered.append(" · ", style="dim #6b7280")
                _append_with_code_highlights(rendered, body, default_style="#f1f5f9", code_style="bold #38bdf8")
            elif line.startswith("Result: ") or line.startswith("Result · "):
                body = line.split(": ", 1)[1] if ": " in line else line.split(" · ", 1)[1]
                rendered.append("✓ Result", style="bold #10b981")
                rendered.append(" · ", style="dim #6b7280")
                rendered.append(body, style="#a7f3d0")
            elif line.startswith("View: ") or line.startswith("View · "):
                body = line.split(": ", 1)[1] if ": " in line else line.split(" · ", 1)[1]
                rendered.append("👁 View", style="bold #60a5fa")
                rendered.append(" · ", style="dim #6b7280")
                rendered.append(body, style="#cbd5e1")
            elif line.startswith("Edit: ") or line.startswith("Edit · "):
                body = line.split(": ", 1)[1] if ": " in line else line.split(" · ", 1)[1]
                rendered.append("✏ Edit", style="bold #fbbf24")
                rendered.append(" · ", style="dim #6b7280")
                rendered.append(body, style="#cbd5e1")
            elif "]" in line and "[" in line:
                tag, _, body = line.partition("]")
                rendered.append(tag + "]", style=_LABEL_STYLE.get(label, "dim"))
                rendered.append(body)
            else:
                rendered.append(line)
        else:
            rendered = Text(line)
        self.write(rendered)
        self.entry_count += 1