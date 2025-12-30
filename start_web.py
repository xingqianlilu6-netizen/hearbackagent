"""Helper script to launch the hearback web UI without installing the package.

Usage:
    python start_web.py

This ensures the project root is on sys.path so that hearback_agent.web can be
imported even when the package is not installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hearback_agent.web import serve  # noqa: E402


def main() -> None:
    serve()


if __name__ == "__main__":
    main()
