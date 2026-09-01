"""fishreader Textual application: layout, key bindings, reading state.

Phase M1: basic layout + pagination + progress resume (TXT only).
The fake AgentLog feed and boss mode arrive in later phases.
"""

from __future__ import annotations

import random
from bisect import bisect_right
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Static

from fishreader.config import (
    FONT_SIZES,
    LOG_STYLES,
    NOVEL_STYLES,
    READER_POSITIONS,
    Config,
    apply_toml_update,
)
from fishreader.fakefeed import FakeFeed
from fishreader.library import Candidate, load_book, scan_library
from fishreader.models import Book
from fishreader.state import ProgressStore
from fishreader.textlayout import Page, wrap_text_with_offsets
from fishreader.widgets.agent_log import AgentLog
from fishreader.widgets.chapter_modal import ChapterModal
from fishreader.widgets.library_modal import LibraryModal
from fishreader.widgets.reader_pane import FONT_WIDTH_BASIS, ReaderPane
from fishreader.widgets.settings_modal import Row, SettingsModal

MIN_TERMINAL_WIDTH = 40
MIN_TERMINAL_HEIGHT = 12


class FishApp(App[None]):
    """A terminal novel reader disguised as a coding agent."""

    TITLE = "fishreader"
    CSS = ""  # built dynamically in __init__

    BINDINGS = [
        Binding("right,space,pagedown", "next_page", "next page"),
        Binding("left,pageup", "prev_page", "prev page"),
        Binding("up", "scroll_up", "scroll up one line"),
        Binding("down", "scroll_down", "scroll down one line"),
        Binding("n", "next_chapter", "next chapter"),
        Binding("p", "prev_chapter", "prev chapter"),
        Binding("t", "toggle_chapters", "table of contents"),
        Binding("l", "toggle_library", "open recent files"),
        Binding("s", "toggle_settings", "settings"),
        Binding("q", "quit", "quit"),
        Binding("ctrl+q", "quit", "quit"),
    ]

    def __init__(self, config: Config, project_root: Path):
        super().__init__()
        self.config = config
        self.root = project_root
        self.session_id = random.randint(1000, 9999)
        self._boss_mode = False
        # Boss key is configurable; priority=True so it fires even while
        # a modal screen (e.g. the library picker) is open.
        self._bindings.bind(
            config.boss_key,
            "toggle_boss_mode",
            description="boss mode",
            priority=True,
        )

        # State must exist before on_mount: Textual dispatches Resize
        # *before* Mount, and on_resize touches these.
        self.current: Book | None = None
        self.chapter_index = 0
        self.line_index = 0
        self._linecache: dict[tuple, list[tuple[str, int]]] = {}
        self.candidates: list[Candidate] = []
        self.valid_ids: set[str] = set()
        self.progress: ProgressStore | None = None
        self.reader_cols = 30
        self.wrap_width = 28
        self._line_spacing = 0
        self._paragraph_spacing = 0
        self._term_height = 30

        width_css = config.raw["reader"]["reader_width"]
        css_width = width_css if isinstance(width_css, str) else f"{int(width_css)}"
        accent = config.theme.get("accent", "green")
        reader_color = config.theme.get("reader_color", "gray")
        self.CSS = f"""
        Screen {{ background: #0d1117; }}
        #titlebar {{ dock: top; height: 1; background: #161b22; color: #8b949e; }}
        #statusbar {{ dock: bottom; height: 1; background: #161b22; color: #8b949e; }}
        #main {{ layout: horizontal; height: 1fr; }}
        #agent-log {{
            width: 1fr;
            height: 100%;
            background: #0d1117;
            border-right: solid #21262d;
            color: #8b949e;
        }}
        #reader-col {{
            width: {css_width};
            height: 100%;
            background: #12151c;
            overflow-y: hidden;
        }}
        #reader-col.boss-hidden {{ display: none; }}
        #reader-col.narrow-hidden {{ display: none; }}
        #main.pos-vertical {{ layout: vertical; }}
        #main.pos-vertical #agent-log {{
            height: 1fr;
            border-right: none;
            border-top: solid #21262d;
        }}
        #reader-col.pos-bottom {{
            width: 100%;
            height: 30%;
        }}
        #reader-header {{
            height: 1;
            background: #12151c;
            color: {reader_color};
            padding: 0 1;
        }}
        #reader-pane {{
            width: 1fr;
            height: 1fr;
            color: {reader_color};
            overflow-y: hidden;
            padding: 0 1;
        }}
        #tiny-screen {{
            display: none;
            height: 1fr;
            content-align: center middle;
            color: #e3b341;
            background: #0d1117;
        }}
        .accent {{ color: {accent}; }}
        """

    # -- lifecycle ----------------------------------------------------------

    def compose(self) -> ComposeResult:
        # markup=False: status/title bars contain [b]oss-style hints which
        # rich markup would otherwise swallow.
        yield Static(id="titlebar", markup=False)
        with Horizontal(id="main"):
            yield AgentLog(
                id="agent-log",
                feed=FakeFeed(),
                min_interval=self.config.disguise["log_interval_min"],
                max_interval=self.config.disguise["log_interval_max"],
                color_levels=self.config.theme["log_level_color"],
            )
            with Vertical(id="reader-col"):
                yield Static("reading_notes.md", id="reader-header", markup=False)
                yield ReaderPane(id="reader-pane")
        yield Static(id="statusbar", markup=False)
        yield Static(id="tiny-screen", markup=False)

    def on_mount(self) -> None:
        w, h = self.size.width, self.size.height
        if w < MIN_TERMINAL_WIDTH or h < MIN_TERMINAL_HEIGHT:
            self._show_tiny_screen()
            return

        self._update_titlebar()
        self._geometry_changed()
        self._apply_reader_position()

        # book discovery
        self.candidates = scan_library(self.config)
        self.valid_ids = {c.id for c in self.candidates}
        self.progress = ProgressStore(self.config.progress_path()).load()
        self.progress.drop_stale(self.valid_ids)

        log = self.query_one("#agent-log", AgentLog)
        self._agent_log = log
        log.write_line("INFO", "workspace initialized")
        log.write_line("INFO", f"scanning {len(self.candidates)} candidate file(s)")
        if not self.candidates:
            log.write_line("OK", "no books yet - drop files into books/ and restart")
            self.query_one("#reader-pane", ReaderPane).show_empty(
                "no books found\n\nput .txt / .epub / .mobi files into\nbooks/ and restart"
            )
            self._update_statusbar()
            return
        if self.config.disguise["log_style"] == "agent":
            log.write_line("OK", "reader ready - arrow keys flip pages")
        log.start()

        # resume last book; first run shows the library picker (M2)
        to_open: str | None = None
        if self.config.reader.get("resume_last", True):
            to_open = self.progress.last_book_id()
        if to_open is not None and to_open in self.valid_ids:
            self.open_book(to_open)
        else:
            log.write("[ok] no resume target — press [l] for recent files")
            self.action_toggle_library()
        self._update_statusbar()

    def on_resize(self, event) -> None:
        # text layout must use the *event* size: App._size is only refreshed
        # after this handler runs.
        w, h = event.size.width, event.size.height
        self._geometry_changed(w, h)
        if self.current is not None:
            self._render(h=h)
        # Narrow terminals: hide the reader column instead of breaking the
        # layout (dev doc 9.2); restore it once there is room again.
        narrow = w < 60
        self.query_one("#reader-col", Vertical).set_class(narrow, "narrow-hidden")

    def on_unmount(self) -> None:
        agent_log = getattr(self, "_agent_log", None)
        if agent_log is not None:
            agent_log.stop()
        self._save_progress()

    # -- geometry ------------------------------------------------------------

    def _geometry_changed(self, term_w: int | None = None, term_h: int | None = None) -> None:
        term_w = term_w or self.size.width
        term_h = term_h or self.size.height
        term_w = max(term_w, MIN_TERMINAL_WIDTH)
        if self.config.reader["reader_position"] == "bottom":
            # bottom pane spans the full terminal width (1fr + padding)
            self.reader_cols = max(8, term_w - 2)
        else:
            self.reader_cols = self.config.reader_width_columns(term_w)
        basis = FONT_WIDTH_BASIS.get(self.config.reader["font_size"], 2)
        self.wrap_width = max(4, self.reader_cols - basis)
        self._line_spacing, self._paragraph_spacing = self.config.effective_spacing()
        self._term_height = term_h
        # clear wrap cache: geometry changed
        self._linecache = {}

    def _apply_reader_position(self) -> None:
        """Swap the reader pane between left/right/bottom placements."""
        pos = self.config.reader["reader_position"]
        main = self.query_one("#main", Horizontal)
        col = self.query_one("#reader-col", Vertical)
        log = self.query_one("#agent-log", AgentLog)
        main.set_class(pos == "bottom", "pos-vertical")
        col.set_class(pos == "bottom", "pos-bottom")
        if pos == "left":
            if main.children[0] is not col:
                main.move_child(col, before=log)
        elif pos == "right":
            if main.children[0] is col:
                main.move_child(col, after=log)

    def _visible_lines(self, height: int | None = None) -> int:
        h = max(1, (height or self._term_height or self.size.height) - 2)
        if self.config.reader["reader_position"] == "bottom":
            # #reader-col is 30% of the main area, minus the 1-line header
            h = max(1, int(h * 0.30) - 1)
        return max(1, h // (1 + self._line_spacing))

    # -- chapter wrap cache ----------------------------------------------------

    def _chapter_lines(self, book: Book, ci: int, width: int) -> list[tuple[str, int]]:
        key = (book.id, ci, width)
        cached = self._linecache.get(key)
        if cached is not None:
            return cached
        ch = book.chapters[ci]
        wrapped = wrap_text_with_offsets(
            book.full_text[ch.start_char : ch.end_char], width
        )
        lines = [(ln, ch.start_char + rel) for ln, rel in wrapped]
        if len(self._linecache) > 64:  # bound memory on huge multi-chapter books
            self._linecache.clear()
        self._linecache[key] = lines
        return lines

    def _progress_to_view(self, book: Book, entry: dict | None) -> None:
        """Set chapter_index / line_index from a progress entry.

        char_offset is the authoritative position (survives resizes and
        inconsistent chapter_index); scroll_line is only a fallback when no
        char offset was saved.
        """
        if entry is None:
            self.chapter_index = 0
            self.line_index = 0
            return
        offset = int(entry.get("char_offset", 0)) or 0
        if offset > 0:
            ci = book.chapter_index_at(offset)
        else:
            ci = min(
                max(0, int(entry.get("chapter_index", 0))),
                max(0, len(book.chapters) - 1),
            )
        self.chapter_index = ci
        if not book.chapters:
            self.line_index = 0
            return
        lines = self._chapter_lines(book, ci, self.wrap_width)
        if offset > 0 and lines:
            offsets = [off for _, off in lines]
            self.line_index = max(0, bisect_right(offsets, offset) - 1)
        elif lines:
            self.line_index = min(
                max(0, int(entry.get("scroll_line", 0))), len(lines) - 1
            )
        else:
            self.line_index = 0
        self.line_index = min(self.line_index, len(lines) - 1)

    # -- books -----------------------------------------------------------------

    def open_book(self, book_id: str) -> None:
        cand = next((c for c in self.candidates if c.id == book_id), None)
        if cand is None:
            self.query_one("#reader-pane", ReaderPane).show_empty("book not found")
            return
        book = load_book(cand, self.config)
        self.current = book
        if not book.readable:
            self.query_one("#reader-pane", ReaderPane).show_empty(
                f"[unsupported] {book.reason or 'unknown error'}"
            )
            self.notify(f"{book.id}: {book.reason}", severity="error", timeout=5)
            self._update_statusbar()
            return
        self.progress.set_last_book(book.id)
        self._progress_to_view(book, self.progress.get(book.id))
        self._render()

    # -- rendering ---------------------------------------------------------------

    def _render(self, h: int | None = None) -> None:
        book = self.current
        pane = self.query_one("#reader-pane", ReaderPane)
        if book is None or not book.readable:
            return
        lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
        if not lines:
            pane.set_page(Page([], 0, 0, self.chapter_index, eof=True))
            self._update_statusbar()
            return
        visible = self._visible_lines(h)
        self.line_index = min(self.line_index, len(lines) - 1)
        start = self.line_index
        page_lines = lines[start : start + visible]
        eof = self.chapter_index == len(book.chapters) - 1 and start + visible >= len(lines)
        first_offset = page_lines[0][1] if page_lines else lines[0][1]
        page = Page(
            lines=[ln for ln, _ in page_lines],
            first_char_offset=first_offset,
            next_page_start=first_offset,
            chapter_index=self.chapter_index,
            eof=eof,
            total_lines=len(lines),
        )
        pane.set_page(
            page,
            novel_style=self.config.novel_style,
            line_spacing=self._line_spacing,
            paragraph_spacing=self._paragraph_spacing,
        )
        if self.config.autosave_on_page():
            self._save_progress()
        self._update_statusbar()

    # -- bars -------------------------------------------------------------------

    def _update_titlebar(self) -> None:
        d = self.config.disguise
        state = "[boss]" if self._boss_mode else "[running]"
        self.query_one("#titlebar", Static).update(
            f"\u25cf {d['agent_name']} v{d['agent_version']} "
            f"\u2014 session #{self.session_id:04d}    {state}"
        )

    def _update_statusbar(self) -> None:
        sb = self.query_one("#statusbar", Static)
        boss_key = self.config.boss_key
        if self._boss_mode:
            sb.update(f"boss mode active  [{boss_key}]ack  [q]uit")
            return
        if self.current is None or not self.current.readable:
            sb.update(f"[{boss_key}]oss  [t]oc  [l]ibrary  [s]ettings  [q]uit     no book loaded")
            return
        book = self.current
        lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
        offset = lines[min(self.line_index, len(lines) - 1)][1] if lines else 0
        pct = (offset / book.total_chars * 100.0) if book.total_chars else 0.0
        if self.config.disguise.get("status_line") == "full":
            hint = (
                f"[{boss_key}]oss  [\u2190/\u2192]page  [\u2191/\u2193]line  "
                f"[n/p]chap  [t]oc  [l]ibrary  [s]ettings  [q]uit"
            )
        else:
            hint = f"[{boss_key}]oss  [t]oc  [l]ibrary  [s]ettings  [q]uit"
        sb.update(f"buff {pct:.1f}% | scroll {min(self.line_index+1, len(lines))}/{len(lines)} | {hint}")

    # -- actions -------------------------------------------------------------------

    def action_next_page(self) -> None:
        if self.current is None or not self.current.readable:
            return
        book = self.current
        lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
        visible = self._visible_lines()
        if self.line_index + visible < len(lines):
            self.line_index += visible
        elif self.chapter_index + 1 < len(book.chapters):
            self.chapter_index += 1
            self.line_index = 0
        else:
            self.line_index = max(0, len(lines) - 1)
        self._render()

    def action_prev_page(self) -> None:
        if self.current is None or not self.current.readable:
            return
        book = self.current
        visible = self._visible_lines()
        if self.line_index - visible >= 0:
            self.line_index -= visible
        elif self.chapter_index > 0:
            self.chapter_index -= 1
            lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
            self.line_index = max(0, len(lines) - visible)
        else:
            self.line_index = 0
        self._render()

    def action_scroll_up(self) -> None:
        if self.current is None or not self.current.readable:
            return
        self.line_index = max(0, self.line_index - 1)
        self._render()

    def action_scroll_down(self) -> None:
        if self.current is None or not self.current.readable:
            return
        book = self.current
        lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
        if self.line_index + 1 < len(lines):
            self.line_index += 1
        elif self.chapter_index + 1 < len(book.chapters):
            self.chapter_index += 1
            self.line_index = 0
        self._render()

    def action_next_chapter(self) -> None:
        if self.current is None or not self.current.readable:
            return
        if self.chapter_index + 1 < len(self.current.chapters):
            self.chapter_index += 1
            self.line_index = 0
            self._render()

    def action_prev_chapter(self) -> None:
        if self.current is None or not self.current.readable:
            return
        if self.chapter_index > 0:
            self.chapter_index -= 1
            self.line_index = 0
            self._render()

    def action_toggle_library(self) -> None:
        if isinstance(self.screen, ModalScreen):
            return  # one picker at a time
        if not self.candidates:
            self.notify("no books in the library yet", severity="warning")
            return
        self.push_screen(
            LibraryModal(
                self.candidates,
                current_id=self.current.id if self.current is not None else None,
            ),
            callback=self._on_library_result,
        )

    def action_toggle_chapters(self) -> None:
        """Table of contents: jump to any chapter of the current book."""
        if isinstance(self.screen, ModalScreen):
            return  # one picker at a time
        if self.current is None or not self.current.readable:
            return
        self.push_screen(
            ChapterModal(self.current.chapters, self.chapter_index),
            callback=self._on_toc_result,
        )

    def _on_toc_result(self, chapter_index: int | None) -> None:
        if chapter_index is None:
            return
        self.chapter_index = chapter_index
        self.line_index = 0
        self._render()

    # -- settings ------------------------------------------------------------------

    def action_toggle_settings(self) -> None:
        """Theme/settings popup: font, layout, spacing, log style."""
        if isinstance(self.screen, ModalScreen):
            return  # one popup at a time
        self.push_screen(
            SettingsModal(
                self._setting_rows(),
                self._setting_values(),
                self._apply_setting,
            )
        )

    def _setting_rows(self) -> list[Row]:
        spacing_labels = {0: "auto"}
        return [
            ("reader", "font_size", "font size", list(FONT_SIZES), {}),
            ("reader", "reader_position", "reader position", list(READER_POSITIONS), {}),
            ("reader", "reader_width", "reader width", ["25%", "30%", "35%", "40%"], {}),
            ("reader", "line_spacing", "line spacing", [0, 1, 2], spacing_labels),
            ("reader", "paragraph_spacing", "paragraph spacing", [0, 1, 2], spacing_labels),
            ("reader", "novel_style", "novel style", list(NOVEL_STYLES), {}),
            ("disguise", "log_style", "log style", list(LOG_STYLES), {}),
        ]

    def _setting_values(self) -> dict[tuple[str, str], object]:
        values: dict[tuple[str, str], object] = {}
        for row in self._setting_rows():
            section, key, *_ = row
            values[(section, key)] = self.config.raw[section][key]
        return values

    def _apply_setting(self, section: str, key: str, value: object) -> None:
        """Apply one setting change: runtime effect + persist to fish.toml."""
        self.config.raw[section][key] = value
        try:
            apply_toml_update(self.config.path, section, {key: value})
        except ConfigError as exc:
            self.notify(
                f"could not persist settings ({exc}) - change lasts this session",
                severity="warning",
                timeout=8,
            )

        if section == "disguise" and key == "log_style":
            log = getattr(self, "_agent_log", None)
            if log is not None:
                log.feed.set_style(str(value))
            return

        if key == "reader_position":
            self._apply_reader_position()
        self._geometry_changed()
        if self.current is not None and self.current.readable:
            self._render()
        self._update_statusbar()

    def action_toggle_boss_mode(self) -> None:
        """Boss key: hide the reading pane, drop any open popup, English only."""
        self._boss_mode = not self._boss_mode
        self.query_one("#reader-col", Vertical).set_class(
            self._boss_mode, "boss-hidden"
        )
        if self._boss_mode and isinstance(self.screen, ModalScreen):
            self.screen.dismiss(None)
        self._update_titlebar()
        self._update_statusbar()
        if not self._boss_mode and self.current is not None:
            self._render()

    def _on_library_result(self, book_id: str | None) -> None:
        if book_id:
            self.open_book(book_id)

    def action_quit(self) -> None:
        self._save_progress()
        self.exit()

    # -- cleanup ------------------------------------------------------------------

    def _save_progress(self) -> None:
        if self.progress is None:
            return
        current = getattr(self, "current", None)
        if current is not None and current.readable:
            book = current
            lines = self._chapter_lines(book, self.chapter_index, self.wrap_width)
            offset = lines[min(self.line_index, len(lines) - 1)][1] if lines else 0
            self.progress.update_book(
                book.id, self.chapter_index, offset, self.line_index
            )
            self.progress.set_last_book(book.id)
        self.progress.save()

    def _show_tiny_screen(self) -> None:
        self.query_one("#main", Horizontal).display = False
        msg = self.query_one("#tiny-screen", Static)
        msg.display = True
        msg.update(
            "terminal too small\n\n"
            f"need at least {MIN_TERMINAL_WIDTH} columns and {MIN_TERMINAL_HEIGHT} rows\n"
            f"(current: {self.size.width}x{self.size.height})\n\n"
            "enlarge the window to start reading"
        )
        self.query_one("#statusbar", Static).update("resize the terminal, then restart")
        self.set_interval(3.0, self.exit)