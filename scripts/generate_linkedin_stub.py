#!/usr/bin/env python3
"""
Auto-generate LinkedIn post stubs for new blog articles.

For each _posts/*.md file that doesn't already have a matching stub in
linkedin_stubs/, create a ready-to-edit .txt file with a draft post.

Usage:
    python generate_linkedin_stub.py [--all]

Without --all, only generates stubs for posts published in the last 3 days.
"""
import re
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent / "github_push" / "blog"
POSTS_DIR = BLOG_DIR / "_posts"
STUBS_DIR = Path(__file__).parent.parent / "linkedin_stubs"
STUBS_DIR.mkdir(exist_ok=True)

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
SITE_URL = "https://suryaraor.github.io/blog"

all_posts = "--all" in sys.argv
cutoff = datetime.now(tz=timezone.utc) - timedelta(days=3)

created = 0
for post_path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
    text = post_path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        continue

    front = m.group(1)
    title_m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    date_m = re.search(r'^date:\s*(\S+)', front, re.MULTILINE)
    desc_m = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)

    title = title_m.group(1).strip('"\'') if title_m else post_path.stem
    date_str = date_m.group(1) if date_m else ""
    description = desc_m.group(1).strip('"\'') if desc_m else ""

    stub_name = post_path.stem + ".txt"
    stub_path = STUBS_DIR / stub_name

    if stub_path.exists():
        continue

    if not all_posts and date_str:
        try:
            post_date = datetime.fromisoformat(date_str[:10])
            if post_date.replace(tzinfo=timezone.utc) < cutoff:
                continue
        except ValueError:
            pass

    post_url = f"{SITE_URL}/{post_path.stem.replace('-', '/', 2).replace('-', '-', 1)}/"
    body = text[m.end():]
    first_para = ""
    for line in body.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('---'):
            first_para = re.sub(r'\*+([^*]+)\*+', r'\1', line)
            first_para = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', first_para)
            first_para = first_para[:280]
            break

    hook = first_para or description or "Read on to find out."

    stub_content = textwrap.dedent(f"""\
        LinkedIn Post Draft — {title}
        {"=" * 60}
        Date: {date_str}
        URL:  {post_url}

        --- DRAFT (edit before posting) ---

        {title}

        {hook}

        🔗 Full article: {post_url}

        #TechBlog #SoftwareEngineering #Engineering
        """)

    stub_path.write_text(stub_content, encoding="utf-8")
    created += 1
    print(f"  Created: {stub_name}")

print(f"\nGenerated {created} LinkedIn stub(s) in {STUBS_DIR}")
