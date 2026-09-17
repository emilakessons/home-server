#!/usr/bin/env python3
"""Search, render and print a coloring page."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import requests
from ddgs import DDGS
from PIL import Image, ImageEnhance, ImageOps

from print_common import OUTPUT_DIR, PAGE_HEIGHT, PAGE_WIDTH, print_files

BASE = Path(__file__).resolve().parent
if not (BASE / "downloads").exists() and Path("/app").is_dir():
    BASE = Path("/app")

DOWNLOAD_DIR = BASE / "downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


def search_coloring_page(subject: str) -> str | None:
    query = f"{subject} målarbild coloring page"
    print("Söker:", query)

    with DDGS() as ddgs:
        results = list(ddgs.images(query, max_results=15))

    if not results:
        print("Inga bilder hittades")
        return None

    for result in results:
        url = result.get("image") or result.get("url")
        if not url:
            continue

        lower = url.lower()
        if not any(ext in lower for ext in (".jpg", ".jpeg", ".png", ".webp")):
            continue
        if any(
            bad in lower
            for bad in (
                "teacherspayteachers",
                "thumbitem",
                "sprite",
                "favicon",
                "logo",
            )
        ):
            continue

        width = int(result.get("width") or 0)
        height = int(result.get("height") or 0)
        if width and height and (width < 400 or height < 400):
            continue

        print("Bild:", url)
        print("Titel:", (result.get("title") or "")[:80])
        return url

    fallback = results[0].get("image") or results[0].get("url")
    print("Fallback-bild:", fallback)
    return fallback


def download_image(url: str, dest: Path) -> None:
    print("Hämtar:", url)
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)


def create_coloring_page(image_file: Path, output_file: Path) -> None:
    print("Bearbetar bild")
    image = Image.open(image_file).convert("RGB")

    margin = 0.05
    max_width = int(PAGE_WIDTH * (1 - 2 * margin))
    max_height = int(PAGE_HEIGHT * (1 - 2 * margin))

    scale = min(max_width / image.width, max_height / image.height)
    new_size = (
        max(1, int(image.width * scale)),
        max(1, int(image.height * scale)),
    )
    image = image.resize(new_size, Image.Resampling.LANCZOS)
    print(f"Skalade till {image.width}x{image.height} (faktor {scale:.2f})")

    canvas = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    x = (PAGE_WIDTH - image.width) // 2
    y = (PAGE_HEIGHT - image.height) // 2
    canvas.paste(image, (x, y))

    gray = ImageOps.grayscale(canvas)
    gray = ImageEnhance.Contrast(gray).enhance(2.5)
    bw = gray.point(lambda pixel: 0 if pixel < 180 else 255)
    bw.save(output_file, "PNG")


def run(subject: str) -> None:
    subject = subject.strip()
    if not subject:
        raise SystemExit("Motiv saknas")

    safe_name = re.sub(r"[^\w\-]+", "_", subject, flags=re.UNICODE).strip("_").lower()
    image_file = DOWNLOAD_DIR / f"{safe_name}.jpg"
    output_file = OUTPUT_DIR / f"{safe_name}_coloring.png"

    print(f"Motiv: {subject}")

    image_url = search_coloring_page(subject)
    if not image_url:
        raise SystemExit("Ingen bild hittades")

    download_image(image_url, image_file)
    create_coloring_page(image_file, output_file)
    print_files([output_file])
    print("KLAR!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Användning: python print_coloring_page.py <motiv>")
        sys.exit(1)
    run(" ".join(sys.argv[1:]))
