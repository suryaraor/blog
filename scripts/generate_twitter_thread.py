#!/usr/bin/env python3
"""
Auto-generate Twitter/X thread drafts from blog post key points.

Extracts: title, description, H2/H3 headings, bold phrases, and bullet points.
Formats them as a numbered tweet thread (each tweet ≤ 280 chars).

Output: one .txt file per post in twitter_threads/ directory.

Usage:
    python generate_twitter_thread.py            # only posts from last 7 days
    python generate_twitter_thread.py --all      # all posts without a thread file
"""
import re
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

BLOG_DIR = Path(__file__).parent.parent
POSTS_DIR = BLOG_DIR / "_posts"
THREADS_DIR = BLOG_DIR / "twitter_threads"
THREADS_DIR.mkdir(exist_ok=True)

SITE_URL = "https://suryaraor.github.io/blog"
TWEET_LIMIT = 280
FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)

all_posts = "--all" in sys.argv
cutoff = datetime.now(tz=timezone.utc) - timedelta(days=7)


def strip_markdown(text: str) -> str:
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def fit_tweet(text: str, prefix: str = "", suffix: str = "") -> str:
    available = TWEET_LIMIT - len(prefix) - len(suffix)
    if len(text) <= available:
        return prefix + text + suffix
    wrapped = textwrap.shorten(text, width=available, placeholder="…")
    return prefix + wrapped + suffix


def extract_key_points(body: str) -> list[str]:
    points: list[str] = []
    for line in body.splitlines():
        line = line.strip()
        if not line:
            continue
        # H2/H3 headings → key points
        heading_m = re.match(r'^#{2,3}\s+(.+)', line)
        if heading_m:
            text = strip_markdown(heading_m.group(1))
            if text and len(text) > 4:
                points.append(text)
            continue
        # Bullet points / numbered lists
        bullet_m = re.match(r'^[-*+]\s+(.+)', line)
        if bullet_m:
            text = strip_markdown(bullet_m.group(1))
            if text and len(text) > 10:
                points.append(text)
            continue
        num_m = re.match(r'^\d+[.)]\s+(.+)', line)
        if num_m:
            text = strip_markdown(num_m.group(1))
            if text and len(text) > 10:
                points.append(text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    result: list[str] = []
    for p in points:
        key = p.lower()
        if key not in seen:
            seen.add(key)
            result.append(p)
    return result


def build_thread(title: str, description: str, points: list[str],
                 url: str, tags: list[str]) -> list[str]:
    tweets: list[str] = []

    # Tweet 1: hook
    hook = description or title
    hook_clean = strip_markdown(hook)
    tweets.append(fit_tweet(hook_clean, suffix="\n\nThread 🧵👇"))

    # Tweets 2…N: key points (group short ones together)
    chunk: list[str] = []
    chunk_len = 0

    def flush_chunk(chunk, tweets):
        if not chunk:
            return []
        num = len(tweets) + 1
        prefix = f"{num}/ "
        combined = " • ".join(chunk)
        tweets.append(fit_tweet(combined, prefix=prefix))
        return []

    for pt in points[:12]:  # cap at 12 content tweets
        bullet = f"• {pt}"
        if chunk_len + len(bullet) + 3 > TWEET_LIMIT - 4:
            chunk = flush_chunk(chunk, tweets)
            chunk_len = 0
        chunk.append(bullet)
        chunk_len += len(bullet) + 3

    chunk = flush_chunk(chunk, tweets)

    # Final tweet: CTA + URL + hashtags
    hashtag_str = " ".join(f"#{t.replace(' ', '')}" for t in tags[:4]) if tags else "#Engineering #Tech"
    closing = f"{len(tweets) + 1}/ Read the full post:\n{url}\n\n{hashtag_str}"
    if len(closing) > TWEET_LIMIT:
        closing = f"{len(tweets) + 1}/ Full post → {url}"
    tweets.append(closing)

    return tweets


def post_url_from_path(post_path: Path) -> str:
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})-(.+)\.md$', post_path.name)
    if m:
        y, mo, d, slug = m.groups()
        return f"{SITE_URL}/{y}/{mo}/{d}/{slug}/"
    return SITE_URL


created = 0
for post_path in sorted(POSTS_DIR.glob("*.md"), reverse=True):
    out_path = THREADS_DIR / (post_path.stem + ".txt")
    if out_path.exists():
        continue

    text = post_path.read_text(encoding="utf-8")
    fm_match = FRONT_MATTER_RE.match(text)
    if not fm_match:
        continue

    front = fm_match.group(1)
    body = text[fm_match.end():]

    title_m = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    date_m = re.search(r'^date:\s*(\S+)', front, re.MULTILINE)
    desc_m = re.search(r'^description:\s*["\']?(.*?)["\']?\s*$', front, re.MULTILINE)
    tags_m = re.search(r'^(?:tags|categories):\s*\[([^\]]+)\]', front, re.MULTILINE)

    title = (title_m.group(1).strip('"\'') if title_m else post_path.stem)
    date_str = (date_m.group(1) if date_m else "")
    description = (desc_m.group(1).strip('"\'') if desc_m else "")
    tags_raw = tags_m.group(1) if tags_m else ""
    tags = [t.strip().strip('"\'') for t in tags_raw.split(',')] if tags_raw else []

    if not all_posts and date_str:
        try:
            post_date = datetime.fromisoformat(date_str[:10])
            if post_date.replace(tzinfo=timezone.utc) < cutoff:
                continue
        except ValueError:
            pass

    url = post_url_from_path(post_path)
    points = extract_key_points(body)

    if not points and not description:
        continue

    tweets = build_thread(title, description, points, url, tags)

    lines = [f"Twitter/X Thread Draft — {title}",
             "=" * 60,
             f"Date: {date_str}",
             f"URL:  {url}",
             f"Tweets: {len(tweets)}",
             "",
             "--- DRAFT (edit before posting) ---",
             ""]

    for i, tweet in enumerate(tweets, 1):
        lines.append(f"── Tweet {i} ({len(tweet)} chars) ──────────────")
        lines.append(tweet)
        lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    created += 1
    print(f"  {out_path.name}  ({len(tweets)} tweets)")

print(f"\nGenerated {created} thread draft(s) in {THREADS_DIR}")
