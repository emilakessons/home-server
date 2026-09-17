#!/usr/bin/env python3
"""Render and print a shopping list as A4 pages."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from print_common import (
    FONT_BOLD,
    FONT_REGULAR,
    OUTPUT_DIR,
    PAGE_HEIGHT,
    PAGE_WIDTH,
    print_files,
)

MARGIN = 120
LINE_HEIGHT = 90
CHECKBOX = 44


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    if Path(path).is_file():
        return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def paginate_items(
    items: list[str], first_page_capacity: int, page_capacity: int
) -> list[list[str]]:
    if not items:
        return [[]]
    pages: list[list[str]] = []
    rest = items[:]
    pages.append(rest[:first_page_capacity])
    rest = rest[first_page_capacity:]
    while rest:
        pages.append(rest[:page_capacity])
        rest = rest[page_capacity:]
    return pages


def create_pages(title: str, items: list[str]) -> list[Image.Image]:
    title_font = load_font(72, bold=True)
    date_font = load_font(36)
    item_font = load_font(52)
    header_height = 220
    first_capacity = (PAGE_HEIGHT - MARGIN * 2 - header_height) // LINE_HEIGHT
    page_capacity = (PAGE_HEIGHT - MARGIN * 2 - 60) // LINE_HEIGHT
    pages_data = paginate_items(items, first_capacity, page_capacity)
    total = len(pages_data)
    images: list[Image.Image] = []

    for i, page_items in enumerate(pages_data, start=1):
        img = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        draw = ImageDraw.Draw(img)
        y = MARGIN

        if i == 1:
            draw.text((MARGIN, y), title, fill="black", font=title_font)
            y += 100
            draw.text(
                (MARGIN, y),
                datetime.now().strftime("%Y-%m-%d %H:%M"),
                fill="gray",
                font=date_font,
            )
            y += 80
            draw.line((MARGIN, y, PAGE_WIDTH - MARGIN, y), fill="black", width=2)
            y += 40
        else:
            y += 20

        for item in page_items:
            if y + LINE_HEIGHT > PAGE_HEIGHT - MARGIN:
                break
            x_box = MARGIN
            y_box = y + 8
            draw.rectangle(
                (x_box, y_box, x_box + CHECKBOX, y_box + CHECKBOX),
                outline="black",
                width=3,
            )
            draw.text((x_box + CHECKBOX + 24, y), item, fill="black", font=item_font)
            y += LINE_HEIGHT

        if total > 1:
            draw.text(
                (MARGIN, PAGE_HEIGHT - MARGIN - 40),
                f"Sida {i} av {total}",
                fill="gray",
                font=load_font(32),
            )

        images.append(img)

    return images


def run(title: str, items: list[str]) -> None:
    items = [str(x).strip() for x in items if str(x).strip()]
    if not items:
        raise SystemExit("Inga poster att skriva ut")

    print(f"Skapar inköpslista: {len(items)} poster")
    images = create_pages(title or "Inköpslista", items)

    paths: list[Path] = []
    for i, img in enumerate(images):
        path = OUTPUT_DIR / f"shopping_list_{i + 1}.png"
        img.save(path, "PNG")
        paths.append(path)

    print_files(paths)
    print("KLAR!")


def main() -> None:
    if len(sys.argv) < 2:
        raw = sys.stdin.read()
    else:
        raw = sys.argv[1]

    data = json.loads(raw)
    run(
        str(data.get("title") or "Inköpslista").strip(),
        data.get("items") or [],
    )


if __name__ == "__main__":
    main()
