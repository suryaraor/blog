#!/usr/bin/env python3
"""
Auto-create branded 1280×720 OG thumbnails from existing post hero images.

For each post that has an image: front matter field but no matching
thumbnail in assets/images/thumbnails/, crop/resize the source image
and save it as a webp thumbnail.

Requires: Pillow  (pip install Pillow)
"""
import re
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow", file=sys.stderr)
    sys.exit(1)

BLOG_DIR = Path(__file__).parent.parent
POSTS_DIR = BLOG_DIR / "_posts"
THUMB_DIR = BLOG_DIR / "assets" / "images" / "thumbnails"
THUMB_DIR.mkdir(parents=True, exist_ok=True)

THUMB_W, THUMB_H = 1280, 720
FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

created = 0
for post_path in sorted(POSTS_DIR.glob("*.md")):
    text = post_path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        continue
    front = m.group(1)
    img_m = re.search(r'^image:\s*(\S+)', front, re.MULTILINE)
    if not img_m:
        continue

    img_url = img_m.group(1).strip("\"'")
    img_rel = img_url.lstrip("/")
    src_path = BLOG_DIR / img_rel
    if not src_path.exists():
        continue

    stem = post_path.stem
    out_path = THUMB_DIR / (stem + ".webp")
    if out_path.exists():
        continue

    try:
        with Image.open(src_path) as img:
            # Smart crop to 16:9
            img_w, img_h = img.size
            target_ratio = THUMB_W / THUMB_H
            src_ratio = img_w / img_h
            if src_ratio > target_ratio:
                new_w = int(img_h * target_ratio)
                left = (img_w - new_w) // 2
                img = img.crop((left, 0, left + new_w, img_h))
            elif src_ratio < target_ratio:
                new_h = int(img_w / target_ratio)
                top = (img_h - new_h) // 2
                img = img.crop((0, top, img_w, top + new_h))
            img = img.resize((THUMB_W, THUMB_H), Image.LANCZOS)
            img = img.convert("RGB")
            img.save(out_path, "webp", quality=82, method=6)
            created += 1
            print(f"  {out_path.name}")
    except Exception as e:
        print(f"  SKIP {src_path.name}: {e}", file=sys.stderr)

print(f"\nCreated {created} thumbnail(s) in {THUMB_DIR}")
