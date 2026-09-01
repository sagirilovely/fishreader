"""Unit tests for fishreader.fakefeed.

Covers the test points from docs/开发文档.md §7.1: 1000 consecutive entries
must stay English-only ASCII with sane length; seed reproducibility;
adjacent bursts differ (bounded rare repeats, see note below).
"""

import sys
import unittest
from datetime import datetime
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.fakefeed import FakeFeed, MAX_LINE_WIDTH  # noqa: E402

LABELS = {"INFO", "WARN", "OK"}

# A fixed clock makes the test deterministic: every burst shares one
# timestamp, so any equality between adjacent bursts is a content collision.
FIXED_NOW = datetime(2026, 9, 1, 12, 0, 0)


def _valid_timestamp(line: str) -> bool:
    ts = line[:8]
    return (
        len(ts) == 8
        and ts[2] == ":"
        and ts[5] == ":"
        and ts[:2].isdigit()
        and ts[3:5].isdigit()
        and ts[6:8].isdigit()
    )


class FakeFeedTest(unittest.TestCase):
    def test_seed_reproducible(self):
        a = FakeFeed(seed=42)
        b = FakeFeed(seed=42)
        for _ in range(20):
            self.assertEqual(a.next(now=FIXED_NOW), b.next(now=FIXED_NOW))

    def test_different_seeds_differ(self):
        a = FakeFeed(seed=42)
        b = FakeFeed(seed=7)
        same = sum(
            a.next(now=FIXED_NOW) == b.next(now=FIXED_NOW) for _ in range(20)
        )
        self.assertLess(same, 20)

    def test_1000_calls_invariants(self):
        feed = FakeFeed(seed=42)
        for _ in range(1000):
            for label, line in feed.next(now=FIXED_NOW):
                self.assertIn(label, LABELS)
                self.assertTrue(line.isascii(), f"non-ascii line: {line!r}")
                self.assertLessEqual(len(line), MAX_LINE_WIDTH)
                self.assertLessEqual(len(line), 120)
                # Agent lines start with Think, Bash, or Result
                self.assertTrue(
                    line.startswith(("Think", "Bash", "Result", "View", "Edit")),
                    f"unexpected agent line format: {line!r}",
                )

    def test_every_burst_is_non_empty(self):
        feed = FakeFeed(seed=42)
        for _ in range(50):
            burst = feed.next(now=FIXED_NOW)
            self.assertGreaterEqual(len(burst), 1)
            for label, line in burst:
                self.assertIn(label, LABELS)
                self.assertTrue(line)

    def test_adjacent_bursts_effectively_differ(self):
        # No adjacent bursts may be identical
        feed = FakeFeed(seed=42)
        prev = None
        identical = 0
        for _ in range(1000):
            burst = feed.next(now=FIXED_NOW)
            if prev is not None and burst == prev:
                identical += 1
            prev = burst
        self.assertEqual(identical, 0)

    def test_no_adjacent_duplicate_lines(self):
        feed = FakeFeed(seed=42)
        prev = None
        duplicate_lines = 0
        for _ in range(1000):
            for label, line in feed.next(now=FIXED_NOW):
                if line == prev:
                    duplicate_lines += 1
                prev = line
        self.assertEqual(duplicate_lines, 0)

    def test_feed_has_variety(self):
        feed = FakeFeed(seed=42)
        bursts = [tuple(line for _, line in feed.next(now=FIXED_NOW)) for _ in range(1000)]
        self.assertGreaterEqual(len(set(bursts)), 50)
        all_lines = [line for burst in bursts for line in burst]
        self.assertTrue(any(line.startswith("Think") for line in all_lines))
        self.assertTrue(any(line.startswith("Bash") for line in all_lines))


class FakeFeedStyleTest(unittest.TestCase):
    """vite/npm/git styles: ASCII, labeled, tool-appropriate content."""

    def test_each_style_is_ascii_and_labeled(self):
        for style in ("agent", "vite", "npm", "git"):
            with self.subTest(style=style):
                feed = FakeFeed(style=style, seed=9)
                bursts = [feed.next(now=FIXED_NOW) for _ in range(60)]
                seen = False
                for burst in bursts:
                    self.assertGreaterEqual(len(burst), 1)
                    for label, line in burst:
                        seen = True
                        self.assertIn(label, LABELS)
                        self.assertTrue(line.isascii(), f"non-ascii {style}: {line!r}")
                        self.assertLessEqual(len(line), MAX_LINE_WIDTH)
                self.assertTrue(seen)

    def test_first_burst_announces_the_tool(self):
        feed = FakeFeed(style="vite", seed=1)
        first = [line for _, line in feed.next(now=FIXED_NOW)]
        self.assertTrue(any("VITE" in line for line in first))
        feed.set_style("npm")
        second = [line for _, line in feed.next(now=FIXED_NOW)]
        self.assertTrue(any("npm install" in line for line in second))
        feed.set_style("git")
        third = [line for _, line in feed.next(now=FIXED_NOW)]
        self.assertTrue(any("git pull" in line for line in third))

    def test_style_flavor_kept_over_many_bursts(self):
        feed = FakeFeed(style="npm", seed=4)
        lines = [
            line
            for _ in range(40)
            for _, line in feed.next(now=FIXED_NOW)
        ]
        self.assertTrue(any("npm" in line for line in lines))
        feed.set_style("git")
        lines = [
            line
            for _ in range(40)
            for _, line in feed.next(now=FIXED_NOW)
        ]
        self.assertTrue(
            any(
                "git" in line or "Rebasing" in line or "Fast-forward" in line
                for line in lines
            )
        )

    def test_unknown_style_rejected(self):
        with self.assertRaises(ValueError):
            FakeFeed(style="emacs")
        feed = FakeFeed(style="agent")
        with self.assertRaises(ValueError):
            feed.set_style("emacs")


if __name__ == "__main__":
    unittest.main()