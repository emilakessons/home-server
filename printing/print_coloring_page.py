#!/usr/bin/env python3

import sys
import os
import re
import requests

from ddgs import DDGS
from PIL import Image, ImageOps, ImageEnhance


if len(sys.argv) < 2:
    print("Användning: python print_coloring_page.py <motiv>")
    sys.exit(1)


subject = " ".join(sys.argv[1:]).strip()
safe_name = re.sub(r"[^\w\-]+", "_", subject, flags=re.UNICODE).strip("_").lower()


BASE = os.environ.get("PRINTING_BASE", "/opt/home-server/printing")
if not os.path.isdir(BASE):
    BASE = "/app"

DOWNLOAD_DIR = f"{BASE}/downloads"
OUTPUT_DIR = f"{BASE}/output"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


image_file = f"{DOWNLOAD_DIR}/{safe_name}.jpg"
output_file = f"{OUTPUT_DIR}/{safe_name}_coloring.png"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


def search_coloring_page(subject):
    """Hitta första bra målarbild via bildsökning."""

    query = f"{subject} målarbild coloring page"

    print("Söker:", query)

    results = []
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

        # Hoppa över uppenbara thumbnails / paywall-CDN
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

    # Fallback: första träffen även om den är liten
    fallback = results[0].get("image") or results[0].get("url")
    print("Fallback-bild:", fallback)
    return fallback


def download_image(url):
    print("Hämtar:", url)

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    with open(image_file, "wb") as f:
        f.write(response.content)


def create_coloring_page():
    print("Bearbetar bild")

    image = Image.open(image_file).convert("RGB")

    # A4 300 DPI, liten marginal så bilden inte går kant i kant
    page_width = 2480
    page_height = 3508
    margin = 0.05
    max_width = int(page_width * (1 - 2 * margin))
    max_height = int(page_height * (1 - 2 * margin))

    # Skala upp eller ner så att bilden fyller sidan (behåll proportioner)
    scale = min(max_width / image.width, max_height / image.height)
    new_size = (
        max(1, int(image.width * scale)),
        max(1, int(image.height * scale)),
    )
    image = image.resize(new_size, Image.Resampling.LANCZOS)

    print(f"Skalade till {image.width}x{image.height} (faktor {scale:.2f})")

    canvas = Image.new("RGB", (page_width, page_height), "white")

    x = (page_width - image.width) // 2
    y = (page_height - image.height) // 2

    canvas.paste(image, (x, y))

    gray = ImageOps.grayscale(canvas)
    gray = ImageEnhance.Contrast(gray).enhance(2.5)

    bw = gray.point(lambda pixel: 0 if pixel < 180 else 255)
    bw.save(output_file, "PNG")


def print_image():
    print("Skriver ut PNG")
    os.system(f'lp -d "Skrivare" "{output_file}"')


print(f"Motiv: {subject}")

image_url = search_coloring_page(subject)

if not image_url:
    raise SystemExit("Ingen bild hittades")

download_image(image_url)
create_coloring_page()
print_image()

print("KLAR!")