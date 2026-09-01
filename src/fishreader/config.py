"""Configuration loading, validation and default file generation.

Config format is TOML (fish.toml), loaded with tomllib and deep-merged
over DEFAULTS. Unknown user keys are ignored.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Reader width is validated between these bounds when given as a percentage.
READER_WIDTH_MIN_PCT = 25
READER_WIDTH_MAX_PCT = 40

FONT_SIZES = ("small", "medium", "large")
NOVEL_STYLES = ("markdown", "comment", "docstring")
READER_POSITIONS = ("left", "right", "bottom")
STATUS_LINES = ("minimal", "full")
LOG_STYLES = ("agent", "vite", "npm", "git")

# Spacing is expressed in *rows*, not in whole blank lines: a terminal can
# only draw whole rows, so a fractional value is spread over the page —
# 0.25 adds one blank row every 4 lines, 0.5 every 2 lines, 1.0 after every
# line. This is what makes density tunable below "one blank line".
SPACING_STEP = 0.25
SPACING_MIN = 0.0
SPACING_MAX = 2.0
# Cycle order offered by the settings menu (0 means "follow font_size").
SPACING_OPTIONS: list[float] = [
    SPACING_MIN + i * SPACING_STEP
    for i in range(int((SPACING_MAX - SPACING_MIN) / SPACING_STEP) + 1)
]

# font_size -> (line_spacing, paragraph_spacing)
FONT_SIZE_SPACING: dict[str, tuple[float, float]] = {
    "small": (0.0, 0.0),
    "medium": (0.0, 1.0),
    "large": (1.0, 2.0),
}

DEFAULTS: dict = {
    "books": {
        "scan_dirs": ["books"],
        "extensions": [".epub", ".mobi", ".txt"],
        "allow_kindleunpack": False,
    },
    "reader": {
        "font_size": "medium",
        "line_spacing": 0,
        "paragraph_spacing": 0,
        "reader_width": "30%",
        "reader_position": "right",
        "novel_style": "markdown",
        "resume_last": True,
    },
    "disguise": {
        "agent_name": "CodeAgent",
        "agent_version": "0.4.2",
        "log_interval_min": 0.8,
        "log_interval_max": 1.5,
        "log_style": "agent",
        "status_line": "minimal",
        "boss_key": "b",
        "full_hide_chinese": True,
    },
    "theme": {
        "log_level_color": True,
        "reader_color": "gray",
        "accent": "green",
    },
    "progress": {
        "file": ".fish_progress.json",
        "autosave_on_page": True,
    },
}

DEFAULT_CONFIG_TEXT = """\
# fish.toml — fishreader 配置
# 首次启动自动生成；修改后重启生效。未知的键会被忽略。

[books]
scan_dirs = ["books"]              # 扫描目录（相对项目根，可多个）
extensions = [".epub", ".mobi", ".txt"]
allow_kindleunpack = false          # MOBI 解析失败时是否尝试外部 kindleunpack CLI

[reader]
# 以下设置可在终端内按 s 打开设置菜单实时调整，改完自动写回本文件
font_size = "medium"               # small | medium | large（显示密度档位，不改终端真实字号）
line_spacing = 0                   # 行距（行后的额外空行数，支持 0.25 小数）；0 = 跟随 font_size
paragraph_spacing = 0              # 段距（段落后的额外空行数，支持 0.25 小数）；0 = 跟随 font_size
reader_width = "30%"               # 阅读区占终端宽度百分比（25%-40%）或固定列数
reader_position = "right"          # left | right | bottom（底部时阅读区占满宽度）
novel_style = "markdown"           # markdown | comment | docstring
resume_last = true                 # 启动时自动续读上次书籍

[disguise]
agent_name = "CodeAgent"
agent_version = "0.4.2"
log_interval_min = 0.8             # 假日志间隔（秒）
log_interval_max = 1.5
log_style = "agent"                # agent | vite | npm | git（伪装日志风格，均只输出英文）
status_line = "minimal"            # minimal | full
boss_key = "b"                     # 老板键
full_hide_chinese = true           # 老板模式下过滤 CJK 字符

[theme]
log_level_color = true             # 日志级别着色（INFO/WARN/OK）
reader_color = "gray"              # 阅读区颜色
accent = "green"

