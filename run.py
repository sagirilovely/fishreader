#!/usr/bin/env python3
"""Bootstrap entry point: python run.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main() -> int:
    from fishreader.cli import main as cli_main

    return cli_main()


if __name__ == "__main__":
    raise SystemExit(main())