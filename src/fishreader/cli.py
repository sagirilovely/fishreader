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
        description="Terminal novel reader disguised as a coding agent and web documentation.",
        epilog="DEFAULT: reads fish.toml from the project root.",
    )
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="path to a fish.toml config file (default: <project>/fish.toml)",
    )
    parser.add_argument(
        "--no-web",
        action="store_true",
        help="disable the background web documentation disguise server",
    )
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="run only the web disguise server without launching the terminal TUI",
    )
    parser.add_argument(
        "--port",
        type=int,
        metavar="PORT",
        help="port for the web documentation server (default: 8080)",
    )
    parser.add_argument(
        "--theme",
        choices=["vue", "react", "rust", "python"],
        help="web documentation theme (default: from fish.toml or 'vue')",
    )
    return parser


def _project_root() -> Path:
    """Resolve the project root (where books/ and fish.toml live).

    In a source/editable install the package lives at <root>/src/fishreader,
    so the repo marker (run.py) identifies the root. A plain site-packages
    install has no repo marker: fall back to the invocation directory, which
    is where the user is expected to keep their books/ folder.
    """
    repo = Path(__file__).resolve().parent.parent.parent
    if (repo / "run.py").is_file():
        return repo
    return Path.cwd()


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

    root = _project_root()
    cfg_path = Path(args.config).expanduser() if args.config else root / "fish.toml"
    try:
        cfg = config_mod.load_config(
            cfg_path, project_root=root, create_if_missing=True
        )
    except config_mod.ConfigError as exc:
        print(f"[fishreader] config error: {exc}", file=sys.stderr)
        return 1

    # Apply CLI overrides
    if args.no_web:
        cfg.raw.setdefault("web", {})["enabled"] = False
    if args.port:
        cfg.raw.setdefault("web", {})["port"] = args.port
    if args.theme:
        cfg.raw.setdefault("web", {})["theme"] = args.theme

    if args.web_only:
        import time
        import webbrowser
        from fishreader.web.server import WebDisguiseServer

        server = WebDisguiseServer(
            cfg, root, port=args.port or cfg.web.get("port", 8080)
        )
        url = server.start()
        candidates = server.get_candidates()
        print(f"[fishreader] Web Documentation Disguise Server started: {url}")
        print(
            f"[fishreader] Active Theme: {cfg.web.get('theme', 'vue')} | Discovered Books: {len(candidates)}"
        )
        print("[fishreader] Press Ctrl+C to exit.")
        if cfg.web_auto_open:
            webbrowser.open(url)
        try:
            while server.is_running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n[fishreader] Stopping server...")
            server.stop()
        return 0

    from fishreader.app import FishApp

    app = FishApp(config=cfg, project_root=root)
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())