[progress]
file = ".fish_progress.json"
autosave_on_page = true            # 翻页即保存进度；false 时仅退出保存
"""


class ConfigError(ValueError):
    """Raised when the config file contains invalid values."""


def snap_spacing(value: float) -> float:
    """Round a spacing value onto the SPACING_STEP grid.

    Keeps hand-written configs comparable with the values the settings menu
    cycles through, so the menu never gets stuck on an off-grid value.
    """
    steps = int((float(value) + SPACING_STEP / 2) // SPACING_STEP)
    return float(round(steps * SPACING_STEP, 2))


def _validate_spacing(field: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigError(f"reader.{field} must be a number, got {value!r}")
    number = float(value)
    if not SPACING_MIN <= number <= SPACING_MAX:
        raise ConfigError(
            f"reader.{field} must be between {SPACING_MIN:g} and {SPACING_MAX:g}, "
            f"got {value!r}"
        )
    return snap_spacing(number)


def _deep_merge(base: dict, override: dict) -> dict:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if key not in merged:
            continue  # ignore unknown keys
        if isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _validate(raw: dict) -> None:
    reader = raw["reader"]
    disguise = raw["disguise"]
    books = raw["books"]

    if reader["font_size"] not in FONT_SIZES:
        raise ConfigError(
            f"reader.font_size must be one of {FONT_SIZES}, got {reader['font_size']!r}"
        )
    if reader["novel_style"] not in NOVEL_STYLES:
        raise ConfigError(
            f"reader.novel_style must be one of {NOVEL_STYLES}, got {reader['novel_style']!r}"
        )
    if reader["reader_position"] not in READER_POSITIONS:
        raise ConfigError(
            "reader.reader_position must be one of "
            f"{READER_POSITIONS}, got {reader['reader_position']!r}"
        )

    width = reader["reader_width"]
    if isinstance(width, str):
        if not width.endswith("%"):
            raise ConfigError(
                f"reader.reader_width must be a percentage like '30%' or an integer "
                f"column count, got {width!r}"
            )
        try:
            pct = int(width[:-1])
        except ValueError:
            raise ConfigError(f"invalid reader.reader_width: {width!r}") from None
        if not READER_WIDTH_MIN_PCT <= pct <= READER_WIDTH_MAX_PCT:
            raise ConfigError(
                f"reader.reader_width percentage must be between "
                f"{READER_WIDTH_MIN_PCT}% and {READER_WIDTH_MAX_PCT}%"
            )
    elif isinstance(width, int):
        if width < 8:
            raise ConfigError(f"reader.reader_width columns must be >= 8, got {width}")
    else:
        raise ConfigError(f"invalid reader.reader_width: {width!r}")

    for field in ("line_spacing", "paragraph_spacing"):
        reader[field] = _validate_spacing(field, reader[field])

    lo = float(disguise["log_interval_min"])
    hi = float(disguise["log_interval_max"])
    if lo <= 0 or hi < lo:
        raise ConfigError(
            "disguise.log_interval_min / log_interval_max must satisfy 0 < min <= max"
        )
    if disguise["status_line"] not in STATUS_LINES:
        raise ConfigError(
            f"disguise.status_line must be one of {STATUS_LINES}"
        )
    log_style = disguise["log_style"]
    if log_style == "english":
        disguise["log_style"] = "agent"  # legacy value; every style is English-only
        log_style = "agent"
    if log_style not in LOG_STYLES:
        raise ConfigError(f"disguise.log_style must be one of {LOG_STYLES}")
    boss = disguise["boss_key"]
    if not isinstance(boss, str) or len(boss) != 1 or not boss.isprintable():
        raise ConfigError(f"disguise.boss_key must be a single printable character")

    exts = books["extensions"]
    if isinstance(exts, (list, tuple)) and exts:
        for e in exts:
            if not isinstance(e, str) or not e.strip():
                raise ConfigError(
                    f"books.extensions entries must be strings like '.txt', got {e!r}"
                )
        books["extensions"] = [
            e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}"
            for e in exts
        ]
    else:
        raise ConfigError("books.extensions must be a non-empty list")


@dataclass
class Config:
    """Validated effective configuration."""

    raw: dict
    path: Path
    root: Path  # project root; relative scan dirs resolve against it

    # -- convenience accessors -------------------------------------------

    @property
    def books(self) -> dict:
        return self.raw["books"]

    @property
    def reader(self) -> dict:
        return self.raw["reader"]

    @property
    def disguise(self) -> dict:
        return self.raw["disguise"]

    @property
    def theme(self) -> dict:
        return self.raw["theme"]

    @property
    def progress(self) -> dict:
        return self.raw["progress"]

    def scan_dirs(self) -> list[Path]:
        out = []
        for d in self.books["scan_dirs"]:
            p = Path(d).expanduser()
            if not p.is_absolute():
                p = self.root / p
            out.append(p)
        return out

    def extensions(self) -> tuple[str, ...]:
        return tuple(self.books["extensions"])

    def reader_width_fraction(self) -> float:
        """Reader pane width as a fraction of terminal width (0..1)."""
        width = self.reader["reader_width"]
        if isinstance(width, str) and width.endswith("%"):
            return int(width[:-1]) / 100.0
        # fixed columns: approximate as fraction of a typical 100-col terminal
        return max(0.2, min(0.5, int(width) / 100.0))

    def reader_width_columns(self, terminal_cols: int) -> int:
        width = self.reader["reader_width"]
        cols = int(width) if isinstance(width, int) else int(terminal_cols * self.reader_width_fraction())
        return max(1, min(cols, terminal_cols - 1))

    def effective_spacing(self) -> tuple[float, float]:
        """(line_spacing, paragraph_spacing) after font_size mapping.

        A non-zero explicit value in *either* field overrides the font_size
        mapping for both (0 means "follow font_size").
        """
        ls = float(self.reader.get("line_spacing", 0))
        ps = float(self.reader.get("paragraph_spacing", 0))
        if ls or ps:
            return (ls, ps)
        base_ls, base_ps = FONT_SIZE_SPACING[self.reader["font_size"]]
        return (base_ls, base_ps)

    @property
    def novel_style(self) -> str:
        return self.reader["novel_style"]

    @property
    def boss_key(self) -> str:
        return self.disguise["boss_key"]

    @property
    def agent_name(self) -> str:
        return self.disguise["agent_name"]

    @property
    def agent_version(self) -> str:
        return self.disguise["agent_version"]

    def log_interval_range(self) -> tuple[float, float]:
        return (
            float(self.disguise["log_interval_min"]),
            float(self.disguise["log_interval_max"]),
        )

    def progress_path(self) -> Path:
        p = Path(self.progress["file"]).expanduser()
        return p if p.is_absolute() else self.root / p

    def autosave_on_page(self) -> bool:
        return bool(self.progress.get("autosave_on_page", True))


def load_config(
    path: Path,
    project_root: Path | None = None,
    create_if_missing: bool = True,
) -> Config:
    """Load fish.toml, generate a default file when missing, validate."""
    path = Path(path)
    if not path.exists():
        if not create_if_missing:
            return Config(raw=copy.deepcopy(DEFAULTS), path=path, root=project_root or path.parent)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(DEFAULT_CONFIG_TEXT, encoding="utf-8")
        except OSError as exc:
            raise ConfigError(f"cannot create default config {path}: {exc}") from exc

    try:
        with open(path, "rb") as fh:
            user = tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc

    merged = _deep_merge(DEFAULTS, user)
    _validate(merged)
    root = project_root or path.parent
    return Config(raw=merged, path=Path(path), root=root)


# -- in-place config updates (used by the in-app settings menu) ---------------

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def _format_toml_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        # whole numbers stay integral so the file reads like a hand-written one
        return str(int(value)) if float(value).is_integer() else str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_format_toml_value(v) for v in value) + "]"
    raise ConfigError(f"cannot write value of type {type(value).__name__}")


def _trailing_comment(text: str) -> str:
    """Return the '# comment' part of a TOML value (quotes-aware), or ''."""
    in_str = False
    for idx, ch in enumerate(text):
        if ch == '"':
            in_str = not in_str
        elif ch == "#" and not in_str:
            start = idx - 1 if idx > 0 and text[idx - 1] == " " else idx
            return text[start:]
    return ""


def _replace_in_section(
    lines: list[str], section: str, values: dict[str, object]
) -> list[str]:
    """Return a new list of lines with key=value pairs updated in `section`.

    Comments and other keys are preserved; missing keys are appended at the
    end of the section; a missing section is appended at the end of the file.
    """
    section_idx = next(
        (i for i, ln in enumerate(lines) if _SECTION_RE.match(ln) and _SECTION_RE.match(ln).group(1).strip() == section),
        None,
    )
    out = list(lines)
    if section_idx is None:
        if out and not out[-1].endswith("\n"):
            out.append("\n")
        out.append(f"\n[{section}]\n")
        for key, value in values.items():
            out.append(f"{key} = {_format_toml_value(value)}\n")
        return out

    end = next(
        (j for j in range(section_idx + 1, len(out)) if _SECTION_RE.match(out[j])),
        len(out),
    )
    for key, value in values.items():
        pattern = re.compile(rf"^(\s*){re.escape(key)}(\s*=\s*)(.*?)(\r?\n?)$")
        found = False
        for j in range(section_idx + 1, end):
            m = pattern.match(out[j])
            if m:
                indent, eq, old_value, newline = m.groups()
                comment = _trailing_comment(old_value)
                out[j] = f"{indent}{key}{eq}{_format_toml_value(value)}{comment}{newline}"
                found = True
                break
        if not found:
            out.insert(end, f"{key} = {_format_toml_value(value)}\n")
            end += 1
    return out


def apply_toml_update(path: Path, section: str, values: dict[str, object]) -> None:
    """Rewrite a few key=value pairs of `section` in place and atomically.

    Preserves comments and unrelated keys, validates the result with tomllib
    before touching the file, and raises ConfigError on any problem (the file
    is left untouched).
    """
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigError(f"cannot read {path}: {exc}") from exc
    lines = text.splitlines(keepends=True)
    updated = _replace_in_section(lines, section, values)
    try:
        tomllib.loads("".join(updated))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"refusing to write invalid toml to {path}: {exc}") from exc
    tmp: str | None = None
    try:
        fd, tmp = tempfile.mkstemp(
            dir=path.parent, prefix=path.name + ".", suffix=".tmp"
        )
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write("".join(updated))
        os.replace(tmp, path)
    except OSError as exc:
        raise ConfigError(f"cannot write {path}: {exc}") from exc
    finally:
        if tmp and os.path.exists(tmp):
            os.unlink(tmp)