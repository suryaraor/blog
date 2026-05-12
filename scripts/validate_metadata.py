#!/usr/bin/env python3
"""
Validate front matter metadata across all _posts/*.md files.

Checks every post for:
  - Required fields: title, date, difficulty
  - Recommended fields: description, image (warn, not fail)
  - OG/Twitter readiness: title + description together

Usage:
    python scripts/validate_metadata.py
    Exit code 1 if any required field is missing.
"""
import re
import sys
from pathlib import Path

import yaml

BLOG_DIR = Path(__file__).parent.parent
POSTS_DIR = BLOG_DIR / "_posts"

FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

REQUIRED_FIELDS = ["title", "date", "difficulty"]
RECOMMENDED_FIELDS = ["description", "image"]
VALID_DIFFICULTY = {"Beginner", "Intermediate", "Advanced"}

errors: list[tuple[str, str]] = []
warnings: list[tuple[str, str]] = []

for post_path in sorted(POSTS_DIR.glob("*.md")):
    text = post_path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        errors.append((post_path.name, "missing or malformed YAML front matter"))
        continue

    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        errors.append((post_path.name, f"YAML parse error: {e}"))
        continue

    # Skip noindex posts (unlisted/reverted)
    if str(fm.get("robots", "")).strip().lower().startswith("noindex"):
        continue

    for field in REQUIRED_FIELDS:
        if not fm.get(field):
            errors.append((post_path.name, f"missing required field: {field}"))

    if fm.get("difficulty") and fm["difficulty"] not in VALID_DIFFICULTY:
        errors.append((post_path.name, f"invalid difficulty '{fm['difficulty']}' — must be one of {sorted(VALID_DIFFICULTY)}"))

    for field in RECOMMENDED_FIELDS:
        if not fm.get(field):
            warnings.append((post_path.name, f"missing recommended field: {field}"))

    # OG/Twitter readiness
    if not fm.get("description"):
        warnings.append((post_path.name, "no description — Open Graph and Twitter cards will fall back to site description"))

checked = len(list(POSTS_DIR.glob("*.md")))

if warnings:
    print(f"Metadata warnings ({len(warnings)}):\n")
    for fname, msg in warnings:
        print(f"  {fname}: {msg}")
    print()

if errors:
    print(f"Metadata errors ({len(errors)}) in {checked} posts:\n")
    for fname, msg in errors:
        print(f"  {fname}: {msg}")
    sys.exit(1)
else:
    if warnings:
        print(f"Checked {checked} posts — {len(warnings)} warning(s), 0 errors.")
    else:
        print(f"All {checked} posts pass metadata validation.")
