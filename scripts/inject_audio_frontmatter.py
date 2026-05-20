#!/usr/bin/env python3
"""
Auto-detect WAV files for posts and inject audio: front matter.

Matches WAV files in assets/audio/posts/ to _posts/ markdown files by
comparing the slug portion (after stripping the date prefix).
"""
import re
import os
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "github_push" / "blog"
POSTS_DIR = BLOG_DIR / "_posts"
AUDIO_DIR = BLOG_DIR / "assets" / "audio" / "posts"
AUDIO_URL_BASE = "/assets/audio/posts/"

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
DATE_PREFIX_RE = re.compile(r'^\d{4}-\d{2}-\d{2}-')


def slug_from_filename(name: str) -> str:
    """Strip date prefix and extension."""
    name = DATE_PREFIX_RE.sub("", name)
    return re.sub(r'\.[^.]+$', '', name)


def truncated_match(wav_slug: str, post_slug: str) -> bool:
    """WAV filenames may be truncated; check if one starts with the other."""
    short = min(len(wav_slug), len(post_slug))
    return wav_slug[:short] == post_slug[:short]


# Build WAV lookup: slug -> filename
wav_by_slug: dict[str, str] = {}
for wav in AUDIO_DIR.glob("*.wav"):
    slug = slug_from_filename(wav.name)
    wav_by_slug[slug] = wav.name

updated = 0
for post_path in sorted(POSTS_DIR.glob("*.md")):
    text = post_path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        continue
    front = m.group(1)
    if "audio:" in front:
        continue

    post_slug = slug_from_filename(post_path.stem)

    # Try exact match first, then truncated match
    matched_wav = wav_by_slug.get(post_slug)
    if not matched_wav:
        for wav_slug, wav_name in wav_by_slug.items():
            if truncated_match(wav_slug, post_slug):
                matched_wav = wav_name
                break

    if not matched_wav:
        continue

    audio_url = AUDIO_URL_BASE + matched_wav
    new_front = front + f"\naudio: {audio_url}"
    new_text = f"---\n{new_front}\n---\n{text[m.end():]}"
    post_path.write_text(new_text, encoding="utf-8")
    updated += 1
    print(f"  {post_path.name} -> {audio_url}")

print(f"\nAdded audio: front matter to {updated} posts.")
