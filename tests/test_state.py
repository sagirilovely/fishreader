"""Unit tests for fishreader.state (ProgressStore).

Covers the test points from docs/开发文档.md §7.1:
atomic writes, corrupt-file recovery, missing-field tolerance.
Schema: {"last_book_id": ..., "books": {id: {chapter_index, char_offset,
scroll_line, updated_at}}}.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.state import ProgressStore  # noqa: E402


class ProgressStoreTolerantLoadTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_missing_file_gives_empty_store(self):
        store = ProgressStore(self.dir / "missing.json").load()
        self.assertIsNone(store.last_book_id())
        self.assertEqual(store.all_book_ids(), [])
        self.assertIsNone(store.get("any"))

    def test_corrupt_json_gives_empty_store(self):
        p = self.dir / "bad.json"
        p.write_text("{ definitely not json", encoding="utf-8")
        store = ProgressStore(p).load()
        self.assertIsNone(store.last_book_id())
        self.assertEqual(store.all_book_ids(), [])

    def test_non_dict_root_gives_empty_store(self):
        p = self.dir / "list.json"
        p.write_text("[1, 2, 3]", encoding="utf-8")
        store = ProgressStore(p).load()
        self.assertEqual(store.all_book_ids(), [])

    def test_non_dict_books_gives_empty_store(self):
        p = self.dir / "bd.json"
        p.write_text(json.dumps({"last_book_id": "x", "books": [1]}), encoding="utf-8")
        store = ProgressStore(p).load()
        self.assertIsNone(store.last_book_id())
        self.assertEqual(store.all_book_ids(), [])

    def test_missing_fields_default_to_zero(self):
        p = self.dir / "mf.json"
        p.write_text(
            json.dumps({"books": {"b1": {"chapter_index": 3}}}), encoding="utf-8"
        )
        store = ProgressStore(p).load()
        entry = store.get("b1")
        self.assertEqual(entry["chapter_index"], 3)
        self.assertEqual(entry["char_offset"], 0)
        self.assertEqual(entry["scroll_line"], 0)
        self.assertEqual(entry["updated_at"], "")

    def test_non_dict_entries_skipped(self):
        p = self.dir / "nd.json"
        p.write_text(
            json.dumps({"books": {"good": {"chapter_index": 1}, "bad": "oops"}}),
            encoding="utf-8",
        )
        store = ProgressStore(p).load()
        self.assertEqual(store.all_book_ids(), ["good"])

    def test_load_preserves_values(self):
        p = self.dir / "ok.json"
        p.write_text(
            json.dumps(
                {
                    "last_book_id": "books/a.txt",
                    "books": {
                        "books/a.txt": {
                            "chapter_index": 3,
                            "char_offset": 12345,
                            "scroll_line": 2,
                            "updated_at": "2026-08-31T12:00:00",
                        }
                    },
                }
            ),
            encoding="utf-8",
        )
        store = ProgressStore(p).load()
        self.assertEqual(store.last_book_id(), "books/a.txt")
        self.assertEqual(store.get("books/a.txt")["char_offset"], 12345)
        self.assertEqual(store.get("books/a.txt")["scroll_line"], 2)


class ProgressStoreMutationTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_update_book_and_get(self):
        store = ProgressStore(self.dir / "p.json")
        store.update_book("books/a.txt", 2, 100, 5)
        entry = store.get("books/a.txt")
        self.assertEqual(entry["chapter_index"], 2)
        self.assertEqual(entry["char_offset"], 100)
        self.assertEqual(entry["scroll_line"], 5)
        self.assertIn("T", entry["updated_at"])  # ISO-ish timestamp
        self.assertEqual(store.get("missing"), None)

    def test_set_and_clear_last_book(self):
        store = ProgressStore(self.dir / "p.json")
        store.set_last_book("books/a.txt")
        self.assertEqual(store.last_book_id(), "books/a.txt")
        store.set_last_book(None)
        self.assertIsNone(store.last_book_id())

    def test_drop_stale_removes_missing_books(self):
        store = ProgressStore(self.dir / "p.json")
        store.update_book("books/old.txt", 1, 2, 3)
        store.update_book("books/keep.txt", 4, 5, 6)
        store.set_last_book("books/old.txt")
        store.drop_stale({"books/keep.txt"})
        self.assertEqual(store.all_book_ids(), ["books/keep.txt"])
        self.assertIsNone(store.last_book_id())

    def test_drop_stale_keeps_last_book_when_valid(self):
        store = ProgressStore(self.dir / "p.json")
        store.update_book("a", 1, 2, 3)
        store.update_book("b", 1, 2, 3)
        store.set_last_book("b")
        store.drop_stale({"a", "b"})
        self.assertEqual(store.last_book_id(), "b")


class ProgressStoreSaveTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_save_roundtrip(self):
        path = self.dir / "p.json"
        store = ProgressStore(path)
        store.update_book("books/a.txt", 2, 100, 5)
        store.set_last_book("books/a.txt")
        store.save()

        self.assertTrue(path.exists())
        # no temp leftovers next to the file
        self.assertEqual(list(self.dir.glob("*.tmp")), [])

        loaded = ProgressStore(path).load()
        self.assertEqual(loaded.last_book_id(), "books/a.txt")
        entry = loaded.get("books/a.txt")
        self.assertEqual(entry["chapter_index"], 2)
        self.assertEqual(entry["char_offset"], 100)
        self.assertEqual(entry["scroll_line"], 5)
        self.assertEqual(
            sorted(entry.keys()),
            ["chapter_index", "char_offset", "scroll_line", "updated_at"],
        )

    def test_save_is_idempotent(self):
        path = self.dir / "p.json"
        store = ProgressStore(path)
        store.update_book("a", 1, 2, 3)
        store.save()
        first = path.read_text(encoding="utf-8")
        store.update_book("a", 9, 8, 7)
        store.save()
        second = path.read_text(encoding="utf-8")
        self.assertNotEqual(first, second)
        self.assertEqual(
            ProgressStore(path).load().get("a")["char_offset"], 8
        )

    def test_save_creates_parent_directories(self):
        path = self.dir / "deep" / "nested" / "p.json"
        store = ProgressStore(path)
        store.update_book("a", 1, 2, 3)
        store.save()
        self.assertTrue(path.exists())
        self.assertIsNotNone(ProgressStore(path).load().get("a"))

    def test_saved_file_always_loadable(self):
        path = self.dir / "p.json"
        store = ProgressStore(path)
        for i in range(10):
            store.update_book(f"b{i}", i, i * 10, 0)
        store.save()
        loaded = ProgressStore(path).load()
        self.assertEqual(len(loaded.all_book_ids()), 10)


if __name__ == "__main__":
    unittest.main()