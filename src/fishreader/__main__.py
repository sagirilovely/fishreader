"""python -m fishreader entry point."""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fishreader.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())