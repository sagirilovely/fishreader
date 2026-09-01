"""Fake English log feed with selectable tool styles.

Template + slot randomization keeps the feed varied and ASCII-only, with a
recent-template guard against short-term repeats. Each style imitates a
different tool so a backend, frontend or infra dev can pick a plausible one:

- agent:  generic coding-agent activity (planning/search/edit/test/git/review)
- vite:   vite dev server / build output
- npm:    npm install / scripts output
- git:    terminal git sessions

Used by widgets/agent_log.
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime

MAX_LINE_WIDTH = 120

LOG_STYLES = ("agent", "vite", "npm", "git")

_MODULES = [
    "auth", "parser", "api", "cache", "scheduler", "storage", "net",
    "core", "utils", "config", "db", "render",
]
_FUNCS = [
    "validate", "extract", "retry", "normalize", "flush", "handle",
    "load", "merge", "dispatch", "render", "resolve", "backoff",
]
_TESTS = [
    "test_auth_flow", "test_parse_edge", "test_cache_miss",
    "test_retry_limit", "test_payload_size", "test_conn_pool",
]
_PATHS = [
    "src/services.py", "src/net/session.py", "tests/test_api.py",
    "docs/notes.md", "src/core/worker.py", "scripts/smoke.sh",
]
_ISSUES = ["issue #4711", "TICKET-223", "regression #4080", "flaky job #99"]
_NEEDLES = ["session handling", "cache key", "deadline", "retry budget", "backoff"]

# category -> probability weight
_CATEGORIES = [
    ("planning", 0.22),
    ("edit", 0.20),
    ("test", 0.20),
    ("search", 0.16),
    ("git", 0.12),
    ("review", 0.10),
]

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
_BRANCHES = ["main", "dev", "feature/session", "fix/cache", "hotfix/parser", "release/2.3"]

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

    def __init__(self, style: str = "agent", seed: int | None = None):
        if style not in LOG_STYLES:
            raise ValueError(f"unknown log style {style!r}, expected one of {LOG_STYLES}")
        self.style = style
        self._first_lines = list(_STYLE_INTROS.get(style, ()))
        self._rng = random.Random(seed)
        self._recent: deque[tuple] = deque(maxlen=12)   # template keys
        self._recent_lines: deque[str] = deque(maxlen=16)  # rendered lines

    def set_style(self, style: str) -> None:
        """Switch style; the next burst announces the new tool."""
        if style not in LOG_STYLES:
            raise ValueError(f"unknown log style {style!r}, expected one of {LOG_STYLES}")
        if style != self.style:
            self.style = style
            self._first_lines = list(_STYLE_INTROS.get(style, ()))
            self._recent.clear()
            self._recent_lines.clear()

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
        line = f"{ts} [{label}] {text}"
        if len(line) > MAX_LINE_WIDTH:
            line = line[: MAX_LINE_WIDTH - 3] + "..."
        return line

    # -- agent generators --------------------------------------------------------

    def _gen_planning(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 3)
        mod, fn, issue = self._pick(_MODULES), self._pick(_FUNCS), self._pick(_ISSUES)
        if tpl == 0:
            return [("INFO", f"planning next edit: reduce coupling in {mod}")]
        if tpl == 1:
            return [("INFO", f"weighing {self._rng.randint(2, 4)} options for {mod}.{fn}")]
        if tpl == 2:
            return [("INFO", f"gathering context for {issue}")]
        return [("INFO", f"outlining steps: {fn} -> {self._pick(_FUNCS)} ({mod})")]

    def _gen_edit(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 3)
        mod, path = self._pick(_MODULES), self._pick(_PATHS)
        if tpl == 0:
            return [("INFO", f"updating {path}")]
        if tpl == 1:
            return [("INFO", f"applying patch to {mod}.py - {self._rng.randint(1, 9)} hunks")]
        if tpl == 2:
            return [("INFO", f"renamed {self._pick(_FUNCS)} -> {self._pick(_FUNCS)} in {mod}")]
        return [("INFO", f"touching {path}"), ("INFO", "0 conflicts after merge")]

    def _gen_test(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 3)
        passed = self._rng.randint(40, 120)
        total = passed + self._rng.randint(0, 10)
        if tpl == 0:
            return [("INFO", f"$ pytest -q tests/{self._pick(_TESTS)}.py")]
        if tpl == 1:
            return [("OK", f"{passed}/{total} tests passed ({self._rng.randint(0, 4)} skipped)")]
        if tpl == 2:
            return [("WARN", f"{self._rng.randint(1, 3)} failing: {self._pick(_TESTS)}")]
        return [
            ("INFO", f"$ pytest -q tests/ -k {self._pick(_TESTS)}"),
            ("OK", f"{passed}/{total} tests passed"),
        ]

    def _gen_search(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 2)
        needle = self._pick(_NEEDLES)
        if tpl == 0:
            return [("INFO", f'$ rg "{needle}" src/')]
        if tpl == 1:
            return [
                ("INFO", f'$ rg "{needle}" src/'),
                ("OK", f"{self._rng.randint(2, 42)} matches in {self._rng.randint(2, 9)} files"),
            ]
        return [("OK", f'found "{needle}" in {self._pick(_PATHS)}')]

    def _gen_git(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 3)
        n = self._rng.randint(1, 12)
        if tpl == 0:
            return [("INFO", "$ git status --short")]
        if tpl == 1:
            return [
                ("INFO", f"{n} changed files, {self._rng.randint(4, 200)} insertions(+)"),
                ("INFO", f"{self._rng.randint(0, 40)} deletions(-)"),
            ]
        if tpl == 2:
            return [("OK", f"staged {n} files on branch fix/{self._pick(_MODULES)}")]
        return [("INFO", "$ git diff --stat")]

    def _gen_review(self) -> list[tuple[str, str]]:
        tpl = self._rng.randint(0, 2)
        mod, fn = self._pick(_MODULES), self._pick(_FUNCS)
        if tpl == 0:
            return [("INFO", f"inspecting diff hunk in {mod}.py")]
        if tpl == 1:
            return [("INFO", f"checking edge cases for {mod}.{fn}")]
        return [("WARN", f"note: {fn} may block on empty input ({mod})")]

    def _agent_burst(self) -> list[tuple[str, str]]:
        names = [name for name, _ in _CATEGORIES]
        weights = [w for _, w in _CATEGORIES]
        category = self._rng.choices(names, weights=weights, k=1)[0]
        tpl = self._rng.randint(0, 3)
        key = (category, tpl)
        if key in self._recent:
            for _ in range(32):  # avoid repeating the same template recently
                category = self._rng.choices(names, weights=weights, k=1)[0]
                tpl = self._rng.randint(0, 3)
                key = (category, tpl)
                if key not in self._recent:
                    break
        self._recent.append(key)
        return getattr(self, f"_gen_{category}")()

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
        while any(line in self._recent_lines for _, line in out) and attempts < 6:
            attempts += 1
            out = self._render_burst(ts)
        for _, line in out:
            self._recent_lines.append(line)
        return out
