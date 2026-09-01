"""Local HTTP server serving the Web Documentation Disguise SPA and API endpoints."""

from __future__ import annotations

import json
import logging
import mimetypes
import socket
import sys
import threading
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fishreader.library import Candidate, load_book, scan_library
from fishreader.models import Book
from fishreader.state import ProgressStore
from fishreader.web.formatter import format_chapter_as_doc
from fishreader.web.real_docs import get_real_doc

if TYPE_CHECKING:
    from fishreader.config import Config

logger = logging.getLogger("fishreader.web")


class DisguiseRequestHandler(BaseHTTPRequestHandler):
    """Custom HTTP handler for API endpoints and static SPA assets."""

    server_version = "fishreader-doc-disguise/1.0"

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default stderr logging to keep terminal TUI pristine
        pass

    def _send_json(self, data: Any, status: int = HTTPStatus.OK) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(raw)

    def _send_error(self, message: str, status: int = HTTPStatus.BAD_REQUEST) -> None:
        self._send_json({"error": message}, status=status)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/api/status":
            self._handle_status()
        elif path == "/api/books":
            self._handle_books()
        elif path == "/api/videos":
            self._handle_videos_list()
        elif path.startswith("/api/videos/"):
            self._handle_video_stream(path)
        elif path.startswith("/api/real_docs"):
            self._handle_real_docs(path)
        elif path.startswith("/api/books/"):
            self._handle_book_detail_or_chapter(path, query)
        elif path == "/api/progress":
            self._handle_get_progress()
        else:
            self._handle_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/progress":
            self._handle_post_progress()
        else:
            self._send_error("Not Found", HTTPStatus.NOT_FOUND)

    # -- Handlers -------------------------------------------------------------

    def _handle_status(self) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        config = server.config
        progress = server.get_progress_store()
        last_id = progress.last_book_id()
        data = {
            "status": "running",
            "version": config.disguise.get("agent_version", "1.0.0"),
            "current_book_id": last_id,
            "theme": config.web.get("theme", "vue"),
            "themes": ["vue", "react", "rust", "python"],
            "disguise_modes": ["clean", "hybrid", "code_dense"],
            "video": {
                "enabled": config.web_video_enabled,
                "position": config.web_video_position,
                "default_size": config.web_video_default_size,
                "ad_style": config.web_ad_style,
                "auto_pause_on_boss": config.web_auto_pause_on_boss,
            },
        }
        self._send_json(data)

    def _handle_books(self) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        candidates = server.get_candidates()
        result = []
        for c in candidates:
            # Check cached book if loaded, else use candidate info
            book = server._book_cache.get(c.id)
            result.append(
                {
                    "id": c.id,
                    "title": book.title if book else c.path.stem,
                    "author": book.author if book else None,
                    "fmt": c.fmt,
                    "readable": book.readable if book else True,
                    "reason": book.reason if book else None,
                    "size_bytes": c.size,
                }
            )
        self._send_json(result)

    def _handle_book_detail_or_chapter(
        self, path: str, query: dict[str, list[str]]
    ) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        # Format: /api/books/<book_id> OR /api/books/<book_id>/chapters/<idx>
        parts = path[len("/api/books/") :].split("/")
        if not parts or not parts[0]:
            self._send_error("Missing book ID", HTTPStatus.BAD_REQUEST)
            return

        # Check if chapters is in parts
        if "chapters" in parts:
            c_idx_pos = parts.index("chapters")
            book_id_parts = parts[:c_idx_pos]
            book_id = urllib.parse.unquote("/".join(book_id_parts))
            try:
                chapter_idx = int(parts[c_idx_pos + 1])
            except (IndexError, ValueError):
                self._send_error("Invalid chapter index", HTTPStatus.BAD_REQUEST)
                return

            book = server.get_book(book_id)
            if not book or not book.readable:
                self._send_error(
                    f"Book not readable: {book.reason if book else 'not found'}",
                    HTTPStatus.NOT_FOUND,
                )
                return

            if not 0 <= chapter_idx < len(book.chapters):
                self._send_error("Chapter index out of range", HTTPStatus.NOT_FOUND)
                return

            ch = book.chapters[chapter_idx]
            theme = query.get("theme", [server.config.web.get("theme", "vue")])[0]
            disguise = query.get(
                "disguise", [server.config.web.get("disguise_mode", "hybrid")]
            )[0]

            formatted = format_chapter_as_doc(
                chapter_title=ch.title,
                chapter_content=ch.content,
                theme=theme,
                disguise_mode=disguise,
            )

            self._send_json(
                {
                    "book_id": book.id,
                    "book_title": book.title,
                    "chapter_index": chapter_idx,
                    "chapter_title": ch.title,
                    "total_chapters": len(book.chapters),
                    "start_char": ch.start_char,
                    "end_char": ch.end_char,
                    "doc": {
                        "title": formatted.title,
                        "theme": formatted.theme,
                        "toc": formatted.toc,
                        "sections": formatted.sections,
                        "paragraph_count": formatted.paragraph_count,
                    },
                }
            )
        else:
            # Single book detail
            book_id = urllib.parse.unquote("/".join(parts))
            book = server.get_book(book_id)
            if not book:
                self._send_error("Book not found", HTTPStatus.NOT_FOUND)
                return

            self._send_json(
                {
                    "id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "fmt": book.fmt,
                    "readable": book.readable,
                    "reason": book.reason,
                    "total_chars": book.total_chars,
                    "chapters": [
                        {
                            "index": c.index,
                            "title": c.title,
                            "length": len(c.content),
                            "start_char": c.start_char,
                        }
                        for c in book.chapters
                    ],
                }
            )

    def _handle_real_docs(self, path: str) -> None:
        # /api/real_docs/<theme>
        parts = path.split("/")
        theme = parts[-1] if len(parts) > 3 and parts[-1] else "vue"
        doc = get_real_doc(theme)
        self._send_json(doc)

    def _handle_get_progress(self) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        progress = server.get_progress_store()
        self._send_json(progress.raw)

    def _handle_post_progress(self) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body)
        except Exception as exc:
            self._send_error(f"Invalid JSON payload: {exc}")
            return

        book_id = data.get("book_id")
        if not book_id or not isinstance(book_id, str):
            self._send_error("Missing book_id")
            return

        chapter_idx = int(data.get("chapter_index", 0))
        char_offset = int(data.get("char_offset", 0))
        scroll_line = int(data.get("scroll_line", 0))

        progress = server.get_progress_store()
        progress.update_book(book_id, chapter_idx, char_offset, scroll_line)
        progress.set_last_book(book_id)
        progress.save()

        self._send_json({"ok": True, "saved": progress.get(book_id)})

    def _handle_videos_list(self) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        videos = server.get_videos()
        self._send_json(videos)

    def _handle_video_stream(self, path: str) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        filename = urllib.parse.unquote(path[len("/api/videos/") :])
        if not filename:
            self._send_error("Missing video filename", HTTPStatus.BAD_REQUEST)
            return

        target = (server.videos_dir / filename).resolve()
        try:
            target.relative_to(server.videos_dir.resolve())
        except ValueError:
            self._send_error("Forbidden", HTTPStatus.FORBIDDEN)
            return

        if not target.is_file():
            self._send_error("Video not found", HTTPStatus.NOT_FOUND)
            return

        file_size = target.stat().st_size
        ctype, _ = mimetypes.guess_type(str(target))
        if not ctype:
            ctype = "video/mp4"

        range_header = self.headers.get("Range")
        if range_header and range_header.startswith("bytes="):
            # Parse Range: bytes=start-end
            range_val = range_header[len("bytes=") :].strip()
            parts = range_val.split("-")
            try:
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            except ValueError:
                start = 0
                end = file_size - 1

            if start >= file_size or end >= file_size or start > end:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return

            length = end - start + 1
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()

            try:
                with open(target, "rb") as fh:
                    fh.seek(start)
                    remaining = length
                    while remaining > 0:
                        chunk_size = min(65536, remaining)
                        data = fh.read(chunk_size)
                        if not data:
                            break
                        self.wfile.write(data)
                        remaining -= len(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
        else:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            try:
                with open(target, "rb") as fh:
                    while True:
                        data = fh.read(65536)
                        if not data:
                            break
                        self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

    def _handle_static(self, path: str) -> None:
        server: WebDisguiseServer = self.server.wrapper  # type: ignore[attr-defined]
        static_dir = server.static_dir

        clean_path = path.lstrip("/")
        if not clean_path or clean_path == "index.html":
            target = static_dir / "index.html"
        else:
            target = (static_dir / clean_path).resolve()

        # Prevent directory traversal
        try:
            target.relative_to(static_dir)
        except ValueError:
            self._send_error("Forbidden", HTTPStatus.FORBIDDEN)
            return

        if not target.is_file():
            # Fallback to index.html for SPA router
            target = static_dir / "index.html"

        if not target.is_file():
            self._send_error("Static asset not found", HTTPStatus.NOT_FOUND)
            return

        ctype, _ = mimetypes.guess_type(str(target))
        if not ctype:
            ctype = "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"

        try:
            content = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except OSError as exc:
            self._send_error(f"Cannot read file: {exc}", HTTPStatus.INTERNAL_SERVER_ERROR)


class WebDisguiseServer:
    """Threaded web server serving the documentation disguise frontend & APIs."""

    def __init__(
        self,
        config: Config,
        project_root: Path,
        host: str | None = None,
        port: int | None = None,
    ):
        self.config = config
        self.root = project_root
        self.host = host or config.web.get("host", "127.0.0.1")
        self.preferred_port = port or int(config.web.get("port", 8080))
        self.port = self.preferred_port
        self.static_dir = Path(__file__).resolve().parent / "static"
        self.videos_dir = project_root / "videos"
        try:
            self.videos_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

        self._candidates: list[Candidate] | None = None
        self._book_cache: dict[str, Book] = {}
        self._progress: ProgressStore | None = None
        self._lock = threading.RLock()
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def get_videos(self) -> list[dict[str, Any]]:
        with self._lock:
            if not self.videos_dir.is_dir():
                return []
            exts = {".mp4", ".webm", ".ogg", ".mov", ".mkv", ".m4v"}
            items = []
            for p in sorted(self.videos_dir.glob("*")):
                if p.is_file() and p.suffix.lower() in exts and not p.name.startswith("."):
                    items.append(
                        {
                            "id": p.name,
                            "name": p.name,
                            "size_bytes": p.stat().st_size,
                            "fmt": p.suffix.lower().lstrip("."),
                            "url": f"/api/videos/{urllib.parse.quote(p.name)}",
                        }
                    )
            return items

    def get_progress_store(self) -> ProgressStore:
        with self._lock:
            if self._progress is None:
                self._progress = ProgressStore(self.config.progress_path()).load()
            return self._progress

    def get_candidates(self) -> list[Candidate]:
        with self._lock:
            if self._candidates is None:
                self._candidates = scan_library(self.config)
            return self._candidates

    def get_book(self, book_id: str) -> Book | None:
        with self._lock:
            if book_id in self._book_cache:
                return self._book_cache[book_id]
            candidates = self.get_candidates()
            cand = next((c for c in candidates if c.id == book_id), None)
            if not cand:
                return None
            book = load_book(cand, self.config)
            if len(self._book_cache) > 16:
                self._book_cache.clear()
            self._book_cache[book_id] = book
            return book

    def _find_available_server(self) -> tuple[ThreadingHTTPServer, int]:
        """Try binding to preferred_port; increment if occupied."""
        cur_port = self.preferred_port
        max_tries = 50
        for i in range(max_tries):
            test_port = cur_port + i
            try:
                # Test socket binding
                server = ThreadingHTTPServer(
                    (self.host, test_port), DisguiseRequestHandler
                )
                server.wrapper = self  # type: ignore[attr-defined]
                server.daemon_threads = True
                return server, test_port
            except OSError as exc:
                if i == max_tries - 1:
                    raise OSError(
                        f"Could not bind to {self.host} ports {cur_port}-{test_port}: {exc}"
                    ) from exc
                continue
        raise OSError("Unable to find available port")

    def start(self) -> str:
        """Start the background HTTP server and return its URL."""
        if self._running:
            return self.url

        self._server, self.port = self._find_available_server()
        self._running = True
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            name="FishWebDisguiseServer",
            daemon=True,
        )
        self._thread.start()
        return self.url

    def stop(self) -> None:
        """Shutdown the HTTP server cleanly."""
        if not self._running or not self._server:
            return
        self._running = False
        try:
            self._server.shutdown()
            self._server.server_close()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._server = None
        self._thread = None

    @property
    def url(self) -> str:
        h = "localhost" if self.host in ("127.0.0.1", "0.0.0.0") else self.host
        return f"http://{h}:{self.port}"

    @property
    def is_running(self) -> bool:
        return self._running


def start_web_server(
    config: Config,
    project_root: Path,
    host: str | None = None,
    port: int | None = None,
) -> WebDisguiseServer:
    """Convenience factory to initialize and launch WebDisguiseServer."""
    server = WebDisguiseServer(config, project_root, host, port)
    server.start()
    return server
