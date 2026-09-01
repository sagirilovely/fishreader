"""Configuration loading, validation and default file generation.

Config format is TOML (fish.toml), loaded with tomllib and deep-merged
over DEFAULTS. Unknown user keys are ignored.
"""

from __future__ import annotations

import copy
import tomllib
from dataclasses import dataclass
from pathlib import Path

# Reader width is validated between these bounds when given as a percentage.
READER_WIDTH_MIN_PCT = 25
READER_WIDTH_MAX_PCT = 40

FONT_SIZES = ("small", "medium", "large")
NOVEL_STYLES = ("markdown", "comment", "docstring")
READER_POSITIONS = ("right", "bottom")
STATUS_LINES = ("minimal", "full")

# font_size -> (line_spacing, paragraph_spacing)
FONT_SIZE_SPACING: dict[str, tuple[int, int]] = {
    "small": (0, 0),
    "medium": (0, 1),
    "large": (1, 2),
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
        "log_style": "english",
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
font_size = "medium"               # small | medium | large（显示密度档位，不改终端真实字号）
line_spacing = 0                   # 每个逻辑行后追加的空行数；设为非 0 时覆盖 font_size 的映射
paragraph_spacing = 0              # 段落后追加的空行数；设为非 0 时覆盖 font_size 的映射
reader_width = "30%"               # 阅读区占终端宽度百分比（25%-40%）或固定列数
reader_position = "right"          # right | bottom（本版本使用 right）
novel_style = "markdown"           # markdown | comment | docstring
resume_last = true                 # 启动时自动续读上次书籍

[disguise]
agent_name = "CodeAgent"
agent_version = "0.4.2"
log_interval_min = 0.8             # 假日志间隔（秒）
log_interval_max = 1.5
log_style = "english"              # 只允许英文日志
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
        value = reader[field]
        if not isinstance(value, int) or not 0 <= value <= 2:
            raise ConfigError(f"reader.{field} must be an integer 0-2")

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

    def effective_spacing(self) -> tuple[int, int]:
        """(line_spacing, paragraph_spacing) after font_size mapping.

        Non-zero explicit values override the font_size mapping.
        """
        ls = int(self.reader.get("line_spacing", 0))
        ps = int(self.reader.get("paragraph_spacing", 0))
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