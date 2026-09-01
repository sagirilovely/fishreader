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
        """Append one entry; the [LEVEL] tag is colored when theme allows."""
        if timestamped:
            ts = datetime.now().strftime("%H:%M:%S")
            line = f"{ts} [{label}] {text}"
        else:
            line = text  # feed lines already carry "HH:MM:SS [LEVEL] ..."

        if self.color_levels:
            tag, _, body = line.partition("]")
            rendered = Text()
            if body:
                rendered.append(tag + "]", style=_LABEL_STYLE.get(label, "dim"))
                rendered.append(body)
            else:
                rendered.append(line)
        else:
            rendered = Text(line)
        self.write(rendered)
        self.entry_count += 1