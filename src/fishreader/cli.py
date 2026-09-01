"""CLI bootstrap: dependency checks, config loading, app launch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _check_dependencies() -> tuple[list[str], bool]:
    """Return (missing_pip_names, mobi_available)."""
    missing: list[str] = []
    for mod, pip in (
        ("textual", "textual"),
        ("bs4", "beautifulsoup4"),
        ("charset_normalizer", "charset-normalizer"),
    ):
        try:
            __import__(mod)
        except ImportError:
            missing.append(pip)

    mobi_ok = False
    if "mobi" not in missing:
        try:
            __import__("mobi")
            mobi_ok = True
        except ImportError:
            mobi_ok = False
    return missing, mobi_ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fishreader",
        description="Terminal novel reader disguised as a coding agent.",
        epilog="DEFAULT: reads fish.toml from the project root.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="path to a fish.toml config file (default: <project>/fish.toml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if sys.version_info < (3, 11):
        print(
            f"[fishreader] Python 3.11+ required (found {sys.version.split()[0]})",
            file=sys.stderr,
        )
        return 1

    missing, mobi_ok = _check_dependencies()
    if missing:
        print(
            "[fishreader] missing dependencies: "
            + ", ".join(missing)
            + "\n  install with: python -m pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1
    if not mobi_ok:
        print(
            "[fishreader] warning: 'mobi' package not available; "
            ".mobi books will be listed as unsupported "
            "(pip install mobi to enable)",
            file=sys.stderr,
        )

    from fishreader import config as config_mod

    root = Path(__file__).resolve().parent.parent  # project root (src/fishreader/cli.py)
    cfg_path = Path(args.config).expanduser() if args.config else root / "fish.toml"
    try:
        cfg = config_mod.load_config(
            cfg_path, project_root=root, create_if_missing=True
        )
    except config_mod.ConfigError as exc:
        print(f"[fishreader] config error: {exc}", file=sys.stderr)
        return 1

    from fishreader.app import FishApp

    app = FishApp(config=cfg, project_root=root)
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())