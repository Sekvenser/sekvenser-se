#!/usr/bin/env python3
"""Resize + convert images to webp before adding them to a post or page.

Images render at ~604px wide (main's 700px max-width, minus main + .card
padding). 1200px covers that at 2x for retina screens without publishing
oversized source photos.

Usage: python3 optimize_image.py assets/photo.jpg [more.jpg ...]
Writes assets/photo.webp alongside the original (never upscales).
"""
import sys
from pathlib import Path

from PIL import Image

TARGET_WIDTH = 1200
QUALITY = 82


def optimize(path):
    path = Path(path)
    img = Image.open(path)
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    if img.width > TARGET_WIDTH:
        height = round(img.height * TARGET_WIDTH / img.width)
        img = img.resize((TARGET_WIDTH, height), Image.LANCZOS)
    out = path.with_suffix(".webp")
    img.save(out, "webp", quality=QUALITY)
    before, after = path.stat().st_size, out.stat().st_size
    print(f"{path.name} -> {out.name}: {before // 1024}KB -> {after // 1024}KB ({img.width}x{img.height})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 optimize_image.py <image> [image ...]")
    for p in sys.argv[1:]:
        optimize(p)
