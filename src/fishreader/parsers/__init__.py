"""Parser factory."""

from __future__ import annotations

from fishreader.config import Config

from .base import BaseParser, ParseError
from .epub_parser import EpubParser
from .mobi_parser import MobiParser
from .txt_parser import TxtParser


def get_parser(extension_or_fmt: str, config: Config | None = None) -> BaseParser | None:
    """Return a parser for the extension; None when unsupported."""
    fmt = extension_or_fmt.lower().lstrip(".")
    if fmt == "txt":
        return TxtParser()
    if fmt == "epub":
        return EpubParser()
    if fmt == "mobi":
        allow_kup = bool(config and config.books.get("allow_kindleunpack", False))
        return MobiParser(allow_kindleunpack=allow_kup)
    return None


__all__ = ["BaseParser", "ParseError", "get_parser"]