"""Unit tests for the Web Disguise HTTP Server and API request handling."""

import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from fishreader.config import load_config
from fishreader.web.real_docs import get_real_doc
from fishreader.web.server import DisguiseRequestHandler, WebDisguiseServer


class MockServer:
    def __init__(self, wrapper):
        self.wrapper = wrapper


from email.message import Message


def call_handler(server_wrapper: WebDisguiseServer, method: str, path: str, body: bytes = b"", headers_dict: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    """Execute a request against DisguiseRequestHandler in-memory."""
    rfile = io.BytesIO(body)
    wfile = io.BytesIO()

    # Create handler with mocked socket
    handler = DisguiseRequestHandler.__new__(DisguiseRequestHandler)
    handler.server = MockServer(server_wrapper)
    handler.rfile = rfile
    handler.wfile = wfile
    handler.client_address = ("127.0.0.1", 12345)
    handler.requestline = f"{method} {path} HTTP/1.1"
    handler.command = method
    handler.path = path
    handler.request_version = "HTTP/1.1"

    msg = Message()
    if body:
        msg["Content-Length"] = str(len(body))
        msg["Content-Type"] = "application/json"
    if headers_dict:
        for k, v in headers_dict.items():
            msg[k] = v
    handler.headers = msg
    handler.close_connection = True

    if method == "GET":
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    elif method == "OPTIONS":
        handler.do_OPTIONS()

    output = wfile.getvalue()
    # Parse status and headers from output
    lines = output.split(b"\r\n")
    status_line = lines[0].decode("utf-8", errors="ignore")
    status_code = int(status_line.split()[1]) if len(status_line.split()) > 1 else 0

    headers = {}
    idx = 1
    while idx < len(lines) and lines[idx]:
        header_line = lines[idx].decode("utf-8", errors="ignore")
        if ": " in header_line:
            k, v = header_line.split(": ", 1)
            headers[k.lower()] = v
        idx += 1

    body_bytes = b"\r\n".join(lines[idx + 1 :]) if idx < len(lines) else b""
    return status_code, headers, body_bytes


class WebServerTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        books_dir = self.root / "books"
        books_dir.mkdir(parents=True)
        (books_dir / "sample.txt").write_text(
            "第一章 开篇\n\n正文第一段。\n\n正文第二段。\n\n第二章 进阶\n\n更多内容。\n",
            encoding="utf-8",
        )
        self.config = load_config(self.root / "fish.toml", project_root=self.root)
        self.server = WebDisguiseServer(self.config, self.root, port=8890)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_status_endpoint(self):
        status, headers, body = call_handler(self.server, "GET", "/api/status")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data["status"], "running")
        self.assertIn("vue", data["themes"])
        self.assertIn("react", data["themes"])

    def test_books_endpoint(self):
        status, headers, body = call_handler(self.server, "GET", "/api/books")
        self.assertEqual(status, 200)
        books = json.loads(body.decode("utf-8"))
        self.assertIsInstance(books, list)
        self.assertEqual(len(books), 1)
        self.assertTrue(books[0]["readable"])
        self.assertEqual(books[0]["title"], "sample")

    def test_book_detail_and_chapter_endpoint(self):
        book_id = "books/sample.txt"
        status, _, body = call_handler(self.server, "GET", f"/api/books/{book_id}")
        self.assertEqual(status, 200)
        detail = json.loads(body.decode("utf-8"))
        self.assertEqual(detail["id"], book_id)
        self.assertEqual(len(detail["chapters"]), 2)

        # Chapter 0
        status, _, body = call_handler(
            self.server, "GET", f"/api/books/{book_id}/chapters/0?theme=vue&disguise=hybrid"
        )
        self.assertEqual(status, 200)
        ch0 = json.loads(body.decode("utf-8"))
        self.assertEqual(ch0["chapter_index"], 0)
        self.assertEqual(ch0["chapter_title"], "第一章 开篇")
        self.assertIn("doc", ch0)
        self.assertGreater(len(ch0["doc"]["sections"]), 0)

    def test_real_docs_endpoint(self):
        status, _, body = call_handler(self.server, "GET", "/api/real_docs/vue")
        self.assertEqual(status, 200)
        vue_doc = json.loads(body.decode("utf-8"))
        self.assertEqual(vue_doc["theme"], "vue")
        self.assertEqual(vue_doc["title"], "响应式基础")

        status, _, body = call_handler(self.server, "GET", "/api/real_docs/react")
        self.assertEqual(status, 200)
        react_doc = json.loads(body.decode("utf-8"))
        self.assertEqual(react_doc["theme"], "react")

    def test_progress_persistence(self):
        post_data = json.dumps({
            "book_id": "books/sample.txt",
            "chapter_index": 1,
            "char_offset": 50,
            "scroll_line": 2,
        }).encode("utf-8")

        status, _, body = call_handler(self.server, "POST", "/api/progress", body=post_data)
        self.assertEqual(status, 200)
        res = json.loads(body.decode("utf-8"))
        self.assertTrue(res["ok"])

        # Fetch progress again
        status, _, body = call_handler(self.server, "GET", "/api/progress")
        self.assertEqual(status, 200)
        progress = json.loads(body.decode("utf-8"))
        self.assertEqual(progress["last_book_id"], "books/sample.txt")
        self.assertEqual(progress["books"]["books/sample.txt"]["chapter_index"], 1)

    def test_static_files_served(self):
        status, headers, body = call_handler(self.server, "GET", "/")
        self.assertEqual(status, 200)
        html = body.decode("utf-8")
        self.assertIn("Vue.js", html)
        self.assertIn("data-theme", html)

        status, headers, body = call_handler(self.server, "GET", "/style.css")
        self.assertEqual(status, 200)
        css = body.decode("utf-8")
        self.assertIn("--brand-color", css)


if __name__ == "__main__":
    unittest.main()
