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
                self.assertTrue(
                    _valid_timestamp(line), f"bad timestamp: {line!r}"
                )
                self.assertTrue(line.startswith(("0", "1", "2")), line)

    def test_every_burst_is_non_empty(self):
        feed = FakeFeed(seed=42)
        for _ in range(50):
            burst = feed.next(now=FIXED_NOW)
            self.assertGreaterEqual(len(burst), 1)
            for label, line in burst:
                self.assertIn(f" [{label}] ", line)

    def test_adjacent_bursts_effectively_differ(self):
        # No adjacent bursts may be identical (template + slot collisions are
        # re-rolled). Under seed 42 this must hold strictly.
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
        # Adjacent *lines* must differ too: fixed templates such as
        # "$ git status --short" or coincidental slot collisions used to slip
        # through the category-level guard.
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
        self.assertGreaterEqual(len(set(bursts)), 100)
        self.assertTrue(any("INFO" in line for burst in bursts for line in burst))
        self.assertTrue(any("WARN" in line for burst in bursts for line in burst))
        self.assertTrue(any("OK" in line for burst in bursts for line in burst))


if __name__ == "__main__":
    unittest.main()