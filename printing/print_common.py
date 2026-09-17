"""Shared printing utilities – single place that talks to CUPS."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# A4 at 300 DPI
PAGE_WIDTH = 2480
PAGE_HEIGHT = 3508

BASE = os.environ.get("PRINTING_BASE", "/opt/home-server/printing")
if not os.path.isdir(BASE):
    BASE = "/app"

OUTPUT_DIR = Path(BASE) / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

PRINTER = os.environ.get("CUPS_PRINTER", "Skrivare")

FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def print_files(paths: list[Path | str]) -> None:
    """Send one or more files to the CUPS printer."""
    if not paths:
        raise ValueError("No files to print")

    for path in paths:
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"File not found: {p}")
        print(f"Skriver ut: {p}")
        subprocess.run(
            ["lp", "-d", PRINTER, str(p)],
            check=True,
        )
