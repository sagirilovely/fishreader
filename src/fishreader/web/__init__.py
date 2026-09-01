"""Web documentation disguise server and assets package for fishreader."""

from __future__ import annotations

from fishreader.web.formatter import format_chapter_as_doc
from fishreader.web.server import WebDisguiseServer, start_web_server

__all__ = ["WebDisguiseServer", "start_web_server", "format_chapter_as_doc"]
