"""Unit tests for fishreader.library (scan + parse-on-demand loading).

Covers the test points from docs/开发文档.md §7.1 (library row and §4.3):
extension filtering, hidden files/dirs skipped, txt < epub < mobi ordering
with natural filename order (book_2 before book_10), and load_book never
raising for broken files.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.config import load_config  # noqa: E402
from fishreader.library import Candidate, load_book, scan_library  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _make_config(root: Path, scan_dirs: list[str], extensions: list[str]):
    toml = root / "fish.toml"
    toml.write_text(
        "[books]\n"
        f"scan_dirs = {json.dumps(scan_dirs)}\n"
        f"extensions = {json.dumps(extensions)}\n",
        encoding="utf-8",
    )
    return load_config(toml, project_root=root)


class ScanLibraryTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.books = self.root / "books"
        (self.books / ".hidden").mkdir(parents=True)
        (self.books / "sub").mkdir()

        files = {
            "books/book_10.txt": "first",
            "books/book_2.txt": "second",
            "books/a.txt": "third",
            "books/novel.epub": "not a real zip",
            "books/thing.mobi": "garbage",
            "books/.hidden/secret.txt": "secret",
            "books/.dotfile.txt": "dot",
            "books/notes.md": "not a book",
            "books/backup.txt~": "editor temp",
            "books/#tmp.txt": "editor temp",
            "books/.DS_Store": "meta",
            "books/sub/nested.txt": "nested",
        }
        for rel, content in files.items():
            p = self.root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

    def test_filters_and_ordering(self):
        cfg = _make_config(self.root, ["books"], [".txt", ".epub", ".mobi"])
        found = scan_library(cfg)
        names = [(c.fmt, c.display_name) for c in found]
        self.assertEqual(
            names,
            [
                ("txt", "a.txt"),
                ("txt", "book_2.txt"),   # natural order: 2 before 10
                ("txt", "book_10.txt"),
                ("txt", "nested.txt"),   # recursion into subdirectories
                ("epub", "novel.epub"),
                ("mobi", "thing.mobi"),
            ],
        )

    def test_hidden_and_temp_files_skipped(self):
        cfg = _make_config(self.root, ["books"], [".txt", ".epub", ".mobi"])
        found = scan_library(cfg)
        names = {c.display_name for c in found}
        self.assertNotIn("secret.txt", names)   # inside .hidden/
        self.assertNotIn(".dotfile.txt", names)
        self.assertNotIn("notes.md", names)     # unsupported extension
        self.assertNotIn("backup.txt~", names)
        self.assertNotIn("#tmp.txt", names)
        self.assertNotIn(".DS_Store", names)

    def test_extension_filter(self):
        cfg = _make_config(self.root, ["books"], [".txt"])
        found = scan_library(cfg)
        self.assertEqual({c.fmt for c in found}, {"txt"})

    def test_candidate_ids_are_root_relative(self):
        cfg = _make_config(self.root, ["books"], [".txt"])
        found = scan_library(cfg)
        ids = {c.id for c in found}
        self.assertIn("books/a.txt", ids)
        self.assertIn("books/sub/nested.txt", ids)
        self.assertTrue(all(not Path(cid).is_absolute() for cid in ids))

    def test_missing_scan_dir_yields_nothing(self):
        cfg = _make_config(self.root, ["books", "nowhere"], [".txt"])
        found = scan_library(cfg)
        self.assertGreaterEqual(len(found), 1)  # books scanned, missing ignored


class LoadBookTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.cfg = _make_config(self.root, ["."], [".txt", ".epub", ".mobi"])

    def _candidate(self, name: str, fmt: str):
        p = self.root / name
        return Candidate(id=str(p.relative_to(self.root).as_posix()), path=p, fmt=fmt, size=1)

    def test_load_book_good_txt(self):
        p = self.root / "ok.txt"
        p.write_text("第一章\n\n正文。\n", encoding="utf-8")
        book = load_book(self._candidate("ok.txt", "txt"), self.cfg)
        self.assertTrue(book.readable)
        self.assertIsNone(book.reason)
        self.assertEqual(book.id, "ok.txt")
        self.assertEqual(book.title, "ok")
        self.assertEqual([c.title for c in book.chapters], ["第一章"])

    def test_load_book_corrupt_epub_is_unreadable_non_raising(self):
        p = self.root / "broken.epub"
        p.write_bytes((FIXTURES / "corrupt.epub").read_bytes())
        book = load_book(self._candidate("broken.epub", "epub"), self.cfg)
        self.assertFalse(book.readable)
        self.assertIsNotNone(book.reason)
        self.assertEqual(book.chapters, [])

    def test_load_book_broken_mobi_is_unreadable_non_raising(self):
        p = self.root / "broken.mobi"
        p.write_bytes((FIXTURES / "broken.mobi").read_bytes())
        book = load_book(self._candidate("broken.mobi", "mobi"), self.cfg)
        self.assertFalse(book.readable)
        self.assertTrue(
            "DRM" in book.reason or "unsupported" in book.reason.lower(),
            book.reason,
        )

    def test_load_book_unknown_fmt_is_unreadable_non_raising(self):
        book = load_book(self._candidate("x.zzz", "zzz"), self.cfg)
        self.assertFalse(book.readable)
        self.assertIn("unsupported", book.reason)

    def test_load_book_missing_file_is_unreadable_non_raising(self):
        book = load_book(self._candidate("missing.txt", "txt"), self.cfg)
        self.assertFalse(book.readable)
        self.assertIsNotNone(book.reason)


if __name__ == "__main__":
    unittest.main()