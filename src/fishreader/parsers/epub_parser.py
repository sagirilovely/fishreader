"""EPUB parser: container.xml -> OPF -> spine -> cleaned text.

Implemented with zipfile + xml.etree + BeautifulSoup (no ebooklib),
per the design doc.
"""

from __future__ import annotations

import posixpath
import zipfile
from pathlib import Path

from fishreader.models import Book

from .base import BaseParser, ParseError, build_book
from .textutils import html_to_text, split_chapters

_OPF_NS = "http://www.idpf.org/2007/opf"
_DC_NS = "http://purl.org/dc/elements/1.1/"
_CNT_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


def _parse_xml(data: bytes, what: str):
    import xml.etree.ElementTree as ET

    try:
        return ET.fromstring(data)
    except ET.ParseError as exc:
        raise ParseError(f"corrupt {what}: {exc}") from exc


def _opf_path(zf: zipfile.ZipFile) -> str:
    try:
        container = zf.read("META-INF/container.xml")
    except KeyError as exc:
        raise ParseError("not an EPUB: missing META-INF/container.xml") from exc
    root = _parse_xml(container, "container.xml")
    rootfile = root.find(f"{{{_CNT_NS}}}rootfiles/{{{_CNT_NS}}}rootfile")
    if rootfile is None:
        raise ParseError("not an EPUB: no rootfile in container.xml")
    full_path = rootfile.get("full-path")
    if not full_path:
        raise ParseError("not an EPUB: rootfile missing full-path")
    return full_path


def _safe_join(base_dir: str, href: str) -> str:
    """Join opf dir + href, refusing directory traversal."""
    rel = posixpath.normpath(href)
    if rel.startswith("..") or posixpath.isabs(rel):
        raise ParseError(f"unsafe path in EPUB: {href!r}")
    return posixpath.normpath(posixpath.join(base_dir, rel))


def _extract_h1(html: str) -> str | None:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    if h1 is None:
        h1 = soup.find(["h2", "h3"]) or soup.find("title")
    if h1 is None:
        return None
    title = h1.get_text(" ", strip=True)
    return title or None


class EpubParser(BaseParser):
    fmt = "epub"

    def parse(self, path: Path) -> Book:
        try:
            zf = zipfile.ZipFile(path)
        except (OSError, zipfile.BadZipFile) as exc:
            raise ParseError(f"cannot open EPUB {path.name}: {exc}") from exc

        with zf:
            opf_path = _opf_path(zf)
            try:
                opf_data = zf.read(opf_path)
            except KeyError as exc:
                raise ParseError(f"EPUB OPF not found: {opf_path}") from exc
            opf_root = _parse_xml(opf_data, "content.opf")

            # metadata
            title_el = opf_root.find(f".//{{{_DC_NS}}}title")
            creator_el = opf_root.find(f".//{{{_DC_NS}}}creator")
            title = title_el.text.strip() if title_el is not None and title_el.text else path.stem
            author = creator_el.text.strip() if creator_el is not None and creator_el.text else None

            # manifest: id -> (href, media_type)
            manifest: dict[str, tuple[str, str]] = {}
            for item in opf_root.findall(f"{{{_OPF_NS}}}manifest/{{{_OPF_NS}}}item"):
                item_id = item.get("id")
                href = item.get("href")
                if item_id and href:
                    manifest[item_id] = (href, item.get("media-type", ""))

            # spine: ordered idrefs
            spine: list[str] = []
            for ref in opf_root.findall(f"{{{_OPF_NS}}}spine/{{{_OPF_NS}}}itemref"):
                idref = ref.get("idref")
                if idref and idref in manifest:
                    spine.append(idref)

            if not spine:
                raise ParseError("EPUB has an empty spine")

            opf_dir = posixpath.dirname(opf_path)

            chapters: list[tuple[str, str]] = []
            for idref in spine:
                href, _media = manifest[idref]
                member = _safe_join(opf_dir, href)
                try:
                    data = zf.read(member)
                except KeyError as exc:
                    raise ParseError(f"EPUB spine item missing: {member}") from exc
                html = data.decode("utf-8", errors="replace")
                text = html_to_text(html)
                if not text.strip():
                    continue
                splits = split_chapters(text)
                if len(splits) > 1 or (splits and splits[0][0] != "前言"):
                    chapters.extend(splits)
                else:
                    ctitle = _extract_h1(html) or "前言"
                    chapters.append((ctitle, text))

            if not chapters:
                chapters = [("前言", "")]

        return build_book(
            book_id=path.as_posix(),
            path=path,
            fmt="epub",
            title=title,
            author=author,
            chapters=chapters,
        )