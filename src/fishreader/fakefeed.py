"""Fake English log feed with selectable tool styles.

Template + slot randomization keeps the feed varied and ASCII-only, with a
recent-template guard against short-term repeats. Each style imitates a
different tool so a backend, frontend or infra dev can pick a plausible one:

- agent:  DeepSeek / Claude Code agentic coding loop (Think / Bash / View / Edit / Result)
- vite:   vite dev server / build output
- npm:    npm install / scripts output
- git:    terminal git sessions

Used by widgets/agent_log.
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime
from pathlib import Path

MAX_LINE_WIDTH = 120

LOG_STYLES = ("agent", "vite", "npm", "git")

_MODULES = [
    "app", "parser", "config", "state", "textlayout", "fakefeed",
    "server", "real_docs", "formatter", "library", "models",
]
_FUNCS = [
    "validate_config", "extract_chapter", "render_page", "normalize_spacing",
    "flush_progress", "handle_boss_key", "parse_stream", "compute_wrap",
    "tokenize_code", "dispatch_action", "resolve_book", "check_resize",
]
_TESTS = [
    "test_app_smoke", "test_txt_parser", "test_epub_parser",
    "test_textlayout", "test_web_server", "test_web_video",
]
_PATHS = [
    "src/fishreader/app.py", "src/fishreader/config.py", "src/fishreader/state.py",
    "src/fishreader/textlayout.py", "src/fishreader/fakefeed.py", "src/fishreader/web/server.py",
]
_NEEDLES = ["boss_key", "reader_width", "auto_pause_on_boss", "line_spacing", "wrap_width"]

# -- non-agent style pools ----------------------------------------------------

_FRONT_FILES = [
    "Header", "App", "main", "store", "api", "useSearch", "stats",
    "TodoList", "Navbar", "Chart", "theme", "auth",
]
_FRONT_EXT = ["vue", "ts", "tsx"]
_PKGS = [
    "chalk", "sass", "lodash", "rimraf", "tailwindcss", "eslint",
    "prettier", "postcss", "vue-router", "axios", "dayjs", "pinia",
]
_BRANCHES = ["main", "dev", "feature/web-player", "fix/boss-banner", "hotfix/parser", "release/v2.1"]

_STYLE_INTROS: dict[str, list[tuple[str, str]]] = {
    "vite": [
        ("OK", "VITE v5.4.7  ready in 312 ms"),
        ("INFO", "->  Local:   http://localhost:5173/"),
        ("INFO", "->  Network: http://192.168.1.8:5173/"),
    ],
    "npm": [
        ("INFO", "$ npm install"),
        ("OK", "added 42 packages in 3s"),
    ],
    "git": [
        ("INFO", "$ git pull --ff-only"),
        ("INFO", "Updating abc1234..def5678"),
        ("INFO", "Fast-forward"),
        ("INFO", " 1 file changed, 6 insertions(+), 6 deletions(-)"),
    ],
}

_VITE_KEYS = [
    "vite:modules", "vite:built", "vite:hmr", "vite:chunk",
    "vite:warnchunk", "vite:reload", "vite:dep", "vite:err",
]
_NPM_KEYS = [
    "npm:uptodate", "npm:added", "npm:deprecated", "npm:test",
    "npm:build", "npm:tsc", "npm:audit", "npm:removed",
]
_GIT_KEYS = [
    "git:status", "git:diff", "git:rebase", "git:rebase-done",
    "git:push", "git:deltas", "git:ahead", "git:log",
]


class FakeFeed:
    """Yields short English log entries that look like a tool at work."""

    def __init__(
        self,
        style: str = "agent",
        seed: int | None = None,
        project_root: Path | str | None = None,
    ):
        if style not in LOG_STYLES:
            raise ValueError(f"unknown log style {style!r}, expected one of {LOG_STYLES}")
        self.style = style
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._root_str = str(self.project_root.resolve()).replace("\\", "/")
        self._first_lines = list(_STYLE_INTROS.get(style, ()))
        self._rng = random.Random(seed)
        self._recent: deque[tuple] = deque(maxlen=12)   # template keys
        self._recent_lines: deque[str] = deque(maxlen=24)  # rendered lines
        self._step_queue: deque[tuple[str, str]] = deque()

    def set_style(self, style: str) -> None:
        """Switch style; the next burst announces the new tool."""
        if style not in LOG_STYLES:
            raise ValueError(f"unknown log style {style!r}, expected one of {LOG_STYLES}")
        if style != self.style:
            self.style = style
            self._first_lines = list(_STYLE_INTROS.get(style, ()))
            self._recent.clear()
            self._recent_lines.clear()
            self._step_queue.clear()

    # -- helpers ---------------------------------------------------------------

    def _pick(self, pool: list[str]) -> str:
        return self._rng.choice(pool)

    def _choose_key(self, keys: list[str]) -> str:
        key = self._rng.choice(keys)
        if key in self._recent:
            for _ in range(32):  # avoid repeating the same template recently
                key = self._rng.choice(keys)
                if key not in self._recent:
                    break
        self._recent.append(key)
        return key

    def _format(self, ts: str, label: str, text: str) -> str:
        if self.style == "agent":
            line = text
        else:
            line = f"{ts} [{label}] {text}"
        if len(line) > MAX_LINE_WIDTH:
            line = line[: MAX_LINE_WIDTH - 3] + "..."
        return line

    # -- agent episode generators (DeepSeek / Claude Code harness style) --------

    def _agent_episode_shell_debug(self) -> list[tuple[str, str]]:
        r = self._root_str
        return [
            ("INFO", "Think: So multiple `echo` commands in one shell call hang! Yet earlier simple `echo hi > run.py` works. This is suspicious."),
            ("INFO", f"Bash: cd {r} && ls -l zz.py 2>&1 || true"),
            ("WARN", "Think: So command didn't even create first file? It timed out before executing? Maybe the tool runner is blocking."),
            ("INFO", "Bash: echo ok"),
            ("INFO", "Think: Okay."),
            ("INFO", f"Bash: cd {r} && echo 'hello' > zz.py && cat zz.py"),
            ("INFO", "Think: So single statement works. Multiple statements separated by `&&` sometimes hang. Let's test python execution directly."),
            ("INFO", f"Bash: cd {r} && python3 -c \"from pathlib import Path; Path('zz.py').write_text('print(1)')\""),
            ("INFO", "Think: So `python3 -c` works. Multiple statements in python? Let's test write multiple files in one python -c."),
            ("INFO", f"Bash: cd {r} && python3 -c \"from pathlib import Path; [Path(f'zz{{i}}.py').write_text('x\\n') for i in range(3)]\""),
            ("OK", "Think: Great. So use Python `-c` with semicolons works reliably. Let's test writing the runner script now."),
            ("INFO", f"Bash: cd {r} && python3 -c \"from pathlib import Path; Path('run.py').write_text('#!/usr/bin/env python3\\n')\""),
            ("WARN", "Think: Writing to `run.py` via Python hangs. But writing to `zz.py` works. Something specific about `run.py` locking?"),
        ]

    def _agent_episode_ast_statusbar(self) -> list[tuple[str, str]]:
        r = self._root_str
        return [
            ("INFO", "Think: Let's inspect `src/fishreader/app.py` AST to see why the layout collapsed when terminal resized below 80 columns."),
            ("INFO", f"Bash: cd {r} && python3 -c \"import ast; ast.parse(open('src/fishreader/app.py').read())\""),
            ("INFO", "Think: Syntax is valid. Let's check `_update_statusbar` where `min(self.line_index, len(lines)-1)` is computed."),
            ("INFO", f"Bash: cd {r} && rg \"def _update_statusbar\" src/"),
            ("INFO", "Think: Found the issue: `_update_statusbar` was called before `lines` cache was initialized. Adding None-check guard."),
            ("INFO", f"Bash: cd {r} && git diff -U3 src/fishreader/app.py"),
            ("INFO", "Think: Let's run the smoke tests to verify the terminal resize and statusbar fix."),
            ("INFO", f"Bash: cd {r} && pytest tests/test_app_smoke.py -v"),
            ("OK", "Result: tests/test_app_smoke.py::test_boss_key PASSED [100%]"),
        ]

    def _agent_episode_parser_opt(self) -> list[tuple[str, str]]:
        r = self._root_str
        return [
            ("INFO", "Think: Measuring memory consumption and CPU profile during EPUB spine unpacking with BeautifulSoup."),
            ("INFO", f"Bash: cd {r} && python3 -m cProfile -s tottime scripts/bench_parser.py 2>&1 | head -n 15"),
            ("INFO", "Think: `BeautifulSoup.get_text()` accounts for 68% of parse time. We can optimize regex whitespace folding."),
            ("INFO", f"Bash: cd {r} && pytest tests/test_epub_parser.py tests/test_txt_parser.py -q"),
            ("OK", "Result: 18 passed in 0.24s (zero encoding warnings)"),
        ]

    def _agent_episode_video_stream(self) -> list[tuple[str, str]]:
        r = self._root_str
        return [
            ("INFO", "Think: Testing HTTP 206 Partial Content byte-range header parsing for HTML5 video player."),
            ("INFO", f"Bash: cd {r} && curl -s -I -H \"Range: bytes=0-1024\" http://127.0.0.1:8080/api/videos/demo.mp4 2>&1 | head -n 6"),
            ("OK", "Think: Received 206 Partial Content with correct Content-Range and Accept-Ranges: bytes. Video seeking verified."),
            ("INFO", f"Bash: cd {r} && pytest tests/test_web_video.py -v"),
            ("OK", "Result: 6 passed in 0.038s"),
        ]

    def _agent_episode_git_regression(self) -> list[tuple[str, str]]:
        r = self._root_str
        return [
            ("INFO", "Think: Checking git working directory status before staging changes."),
            ("INFO", f"Bash: cd {r} && git status --short"),
            ("INFO", "Think: Uncommitted modifications in `src/` and `tests/`. Running full regression suite before commit."),
            ("INFO", f"Bash: cd {r} && python3 -m unittest discover -s tests -v"),
            ("OK", "Think: All unit tests passed. Staging and committing changes."),
            ("INFO", f"Bash: cd {r} && git add src/ tests/ && git commit -m \"refactor(agent): improve terminal fake feed realism\""),
        ]

    def _agent_dynamic_pair(self) -> list[tuple[str, str]]:
        r = self._root_str
        mod = self._pick(_MODULES)
        fn = self._pick(_FUNCS)
        test = self._pick(_TESTS)
        path = self._pick(_PATHS)
        needle = self._pick(_NEEDLES)

        tpl = self._rng.randint(0, 5)
        if tpl == 0:
            return [
                ("INFO", f"Think: Verifying if `{mod}.py` has any unresolved type annotation errors."),
                ("INFO", f"Bash: cd {r} && mypy src/fishreader/{mod}.py --ignore-missing-imports"),
            ]
        if tpl == 1:
            return [
                ("INFO", f"Think: Checking AST tree nodes for `{fn}` definition in `{mod}.py`."),
                ("INFO", f"Bash: cd {r} && python3 -c \"import ast; ast.parse(open('{path}').read())\""),
            ]
        if tpl == 2:
            return [
                ("INFO", f"Think: Searching codebase for references to `{needle}` in `src/`."),
                ("INFO", f"Bash: cd {r} && rg \"{needle}\" src/"),
            ]
        if tpl == 3:
            return [
                ("INFO", f"Think: Running targeted test suite `{test}.py` with verbose traceback."),
                ("INFO", f"Bash: cd {r} && pytest tests/{test}.py -v"),
                ("OK", f"Result: tests/{test}.py PASSED [100%]"),
            ]
        if tpl == 4:
            return [
                ("INFO", f"Think: Inspecting git diff stats for `{path}`."),
                ("INFO", f"Bash: cd {r} && git diff --stat {path}"),
            ]
        return [
            ("INFO", f"Think: Checking syntax and ruff linter compliance for `src/fishreader/`."),
            ("INFO", f"Bash: cd {r} && ruff check src/fishreader/"),
            ("OK", "Result: All checks passed without lint errors."),
        ]

    def _agent_burst(self) -> list[tuple[str, str]]:
        if not self._step_queue:
            episodes = [
                self._agent_episode_shell_debug,
                self._agent_episode_ast_statusbar,
                self._agent_episode_parser_opt,
                self._agent_episode_video_stream,
                self._agent_episode_git_regression,
                self._agent_dynamic_pair,
                self._agent_dynamic_pair,
            ]
            chosen_func = self._rng.choice(episodes)
            chosen = chosen_func()
            self._step_queue.extend(chosen)

        # Emit 1 to 2 lines per tick from current queue
        burst_len = min(len(self._step_queue), self._rng.randint(1, 2))
        res = [self._step_queue.popleft() for _ in range(burst_len)]
        return res

    # -- style bursts -------------------------------------------------------------

    def _vite_burst(self) -> list[tuple[str, str]]:
        k = self._choose_key(_VITE_KEYS)
        if k == "vite:modules":
            return [("INFO", f"{self._rng.randint(80, 420)} modules transformed (debug mode)")]
        if k == "vite:built":
            return [("OK", f"built in {self._rng.uniform(0.9, 3.2):.2f}s")]
        if k == "vite:hmr":
            return [
                ("INFO", f"hmr update /src/components/{self._pick(_FRONT_FILES)}.vue "
                         f"({self._rng.randint(1, 6)} changed modules)")
            ]
        if k == "vite:chunk":
            return [
                ("INFO", f"dist/assets/index-{self._rng.randint(0x1a, 0xfe):02x}"
                         f"{self._rng.randint(0x1a, 0xfe):02x}.js    "
                         f"{self._rng.randint(120, 480)}.00 kB  "
                         f"gzip: {self._rng.randint(30, 120)}.00 kB")
            ]
        if k == "vite:warnchunk":
            return [
                ("WARN", f"warn [vite] chunk {self._rng.randint(160, 480)}.00 kB exceeds "
                         "150 kB - consider code-splitting")
            ]
        if k == "vite:reload":
            return [("INFO", f"page reload src/{self._pick(_FRONT_FILES)}.{self._pick(_FRONT_EXT)}")]
        if k == "vite:dep":
            return [("INFO", "[vite] optimized dependencies changed - reloading")]
        return [
            ("WARN", f"[vite] internal server error: [plugin:vite:css] could not resolve "
                     f"'./styles/{self._pick(_FRONT_FILES).lower()}.css'")
        ]

    def _npm_burst(self) -> list[tuple[str, str]]:
        k = self._choose_key(_NPM_KEYS)
        if k == "npm:uptodate":
            return [("OK", f"up to date in {self._rng.randint(90, 900)}ms")]
        if k == "npm:added":
            return [("OK", f"added {self._rng.randint(4, 90)} packages in {self._rng.randint(1, 8)}s")]
        if k == "npm:deprecated":
            return [
                ("WARN", f"npm warn deprecated {self._pick(_PKGS)}@{self._rng.randint(1, 5)}."
                         f"{self._rng.randint(0, 9)}: use crypto.hash instead")
            ]
        if k == "npm:test":
            return [
                ("INFO", "$ npm test"),
                ("OK", f"{self._rng.randint(20, 140)} tests passed in "
                       f"{self._rng.uniform(0.4, 3.1):.2f}s"),
            ]
        if k == "npm:build":
            return [("INFO", f"> {self._pick(_PKGS)}@0.1.0 build")]
        if k == "npm:tsc":
            return [("INFO", "> vite build && tsc -b")]
        if k == "npm:audit":
            return [("OK", "found 0 vulnerabilities")]
        return [("INFO", f"removed {self._rng.randint(1, 25)} packages in {self._rng.randint(1, 4)}s")]

    def _git_burst(self) -> list[tuple[str, str]]:
        k = self._choose_key(_GIT_KEYS)
        branch = self._pick(_BRANCHES)
        if k == "git:status":
            return [("INFO", "$ git status --short")]
        if k == "git:diff":
            return [("INFO", "$ git diff --stat")]
        if k == "git:rebase":
            return [("INFO", f"Rebasing (1/{self._rng.randint(2, 5)})")]
        if k == "git:rebase-done":
            return [("OK", f"Successfully rebased and updated refs/heads/{branch}.")]
        if k == "git:push":
            return [("INFO", f"$ git push origin {branch}")]
        if k == "git:deltas":
            return [
                ("INFO", f"remote: Resolving deltas: 100% ({self._rng.randint(20, 99)}/"
                         f"{self._rng.randint(40, 120)}), done.")
            ]
        if k == "git:ahead":
            return [("INFO", f"Your branch is ahead of 'origin/main' by {self._rng.randint(2, 14)} commit(s).")]
        return [("INFO", "$ git log --oneline -5")]

    # -- public -------------------------------------------------------------------

    def _render_burst(self, ts: str) -> list[tuple[str, str]]:
        if self.style == "agent":
            raw = self._agent_burst()
        elif self.style == "vite":
            raw = self._vite_burst()
        elif self.style == "npm":
            raw = self._npm_burst()
        else:
            raw = self._git_burst()
        return [(label, self._format(ts, label, text)) for label, text in raw]

    def next(self, now: datetime | None = None) -> list[tuple[str, str]]:
        """Return one log burst: [(label, rendered_line), ...].

        Lines are ASCII-only, timestamped and under 120 columns. After a style
        switch the first burst announces the new tool.
        """
        ts = (now or datetime.now()).strftime("%H:%M:%S")

        if self._first_lines:
            out = [
                (label, self._format(ts, label, text)) for label, text in self._first_lines
            ]
            self._first_lines = []
            for _, line in out:
                self._recent_lines.append(line)
            return out

        out = self._render_burst(ts)
        # Re-roll until no line repeats a recently emitted one (slots like
        # issue numbers or search needles can otherwise collide by chance).
        attempts = 0
        while any(line in self._recent_lines for _, line in out) and attempts < 12:
            attempts += 1
            if self.style == "agent":
                self._step_queue.clear()
            out = self._render_burst(ts)
        for _, line in out:
            self._recent_lines.append(line)
        return out
