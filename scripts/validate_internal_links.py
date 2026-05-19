#!/usr/bin/env python3
"""
Validate all internal links in _posts/*.md files.

Checks:
  - Markdown links [text](/path) that start with '/'
  - Looks for matching _posts file or static page

Usage:
    python validate_internal_links.py
    Exit code 1 if broken links found.
"""
import re
import sys
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent
POSTS_DIR = BLOG_DIR / "_posts"

LINK_RE = re.compile(r'\[([^\]]+)\]\((/[^)]+)\)')
FRONT_MATTER_RE = re.compile(r'^---\s*\n.*?\n---\s*\n', re.DOTALL)

# Build set of valid post URLs from filenames
# Jekyll permalink format: /:year/:month/:day/:title/
POST_URLS: set[str] = set()
for p in POSTS_DIR.glob("*.md"):
    # Extract date and slug
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$', p.name)
    if m:
        y, mo, d, slug = m.groups()
        POST_URLS.add(f"/{y}/{mo}/{d}/{slug}/")
        POST_URLS.add(f"/{y}/{mo}/{d}/{slug}")

# Static pages that exist
STATIC_PAGES = {"/", "/about", "/about/", "/search", "/search/",
                "/tags", "/tags/", "/archive", "/archive/",
                "/feed.xml", "/sitemap.xml", "/manifest.json"}

broken: list[tuple[str, int, str, str]] = []

_arg_files = [f for f in sys.argv[1:] if f.endswith(".md")]
if _arg_files:
    _resolved = []
    for f in _arg_files:
        p = Path(f)
        if not p.is_absolute():
            p = BLOG_DIR / f
        if p.exists():
            _resolved.append(p)
    check_paths = sorted(_resolved)
    _scope = f"{len(check_paths)} changed post(s)"
else:
    check_paths = sorted(POSTS_DIR.glob("*.md"))
    _scope = f"{len(check_paths)} posts"

for post_path in check_paths:
    text = post_path.read_text(encoding="utf-8")
    # Strip front matter before scanning
    body = FRONT_MATTER_RE.sub("", text, count=1)
    for i, line in enumerate(body.splitlines(), 1):
        for link_text, url in LINK_RE.findall(line):
            # Only check internal links (skip anchors, external)
            if url.startswith("//") or url.startswith("http"):
                continue
            path_only = url.split("#")[0].split("?")[0]
            if path_only in POST_URLS or path_only in STATIC_PAGES:
                continue
            # Allow category paths
            if re.match(r'^/[a-z0-9-]+/?$', path_only):
                continue
            broken.append((post_path.name, i, link_text, url))

if broken:
    print(f"Found {len(broken)} broken internal link(s):\n")
    for fname, lineno, text, url in broken:
        print(f"  {fname}:{lineno}  [{text}]({url})")
    sys.exit(1)
else:
    print(f"All internal links OK (checked {_scope}).")
