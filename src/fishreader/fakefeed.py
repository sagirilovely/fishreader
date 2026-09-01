"""Fake English agent log generator.

Template + slot randomization keeps the feed varied and ASCII-only, with a
recent-template guard against short-term repeats. Used by widgets/agent_log.
"""

from __future__ import annotations

import random
from collections import deque
from datetime import datetime

MAX_LINE_WIDTH = 120

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


class FakeFeed:
    """Yields short English log entries that look like an agent at work."""

    def __init__(self, seed: int | None = None):
        self._rng = random.Random(seed)
        self._recent: deque[tuple[str, int]] = deque(maxlen=12)  # (category, template idx)
        self._recent_lines: deque[str] = deque(maxlen=16)       # rendered lines

    # -- generators ----------------------------------------------------------

    def _pick(self, pool: list[str]) -> str:
        return self._rng.choice(pool)

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

    # -- public ---------------------------------------------------------------

    def next(self, now: datetime | None = None) -> list[tuple[str, str]]:
        """Return one log burst: [(label, rendered_line), ...].

        Lines are ASCII-only, timestamped and under 120 columns.
        """
        ts = (now or datetime.now()).strftime("%H:%M:%S")

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

        gen = getattr(self, f"_gen_{category}")()
        out: list[tuple[str, str]] = []
        for label, text in gen:
            line = f"{ts} [{label}] {text}"
            if len(line) > MAX_LINE_WIDTH:
                line = line[: MAX_LINE_WIDTH - 3] + "..."
            out.append((label, line))
        # Re-roll until no line repeats a recently emitted one (slots like
        # issue numbers or search needles can otherwise collide by chance).
        attempts = 0
        while any(line in self._recent_lines for _, line in out) and attempts < 6:
            attempts += 1
            category = self._rng.choices(names, weights=weights, k=1)[0]
            tpl = self._rng.randint(0, 3)
            out = []
            for label, text in getattr(self, f"_gen_{category}")():
                line = f"{ts} [{label}] {text}"
                if len(line) > MAX_LINE_WIDTH:
                    line = line[: MAX_LINE_WIDTH - 3] + "..."
                out.append((label, line))
        for _, line in out:
            self._recent_lines.append(line)
        return out