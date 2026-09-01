"""Claude Code animated mascot and fake runtime status widget for Terminal Boss Mode."""

from __future__ import annotations

from pathlib import Path
from rich.text import Text
from textual.timer import Timer
from textual.widgets import Static

CORAL_COLOR = "bold #d97768"

# 8 Animation frames for Claude Robot Mascot
MASCOT_FRAMES = [
    # Frame 0: Neutral Idle (Eyes Open)
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │█│ │ │█│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
    # Frame 1: Neutral Idle (Slight Pause)
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │█│ │ │█│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
    # Frame 2: Blinking Eyes
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │─│ │ │─│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
    # Frame 3: Step Left / Glance Left
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │█│ │ │█│ │ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "   / /        │ │    ",
    ],
    # Frame 4: Neutral Return
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │█│ │ │█│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
    # Frame 5: Step Right / Glance Right
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │ │█│ │ │█│    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │        \\ \\   ",
    ],
    # Frame 6: Happy Eyes (^ ^)
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │^│ │ │^│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
    # Frame 7: Bounce / Shrug
    [
        "    ┌─┬─┬─┬─┬─┬─┐    ",
        "    │ │•│ │ │•│ │    ",
        "  ┌─┴─┼─┼─┼─┼─┼─┴─┐  ",
        "  │ │ │ │ │ │ │ │ │  ",
        "  └─┬─┴─┴─┴─┴─┴─┬─┘  ",
        "    │ │       │ │    ",
    ],
]


class ClaudeRobotPane(Static):
    """Animated Claude Code Mascot and Runtime Status Pane for Boss Mode."""

    def __init__(
        self,
        project_root: Path | str | None = None,
        id: str = "claude-pane",
        **kwargs,
    ):
        super().__init__(id=id, **kwargs)
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # Formulate compact display path (e.g. ~/Desktop/fish)
        home = str(Path.home())
        raw_path = str(self.project_root.resolve())
        if raw_path.startswith(home):
            self.display_path = "~" + raw_path[len(home):]
        else:
            self.display_path = raw_path

        self._frame_idx = 0
        self._timer: Timer | None = None
        self._tokens = 42800
        self._cost = 0.048
        self._uptime_seconds = 840

    def on_mount(self) -> None:
        self._render_frame()

    def start_animation(self) -> None:
        """Start the mascot animation timer."""
        self.stop_animation()
        self._render_frame()
        self._timer = self.set_interval(0.6, self._tick)

    def stop_animation(self) -> None:
        """Stop the mascot animation timer."""
        if self._timer is not None:
            try:
                self._timer.stop()
            except Exception:
                pass
            self._timer = None

    def _tick(self) -> None:
        self._frame_idx = (self._frame_idx + 1) % len(MASCOT_FRAMES)
        self._tokens += 120
        self._cost += 0.0003
        self._uptime_seconds += 1
        self._render_frame()

    def on_resize(self) -> None:
        self._render_frame()

    def _render_frame(self) -> None:
        width = max(self.size.width, 24)
        frame = MASCOT_FRAMES[self._frame_idx]
        t = Text()

        # Check if we have enough width for side-by-side (>= 48)
        if width >= 48:
            side_info = [
                [("Claude Code ", "bold #f8fafc"), ("v2.1.132", "#94a3b8")],
                [("claude-opus-4-8 · API Usage Billing", "#94a3b8")],
                [(self.display_path, "#64748b")],
                [("⚡ Status: Agent Loop Active", "#34d399")],
                [(f"📊 Context: {self._tokens/1000:.1f}k / 200k ({(self._tokens/200000)*100:.1f}%)", "#cbd5e1")],
                [(f"💰 Session Cost: ${self._cost:.3f}", "#fbbf24")],
            ]
            t.append("\n")
            for i in range(max(len(frame), len(side_info))):
                f_line = frame[i] if i < len(frame) else " " * 21
                t.append(f_line + "  ", style=CORAL_COLOR)
                if i < len(side_info):
                    for chunk, st in side_info[i]:
                        t.append(chunk, style=st)
                t.append("\n")
            t.append("\n")
            t.append("  💡 Tools: Bash · View · Edit · Grep · Glob\n", style="dim #64748b")
            t.append(f"  ⏱️  Uptime: {self._uptime_seconds // 3600:02d}:{(self._uptime_seconds % 3600) // 60:02d}:{self._uptime_seconds % 60:02d}\n", style="dim #64748b")
        else:
            # Stacked vertical layout
            t.append("\n")
            for line in frame:
                t.append(line.center(width) + "\n", style=CORAL_COLOR)
            t.append("\n")

            # Title
            t.append("Claude Code ".center(max(width // 2, 12)), style="bold #f8fafc")
            t.append("v2.1.132\n", style="#94a3b8")
            t.append("claude-opus-4-8 · API Usage Billing\n".center(width), style="#94a3b8")
            t.append(f"{self.display_path}\n".center(width), style="#64748b")
            t.append("\n")
            t.append("  ⚡ Status: Agent Loop Active\n", style="#34d399")
            t.append(f"  📊 Context: {self._tokens/1000:.1f}k / 200k ({(self._tokens/200000)*100:.1f}%)\n", style="#cbd5e1")
            t.append(f"  💰 Session Cost: ${self._cost:.3f}\n", style="#fbbf24")
            t.append(f"  ⏱️  Uptime: {self._uptime_seconds // 3600:02d}:{(self._uptime_seconds % 3600) // 60:02d}:{self._uptime_seconds % 60:02d}\n", style="dim #64748b")

        self._current_text = t
        try:
            self.update(t)
        except Exception:
            pass
