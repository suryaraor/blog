#!/usr/bin/env python3
"""Process root-level markdown drafts into Jekyll posts and optionally push.

Workflow:
1) Find unprocessed source markdown files in articles/, workspace root, and artifacts/.
2) Clean mojibake and remove requested sections.
3) Normalize front matter and write Jekyll post to _posts or _unlisted.
4) Move processed source file into workspace processed folder.
5) Move leftover root support files into artifacts/ and runs/.
6) Validate output, optionally run Jekyll build, optionally git commit/push.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


class _Tee:
    """Write to both a stream and a log file simultaneously."""

    def __init__(self, stream, log_file):
        self._stream = stream
        self._log = log_file

    def write(self, data: str) -> int:
        self._log.write(data)
        return self._stream.write(data)

    def flush(self) -> None:
        self._stream.flush()
        self._log.flush()

    def __getattr__(self, name):
        return getattr(self._stream, name)


SKIP_NAME_TOKENS = (
    "image_prompt",
    "headline",   # covers headline-options, headlines, headline_formulas, etc.
    "topics",
    "_prompt",    # matches blog_prompt, generation_prompt, etc. but NOT article titles like "prompt-injection"
    "skill",
    "template",
    "readme",
    "checklist",
    "formulas",
    "covered_categories",
    "toolkit",
    # report / meta files that must never become blog posts
    "report",
    "summary",
    "delivery",
    "metadata",
    "completion",
    "scheduled",
    "execution",
    "pre_claude",  # PRE_CLAUDE_PLAN_* pipeline reports
)

TIER_KEYWORDS = {
    3: [
        "deepfake",
        "weapon",
        "military",
        "moratorium",
        "arms race",
        "legislature",
        "extinction",
        "pentagon",
        "layoff",
    ],
    2: [
        "wealth gap",
        "power grid",
        "belief divide",
        "controversial",
        "ipo",
        "inequality",
        "political",
        "job loss",
    ],
    1: ["regulation", "crisis", "automat"],
}

HEADING_HEADLINE_RE = re.compile(r"^\s{0,3}#{1,6}\s*(?:five|5)\b.*headlines?\s*$", re.IGNORECASE)
THE_HOOK_RE = re.compile(r"^\s{0,3}#{1,6}\s*the hook\b", re.IGNORECASE)
IMAGE_PROMPT_RE = re.compile(r"^\s{0,3}#{1,6}\s*image\s+prompt\b", re.IGNORECASE)
H1_RE = re.compile(r"^\s{0,3}#\s+(.+?)\s*$", re.MULTILINE)
ROOT_DRAFT_RE = re.compile(r"^(?:\d{4}[_-]\d{2}[_-]\d{2}|ARTICLE_|PRE_CLAUDE_PLAN_)", re.IGNORECASE)


def build_workspace_paths(script_path: Path) -> Dict[str, Path]:
    blog_root = script_path.resolve().parents[1]
    workspace_root = blog_root.parents[1]
    return {
        "workspace_root": workspace_root,
        "blog_root": blog_root,
        "source_dir": workspace_root,
        "articles_dir": workspace_root / "articles",
        "artifacts_dir": workspace_root / "artifacts",
        "processed_dir": workspace_root / "processed",
        "posts_dir": blog_root / "_posts",
        "unlisted_dir": blog_root / "_unlisted",
        "reverted_dir": blog_root / "_reverted",
        "images_dir": blog_root / "assets" / "images" / "posts",
    }


def parse_args() -> argparse.Namespace:
    paths = build_workspace_paths(Path(__file__))

    parser = argparse.ArgumentParser(
        description="Process markdown drafts from articles/, the workspace root, and artifacts/ to Jekyll posts and optionally push."
    )
    parser.add_argument("--source-dir", type=Path, default=paths["source_dir"])
    parser.add_argument("--articles-dir", type=Path, default=paths["articles_dir"])
    parser.add_argument("--artifacts-dir", type=Path, default=paths["artifacts_dir"])
    parser.add_argument("--processed-dir", type=Path, default=paths["processed_dir"])
    parser.add_argument("--blog-root", type=Path, default=paths["blog_root"])
    parser.add_argument("--posts-dir", type=Path, default=paths["posts_dir"])
    parser.add_argument("--unlisted-dir", type=Path, default=paths["unlisted_dir"])
    parser.add_argument("--reverted-dir", type=Path, default=paths["reverted_dir"])
    parser.add_argument("--publish-date", default=dt.date.today().isoformat())
    parser.add_argument("--branch", default="gh-pages")
    parser.add_argument("--remote", default="origin")
    parser.add_argument("--run-build", action="store_true", help="Run bundle exec jekyll build")
    parser.add_argument("--git-push", action="store_true", help="Commit and push written posts")
    parser.add_argument("--git-user-name", default="")
    parser.add_argument("--git-user-email", default="")
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Overwrite existing output file if publish-date + slug already exists",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument(
        "--generate-images",
        action="store_true",
        default=True,
        help="Fetch hero images (Unsplash for 'photo' style, Pollinations.AI for 'sketch' style)",
    )
    parser.add_argument(
        "--no-generate-images",
        dest="generate_images",
        action="store_false",
        help="Disable automatic hero image generation",
    )
    parser.add_argument(
        "--unsplash-key",
        default="",
        help="Unsplash API access key (overrides UNSPLASH_ACCESS_KEY env var)",
    )
    parser.add_argument(
        "--image-style",
        choices=["photo", "sketch", "isometric", "watercolor", "glassmorphism", "flat_vector", "auto"],
        default="auto",
        help=(
            "Image style for Pollinations.AI: 'auto' detects theme from post content (default); "
            "'isometric' for how-to/educational; 'watercolor' for ethics/future-AI; "
            "'glassmorphism' for hardware/coding; 'flat_vector' for tool reviews/UI-UX; "
            "'sketch' for legacy pencil-drawing; 'photo' uses Unsplash instead"
        ),
    )
    parser.add_argument(
        "--pollinations-model",
        default="flux",
        help="Pollinations.AI model to use (default: flux). Options: flux, flux-realism, flux-3d, flux-anime, turbo",
    )
    parser.add_argument(
        "--exit-delay",
        type=int,
        default=10,
        metavar="SECONDS",
        help="Seconds to pause before closing so the window stays readable (0 to disable, default: 10)",
    )
    return parser.parse_args()


def read_text_utf8_replace(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def fix_mojibake(text: str) -> Tuple[str, List[str]]:
    replacements = [
        ("â€”", "—"),
        ("â€“", "–"),
        ("â€™", "'"),
        ("â€˜", "'"),
        ("â€œ", '"'),
        ("â€\x9d", '"'),
        ("â€", '"'),
        ("â€", '"'),
        ("â€", '"'),
        ("Â·", "·"),
        ("â€¢", "•"),
        ("clichÃ©", "cliché"),
        ("naÃ¯vetÃ©", "naïveté"),
        ("Ã©", "é"),
        ("Ã¨", "è"),
        ("Ãª", "ê"),
        ("Ã«", "ë"),
        ("Ã¡", "á"),
        ("Ã ", "à"),
        ("Ã¢", "â"),
        ("Ã£", "ã"),
        ("Ã¶", "ö"),
        ("Ã´", "ô"),
        ("Ã³", "ó"),
        ("Ãº", "ú"),
        ("Ã¹", "ù"),
        ("Ã¼", "ü"),
        ("Ã±", "ñ"),
        ("Ã§", "ç"),
        ("Ã¯", "ï"),
        ("Ã®", "î"),
        ("Ã­", "í"),
    ]

    applied: List[str] = []
    cleaned = text
    for old, new in replacements:
        if old in cleaned:
            cleaned = cleaned.replace(old, new)
            applied.append(f"{old} -> {new}")

    return cleaned, applied


def filename_to_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d{4}[_-]\d{2}[_-]\d{2}(?:[_-]\d{2})?[_-]?", "", stem)
    stem = re.sub(r"[_-]+", " ", stem).strip()
    if not stem:
        stem = "Untitled"
    return " ".join(part.capitalize() for part in stem.split())


def extract_title(text: str, source_name: str) -> str:
    m = H1_RE.search(text)
    if m:
        return m.group(1).strip()
    return filename_to_title(source_name)


def slugify_title(title: str) -> str:
    t = title.lower()
    t = re.sub(r"[\'\"’“”]", "", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    t = re.sub(r"\s+", "-", t).strip("-")
    return t or "untitled"


def find_next_order(posts_dir: Path, unlisted_dir: Path, reverted_dir: Optional[Path] = None) -> int:
    """Scan existing posts/unlisted/reverted for the highest order: value and return max+1."""
    max_order = 0
    order_re = re.compile(r"^\s*order\s*:\s*(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
    dirs = [posts_dir, unlisted_dir]
    if reverted_dir is not None:
        dirs.append(reverted_dir)
    for directory in dirs:
        if not directory.exists():
            continue
        for md in directory.glob("*.md"):
            try:
                text = md.read_text(encoding="utf-8", errors="replace")
                m = order_re.search(text[:500])  # only check front matter region
                if m:
                    max_order = max(max_order, int(m.group(1)))
            except OSError:
                pass
    return max_order + 1


def extract_image_prompt(text: str) -> Optional[str]:
    """Return the text under ## Image Prompt heading before clean_sections strips it."""
    lines = text.splitlines()
    capturing = False
    parts: List[str] = []
    for line in lines:
        if IMAGE_PROMPT_RE.match(line):
            capturing = True
            continue
        if capturing:
            if re.match(r"^\s{0,3}#{1,6}\s+", line) or re.match(r"^\s*---\s*$", line):
                break
            parts.append(line)
    result = "\n".join(parts).strip()
    return result or None


def load_env_file(blog_root: Path) -> None:
    """Load .env from blog_root into os.environ; existing env vars are not overwritten."""
    env_file = blog_root / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_DIRECTIVE_LINE_RE = re.compile(
    r"^\s*(style|lighting|camera|shot|color|mood|tone|composition|background|setting|"
    r"format|aspect|ratio|resolution|quality|render|post.?processing)\s*:",
    re.IGNORECASE,
)
_STRIP_PHRASES = re.compile(
    r"\b(create\s+a|visual\s+metaphor\s+of|photorealistic|dramatic\s+lighting|"
    r"editorial\s+quality|cinematic|high\s+contrast|professional\s+photography|"
    r"ultra.?realistic|hyperrealistic|highly\s+detailed|full.?bleed|wide.?angle|"
    r"stock\s+photo(?:graphy)?)\b",
    re.IGNORECASE,
)
_PUNCTUATION_RE = re.compile(r"[—–\-|,;:.!?\"'()\[\]{}]")

_TITLE_STOP_WORDS = {
    "why", "how", "what", "when", "where", "who", "which", "the", "a", "an",
    "and", "or", "but", "for", "nor", "yet", "so", "as", "at", "by", "in",
    "of", "on", "to", "up", "is", "are", "was", "were", "be", "been",
    "have", "has", "had", "do", "does", "did", "will", "would", "should",
    "could", "may", "might", "we", "you", "they", "it", "this", "that",
    "just", "now", "not", "your", "our", "its", "my", "we're", "you're",
    "they're", "it's", "there", "here", "about", "with", "from", "into",
    "already", "still", "also", "even", "very", "than", "then", "too",
    "more", "most", "some", "every", "any", "new", "big", "make", "get",
    "their", "these", "those", "over", "under", "been", "only", "never",
    "re", "ve", "ll", "s", "d",
}

_TECH_JARGON = {
    "rag", "llm", "api", "sdk", "saas", "paas", "k8s", "orm", "crud",
    "rest", "graphql", "cicd", "devops", "npm", "pip", "git", "cli",
    "based", "using", "via",
}


def _title_to_search_words(title: str) -> List[str]:
    """Strip stop words and tech jargon from a title; return searchable content words."""
    cleaned = _PUNCTUATION_RE.sub(" ", title)
    words = cleaned.split()
    return [
        w for w in words
        if len(w) > 2
        and w.lower() not in _TITLE_STOP_WORDS
        and w.lower() not in _TECH_JARGON
    ]


def extract_search_keywords(image_prompt: Optional[str], title: str) -> str:
    """Distill image_prompt or title into a short Unsplash search query (3-5 key nouns)."""
    if image_prompt:
        content_lines = [
            line.strip()
            for line in image_prompt.splitlines()
            if line.strip() and not _DIRECTIVE_LINE_RE.match(line)
        ]
        combined = " ".join(content_lines[:3])
        combined = _STRIP_PHRASES.sub(" ", combined)
        combined = _PUNCTUATION_RE.sub(" ", combined)
        words = [w for w in combined.split() if len(w) > 2]
        if words:
            query = " ".join(words[:6])
            return query[:60].rsplit(" ", 1)[0] if len(query) > 60 else query
    content_words = _title_to_search_words(title)
    if content_words:
        query = " ".join(content_words[:5])
        return query[:60].rsplit(" ", 1)[0] if len(query) > 60 else query
    return title[:60].rsplit(" ", 1)[0] if len(title) > 60 else title


def _unsplash_search(query: str, access_key: str) -> List[dict]:
    """Run a single Unsplash search; return results list (empty on error or no hits)."""
    encoded_query = urllib.parse.quote(query)
    search_url = (
        f"https://api.unsplash.com/search/photos"
        f"?query={encoded_query}&per_page=10&orientation=landscape&content_filter=high&order_by=relevant"
    )
    req = urllib.request.Request(
        search_url, headers={"Authorization": f"Client-ID {access_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("results", [])
    except urllib.error.URLError as exc:
        print(f"[image] Unsplash search error: {exc}", file=sys.stderr)
        return []


def _build_query_candidates(query: str) -> List[str]:
    """Return progressively simpler fallback queries from the original."""
    candidates: List[str] = [query]
    words = query.split()
    if len(words) > 3:
        candidates.append(" ".join(words[:3]))
    if len(words) > 2:
        candidates.append(" ".join(words[:2]))
    if len(words) > 1:
        candidates.append(words[0])
    return list(dict.fromkeys(candidates))  # deduplicate while preserving order


def fetch_unsplash_image(query: str, access_key: str) -> Optional[Tuple[bytes, str]]:
    """Search Unsplash for a landscape photo; return (jpeg_bytes, attribution_markdown) or None.

    Fetches top 10 results, picks the one with the most likes, and retries with
    progressively shorter queries if the first search returns no results.
    """
    results: List[dict] = []
    used_query = query
    for candidate in _build_query_candidates(query):
        results = _unsplash_search(candidate, access_key)
        if results:
            used_query = candidate
            if candidate != query:
                print(f"[image] Fell back to shorter query: '{candidate}'")
            break

    if not results:
        print(f"[image] No Unsplash results for: {query}", file=sys.stderr)
        return None

    # Pick the photo with the most likes from the relevance-ranked results
    photo = max(results, key=lambda p: p.get("likes", 0))
    print(f"[image] '{used_query}' -> selected photo #{results.index(photo) + 1}/{len(results)} by likes ({photo.get('likes', 0)})")

    download_url = photo["urls"]["regular"]
    photographer = photo["user"]["name"]
    user_link = photo["user"]["links"]["html"]

    # Trigger download tracking as required by Unsplash API guidelines
    track_url = photo.get("links", {}).get("download_location")
    if track_url:
        try:
            urllib.request.urlopen(
                urllib.request.Request(f"{track_url}?client_id={access_key}"), timeout=10
            )
        except Exception:
            pass

    try:
        with urllib.request.urlopen(urllib.request.Request(download_url), timeout=30) as img_resp:
            image_bytes = img_resp.read()
    except urllib.error.URLError as exc:
        print(f"[image] Unsplash download error: {exc}", file=sys.stderr)
        return None

    attribution = (
        f"Photo by [{photographer}]({user_link}?utm_source=blog&utm_medium=referral)"
        f" on [Unsplash](https://unsplash.com/?utm_source=blog&utm_medium=referral)"
    )
    return image_bytes, attribution


# ── Theme keyword maps ────────────────────────────────────────────────────────
# Each entry: (title/category keywords, theme name)
# Evaluated in order; first match wins.
_THEME_SIGNALS: List[Tuple[List[str], str]] = [
    # Ethics / Future-of-AI posts → Watercolor
    (["ethic", "future", "society", "human", "conscious", "moral", "trust",
      "bias", "fairness", "rights", "philosophy", "existential", "sentient",
      "regulate", "regulation", "policy", "governance", "democratic",
      "intentional internet", "wealth gap", "inequality", "divide"], "watercolor"),
    # Hardware / Deep-coding posts → Glassmorphism
    (["hardware", "chip", "silicon", "gpu", "cpu", "neural chip", "circuit",
      "architecture", "infrastructure", "cloud", "kubernetes", "docker",
      "spring boot", "backend", "database", "hexagonal", "coding", "code",
      "angular", "react", "typescript", "python", "rust", "go lang",
      "databricks", "data engineering", "data pipeline", "edge ai"], "glassmorphism"),
    # AI Tool Reviews / Productivity / UI-UX → Flat Vector
    (["tool", "review", "ui", "ux", "design", "app", "product", "software",
      "platform", "saas", "interface", "workflow", "productivity", "automation",
      "agent", "agentic", "assistant", "chatbot", "copilot", "plugin"], "flat_vector"),
    # How-To / Educational / Tutorials → Isometric 3D
    (["how to", "how-to", "guide", "tutorial", "learn", "beginner", "step",
      "build", "create", "implement", "setup", "getting started", "explained",
      "introduction", "deep dive", "breakdown", "interceptor", "store"], "isometric"),
]

# Theme → Pollinations.AI prompt suffix + preferred background descriptor
_THEME_PROMPTS: Dict[str, Tuple[str, str]] = {
    "isometric": (
        "Clean Isometric 3D Illustration, white background with blue accent colors, "
        "organized geometric layout, professional tech illustration, crisp edges, "
        "soft shadows, modern infographic style",
        "isometric",
    ),
    "watercolor": (
        "Abstract Watercolor and Ink illustration, muted earth tones and soft pastels, "
        "organic flowing shapes, hand-painted texture, ink wash, expressive brushstrokes, "
        "thoughtful and human feeling, no harsh edges",
        "watercolor",
    ),
    "glassmorphism": (
        "Futuristic Glassmorphism with Neon Circuitry, dark mode deep black background, "
        "glowing teal and cyan neon accents, frosted glass panels, circuit board patterns, "
        "high-tech digital aesthetic, dramatic contrast, cyberpunk-inspired",
        "glassmorphism",
    ),
    "flat_vector": (
        "Flat Vector Illustration in Modern Web Design style, vibrant high-contrast primary colors, "
        "clean geometric shapes, bold solid fills, minimal shadows, modern app UI aesthetic, "
        "crisp and polished, no gradients",
        "flat_vector",
    ),
    # Legacy fallback kept for --image-theme sketch
    "sketch": (
        "pencil sketch, crosshatching, black and white ink drawing, "
        "detailed hand-drawn illustration, no color, fine line art",
        "sketch",
    ),
}


def detect_image_theme(title: str, category: str = "", image_prompt: str = "") -> str:
    """Return the best-matching theme name for a post based on title/category/prompt signals."""
    haystack = " ".join([title, category, image_prompt]).lower()
    for signals, theme in _THEME_SIGNALS:
        if any(sig in haystack for sig in signals):
            return theme
    # Default: isometric (most broadly applicable for tech content)
    return "isometric"


def build_pollinations_prompt(
    image_prompt: Optional[str],
    title: str,
    theme: str = "auto",
    category: str = "",
) -> str:
    """Build a Pollinations.AI prompt with a content-matched visual theme suffix.

    theme values:
      "auto"         — detect from title/category/image_prompt (recommended)
      "isometric"    — How-To / Educational posts
      "watercolor"   — Ethics / Future-of-AI posts
      "glassmorphism"— Hardware / Coding posts
      "flat_vector"  — Tool Reviews / UI-UX posts
      "sketch"       — Legacy pencil-sketch (backwards compat)
    """
    _DIRECTIVE_LABELS_RE = re.compile(
        r"^\s*(style|lighting|camera|shot|color|mood|tone|composition|background|"
        r"setting|format|aspect|ratio|resolution|quality|render)\s*:",
        re.IGNORECASE,
    )
    if image_prompt:
        content_lines = [
            line.strip()
            for line in image_prompt.splitlines()
            if line.strip() and not _DIRECTIVE_LABELS_RE.match(line)
        ]
        base = " ".join(content_lines[:4]).strip()
    else:
        base = title

    if theme == "auto":
        theme = detect_image_theme(title, category, image_prompt or "")

    theme_suffix, _ = _THEME_PROMPTS.get(theme, _THEME_PROMPTS["isometric"])
    return f"{base}, {theme_suffix}"


def fetch_pollinations_image(
    image_prompt: Optional[str],
    title: str,
    model: str = "flux",
    theme: str = "auto",
    category: str = "",
) -> Optional[Tuple[bytes, str]]:
    """Generate a themed hero image via Pollinations.AI; return (jpeg_bytes, attribution) or None."""
    resolved_theme = theme if theme != "auto" else detect_image_theme(title, category, image_prompt or "")
    prompt_text = build_pollinations_prompt(image_prompt, title, theme=resolved_theme, category=category)
    encoded = urllib.parse.quote(prompt_text)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1200&height=675&model={model}&nologo=true&seed=42"
    )
    print(f"[image] Generating image via Pollinations.AI (model={model}, theme={resolved_theme})…")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "blog-pipeline/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            image_bytes = resp.read()
    except urllib.error.URLError as exc:
        print(f"[image] Pollinations.AI error: {exc}", file=sys.stderr)
        return None

    if len(image_bytes) < 1024:
        print("[image] Pollinations.AI returned unexpectedly small response; skipping.", file=sys.stderr)
        return None

    attribution = "AI-generated illustration via [Pollinations.AI](https://pollinations.ai)"
    return image_bytes, attribution


def clean_sections(text: str) -> Tuple[str, Dict[str, int]]:
    lines = text.splitlines()
    out: List[str] = []
    i = 0
    removed_headline_blocks = 0
    removed_hook_headings = 0
    removed_image_prompts = 0

    while i < len(lines):
        line = lines[i]

        if HEADING_HEADLINE_RE.match(line):
            removed_headline_blocks += 1
            i += 1

            while i < len(lines) and lines[i].strip() == "":
                i += 1

            while i < len(lines):
                cur = lines[i]
                if re.match(r"^\s{0,3}\d+[\.)]\s+", cur):
                    i += 1
                    continue
                if re.match(r"^\s{2,}\S+", cur):
                    i += 1
                    continue
                if cur.strip() == "":
                    i += 1
                    continue
                break

            if i < len(lines) and re.match(r"^\s*---\s*$", lines[i]):
                i += 1

            continue

        if THE_HOOK_RE.match(line):
            removed_hook_headings += 1
            i += 1
            continue

        if IMAGE_PROMPT_RE.match(line):
            # Remove the Image Prompt heading and everything to end of file
            removed_image_prompts += 1
            # Strip trailing --- separator that may precede it
            while out and re.match(r"^\s*---\s*$", out[-1]):
                out.pop()
            break

        out.append(line)
        i += 1

    return "\n".join(out).strip() + "\n", {
        "headline_blocks": removed_headline_blocks,
        "hook_headings": removed_hook_headings,
        "image_prompts": removed_image_prompts,
    }


def parse_front_matter(text: str) -> Tuple[Optional[List[str]], str]:
    if not text.startswith("---"):
        return None, text

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text

    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break

    if end_idx is None:
        return None, text

    front_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return front_lines, body


def normalize_front_matter(
    text: str, title: str, publish_date: str, order: int,
    image: Optional[str] = None, image_credit: Optional[str] = None
) -> str:
    front_lines, body = parse_front_matter(text)

    extra_lines: List[str] = []
    existing_order: Optional[int] = None
    if front_lines is not None:
        for line in front_lines:
            if re.match(r"^\s*(layout|title|date|order|image)\s*:", line, re.IGNORECASE):
                m = re.match(r"^\s*order\s*:\s*(\d+)", line, re.IGNORECASE)
                if m:
                    existing_order = int(m.group(1))
                continue
            extra_lines.append(line)

    escaped_title = title.replace('"', '\\"')
    final_order = existing_order if existing_order is not None else order
    fm = [
        "---",
        f"order: {final_order}",
        "layout: default",
        f'title: "{escaped_title}"',
        f"date: {publish_date}",
    ]
    if image:
        fm.append(f"image: {image}")
    if image_credit:
        fm.append(f'image_credit: "{image_credit}"')
    fm.extend(extra_lines)
    fm.append("---")

    if not body.endswith("\n"):
        body += "\n"

    return "\n".join(fm) + "\n" + body


def keyword_pattern(keyword: str) -> re.Pattern[str]:
    if keyword == "automat":
        return re.compile(r"\bautomat\w*\b", re.IGNORECASE)
    escaped = re.escape(keyword).replace(r"\ ", r"\s+")
    return re.compile(rf"\b{escaped}\b", re.IGNORECASE)


def sensitivity_score(title: str, body_text: str) -> Tuple[int, List[Tuple[str, str, int]]]:
    heading_lines = "\n".join(
        line for line in body_text.splitlines() if re.match(r"^\s{0,3}#{1,6}\s+", line)
    )
    non_heading_lines = "\n".join(
        line for line in body_text.splitlines() if not re.match(r"^\s{0,3}#{1,6}\s+", line)
    )

    details: List[Tuple[str, str, int]] = []

    for tier, keywords in TIER_KEYWORDS.items():
        for kw in keywords:
            pat = keyword_pattern(kw)
            options: List[Tuple[str, int]] = []

            if pat.search(title):
                options.append(("title", int(math.ceil(tier * 1.5))))
            if pat.search(heading_lines):
                options.append(("heading", max(0, int(math.floor(tier * 0.5)))))
            if pat.search(non_heading_lines):
                options.append(("body", tier))

            if options:
                best = sorted(options, key=lambda x: x[1], reverse=True)[0]
                details.append((kw, best[0], best[1]))

    score = sum(p for _, _, p in details)
    if len(details) >= 3:
        score += 1
        details.append(("cluster_bonus", "global", 1))

    return score, details


def move_supporting_files(source_file: Path, processed_dir: Path) -> List[str]:
    """Move matching HEADLINES and IMAGE_PROMPT files to processed/ folder."""
    moved_files = []
    
    # Extract base name pattern: "2026_04_27_ARTICLE_global_inequality_ai" -> "2026_04_27_*_global_inequality_ai"
    source_name = source_file.stem
    if "_ARTICLE_" not in source_name:
        return moved_files
    
    # Build pattern to find matching files: "2026_04_27_{HEADLINES,IMAGE_PROMPT}_global_inequality_ai.txt"
    date_part = source_name.split("_ARTICLE_")[0]  # e.g., "2026_04_27"
    topic_part = source_name.split("_ARTICLE_")[1]  # e.g., "global_inequality_ai"
    
    # Look for matching HEADLINES and IMAGE_PROMPT files
    for file_type in ["HEADLINES", "IMAGE_PROMPT"]:
        pattern = f"{date_part}_{file_type}_{topic_part}*.txt"
        matching_files = list(source_file.parent.glob(pattern))
        
        for matching_file in matching_files:
            target = processed_dir / matching_file.name
            if target.exists():
                target.unlink()
            shutil.move(str(matching_file), str(target))
            moved_files.append(matching_file.name)
    
    return moved_files


def move_root_support_files(workspace_root: Path, artifacts_dir: Path, runs_dir: Path) -> List[str]:
    """Move leftover root support files into their canonical folders."""
    moved_files: List[str] = []

    def move_matches(patterns: List[str], destination: Path) -> None:
        for pattern in patterns:
            for matching_file in workspace_root.glob(pattern):
                if not matching_file.is_file():
                    continue
                target = destination / matching_file.name
                if target.exists():
                    target.unlink()
                shutil.move(str(matching_file), str(target))
                moved_files.append(str(target.relative_to(workspace_root)))

    archive_dir = workspace_root / "articles" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    move_matches([
        "*_HEADLINES_*.txt",
        "*_IMAGE_PROMPT_*.txt",
        "PRE_CLAUDE_PLAN_*.md",
    ], archive_dir)

    if runs_dir.exists():
        move_matches([
            "EXECUTION_SUMMARY_*.md",
            "EXECUTION_REPORT_*.md",
            "EXECUTION_REPORT_*.txt",
            "SCHEDULED_TASK_*.md",
            "SCHEDULED_TASK_*.txt",
            "*_COMPLETION_REPORT*.md",
            "*_COMPLETION_REPORT*.txt",
            "*_COMPLETION_SUMMARY*.md",
            "*_DELIVERY*.md",
            "*TASK_COMPLETION*.md",
        ], runs_dir)

    return moved_files


def find_unprocessed_files(source_dirs: List[Path], processed_dir: Path) -> List[Path]:
    processed_names = {p.name.lower() for p in processed_dir.glob("*.md")}

    candidates: List[Path] = []
    seen_paths = set()
    for source_dir in source_dirs:
        if not source_dir.exists():
            continue
        for p in source_dir.iterdir():
            if not p.is_file() or p.suffix.lower() != ".md":
                continue

            resolved = p.resolve()
            if resolved in seen_paths:
                continue

            low_name = p.name.lower()
            matched_token = next((tok for tok in SKIP_NAME_TOKENS if tok in low_name), None)
            if matched_token:
                print(f"[skip] {p.name} — matches skip token '{matched_token}'")
                continue
            if source_dir.name not in {"artifacts", "articles"} and not ROOT_DRAFT_RE.match(p.name):
                print(f"[skip] {p.name} — not a recognized draft pattern in '{source_dir.name}'")
                continue
            if low_name in processed_names:
                print(f"[skip] {p.name} — already processed")
                continue
            seen_paths.add(resolved)
            candidates.append(p)

    return sorted(candidates)


def slug_already_exists(posts_dir: Path, unlisted_dir: Path, slug: str, reverted_dir: Optional[Path] = None) -> bool:
    pattern = f"*-{slug}.md"
    exists = any(posts_dir.glob(pattern)) or any(unlisted_dir.glob(pattern))
    if not exists and reverted_dir is not None:
        exists = any(reverted_dir.glob(pattern))
    return exists


@dataclass
class FileReport:
    source: Path
    output: Path
    title: str
    slug: str
    destination: str
    score: int
    score_details: List[Tuple[str, str, int]]
    removed: Dict[str, int]
    mojibake_fixes: List[str]
    validations: Dict[str, bool]
    moved_supporting_files: List[str] = None
    image_filename: Optional[str] = None
    image_credit: Optional[str] = None


def validate_output(path: Path, content: str) -> Dict[str, bool]:
    raw = path.read_bytes()
    checks = {
        "filename_pattern": bool(re.match(r"^\d{4}-\d{2}-\d{2}-.+\.md$", path.name)),
        "starts_with_front_matter": content.startswith("---\n"),
        "has_order_field": bool(re.search(r"^\s*order\s*:\s*\d+", content[:500], re.MULTILINE)),
        "no_headline_heading": not bool(HEADING_HEADLINE_RE.search(content)),
        "no_the_hook_heading": not bool(THE_HOOK_RE.search(content)),
        "no_image_prompt_heading": not bool(IMAGE_PROMPT_RE.search(content)),
        "no_mojibake_patterns": not bool(re.search(r"â€|Ã|Â·", content)),
        "utf8_no_bom": raw[:3] != b"\xef\xbb\xbf",
    }
    return checks


def run_jekyll_build(blog_root: Path) -> Tuple[str, str]:
    try:
        proc = subprocess.run(
            ["bundle", "exec", "jekyll", "build"],
            cwd=blog_root,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        return "non-blocking", f"bundle not found: {exc}"

    if proc.returncode == 0:
        return "success", proc.stdout.strip()

    out = (proc.stdout + "\n" + proc.stderr).lower()
    if "bundle: command not found" in out or "bundler" in out or "ruby" in out:
        return "non-blocking", proc.stderr.strip() or proc.stdout.strip()

    return "failed", proc.stderr.strip() or proc.stdout.strip()


def run_git(args: argparse.Namespace, written_paths: List[Path]) -> Tuple[bool, str]:
    if not written_paths:
        return True, "No new output files to commit."

    rel_paths = [str(p.relative_to(args.blog_root)).replace("\\", "/") for p in written_paths]

    def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, cwd=args.blog_root, text=True, capture_output=True, check=False)

    if args.git_user_name:
        run_cmd(["git", "config", "user.name", args.git_user_name])
    if args.git_user_email:
        run_cmd(["git", "config", "user.email", args.git_user_email])

    # Pull latest before committing to avoid non-fast-forward rejections on push
    pull = run_cmd(["git", "pull", "--rebase", "--autostash", args.remote, args.branch])
    if pull.returncode != 0:
        return False, f"git pull --rebase --autostash failed: {pull.stderr.strip() or pull.stdout.strip()}"

    add = run_cmd(["git", "add", *rel_paths])
    if add.returncode != 0:
        return False, add.stderr.strip() or add.stdout.strip()

    message = f"Automate blog post import for {args.publish_date} ({len(rel_paths)} files)"
    commit = run_cmd(["git", "commit", "-m", message])
    if commit.returncode != 0:
        output = (commit.stderr + "\n" + commit.stdout).strip()
        if "nothing to commit" in output.lower():
            return True, "Nothing to commit."
        return False, output

    push = run_cmd(["git", "push", args.remote, args.branch])
    if push.returncode != 0:
        return False, push.stderr.strip() or push.stdout.strip()

    return True, (commit.stdout + "\n" + push.stdout + "\n" + push.stderr).strip()


def collect_pending_publish_paths(blog_root: Path) -> List[Path]:
    """Collect tracked or untracked publish artifacts that still need to be committed."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=blog_root,
        text=True,
        capture_output=True,
        check=False,
    )

    if proc.returncode != 0:
        return []

    publishable_prefixes = (
        "_posts/",
        "_unlisted/",
        "_reverted/",
        "assets/images/posts/",
        "assets/audio/posts/",
    )

    pending: List[Path] = []
    seen = set()

    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue

        path_text = line[3:].strip()
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1].strip()

        normalized = path_text.replace("\\", "/")
        if not normalized.startswith(publishable_prefixes):
            continue

        full_path = blog_root / normalized
        if full_path in seen:
            continue
        seen.add(full_path)
        pending.append(full_path)

    return pending


def validate_remote_push(blog_root: Path, written_paths: List[Path], remote: str, branch: str) -> Tuple[bool, str]:
    """Pull latest from remote and validate pushed files are present."""
    if not written_paths:
        return True, "No files to validate."

    def run_cmd(cmd: List[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(cmd, cwd=blog_root, text=True, capture_output=True, check=False)

    pull = run_cmd(["git", "pull", remote, branch])
    if pull.returncode != 0:
        return False, f"git pull failed: {pull.stderr.strip() or pull.stdout.strip()}"

    missing_files = []
    for path in written_paths:
        if not path.exists():
            missing_files.append(str(path.relative_to(blog_root)))

    if missing_files:
        return False, (
            f"After pull, {len(missing_files)} file(s) missing from local repo:\n"
            + "\n".join(f"  - {f}" for f in missing_files)
        )

    details = f"✅ All {len(written_paths)} pushed file(s) validated after pull from {remote}/{branch}"
    return True, details


def cleanup_topics_file(workspace_root: Path) -> None:
    """Archive verbose topics.txt and create compact version for next workflow."""
    topics_file = workspace_root / "docs" / "topics.txt"
    if not topics_file.exists():
        return
    
    archive_dir = workspace_root / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    # Archive with timestamp
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    archive_file = archive_dir / f"topics_archive_{timestamp}.txt"
    shutil.copy2(str(topics_file), str(archive_file))
    
    # Create compact header for next workflow
    compact_content = """# Active Topics List

## Format
Date | Status | Topic | Brief Rationale

## Current Topics

---

## Archive
See archive/topics_archive_*.txt for complete historical logs.
"""
    
    topics_file.write_text(compact_content, encoding="utf-8")


def print_report(
    reports: List[FileReport],
    build_result: Optional[Tuple[str, str]],
    git_result: Optional[Tuple[bool, str]],
) -> None:
    print("\n=== Processing Report ===")

    for rep in reports:
        print(f"\nSource: {rep.source}")
        print(f"Output: {rep.output}")
        print(f"Title: {rep.title}")
        print(f"Slug: {rep.slug}")
        print(f"Destination: {rep.destination}")
        print(f"Sensitivity score: {rep.score}")
        if rep.score_details:
            print("Score details:")
            for kw, loc, pts in rep.score_details:
                print(f"  - {kw} [{loc}] = {pts}")

        print(
            "Sections removed: "
            f"headlines={rep.removed['headline_blocks']}, "
            f"the_hook={rep.removed['hook_headings']}, "
            f"image_prompt={rep.removed.get('image_prompts', 0)}"
        )
        if rep.mojibake_fixes:
            print(f"Mojibake fixes: yes ({len(rep.mojibake_fixes)} replacements)")
        else:
            print("Mojibake fixes: no")
        
        if rep.image_filename:
            print(f"Image: {rep.image_filename}")
            if rep.image_credit:
                print(f"Image credit: {rep.image_credit}")
        else:
            print("Image: none")

        if rep.moved_supporting_files:
            print(f"Supporting files moved: yes ({len(rep.moved_supporting_files)} files)")
            for fname in rep.moved_supporting_files:
                print(f"  - {fname}")
        else:
            print("Supporting files moved: no")

        print("Validation:")
        for check, ok in rep.validations.items():
            print(f"  - {check}: {'PASS' if ok else 'FAIL'}")

    if build_result is not None:
        status, details = build_result
        print(f"\nJekyll build: {status}")
        if details:
            print(details)

    if git_result is not None:
        ok, details = git_result
        print(f"\nGit push: {'success' if ok else 'failure'}")
        if details:
            print(details)


def main() -> int:
    args = parse_args()

    args.source_dir = args.source_dir.resolve()
    args.articles_dir = args.articles_dir.resolve()
    args.artifacts_dir = args.artifacts_dir.resolve()
    args.processed_dir = args.processed_dir.resolve()
    args.blog_root = args.blog_root.resolve()
    args.posts_dir = args.posts_dir.resolve()
    args.unlisted_dir = args.unlisted_dir.resolve()
    args.reverted_dir = args.reverted_dir.resolve()

    # Set up per-run log file
    logs_dir = args.source_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    run_ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"run_{run_ts}.log"
    _log_file = open(log_path, "w", encoding="utf-8")
    _orig_stdout, _orig_stderr = sys.stdout, sys.stderr
    sys.stdout = _Tee(sys.stdout, _log_file)
    sys.stderr = _Tee(sys.stderr, _log_file)

    _exit_code = 0
    try:
        _exit_code = _main_inner(args, logs_dir, log_path)
    finally:
        sys.stdout = _orig_stdout
        sys.stderr = _orig_stderr
        _log_file.close()
        _orig_stdout.write(f"\nLog written → {log_path}\n")
        _orig_stdout.flush()
        if args.exit_delay > 0:
            for _i in range(args.exit_delay, 0, -1):
                _orig_stdout.write(f"\rClosing in {_i}s… (Ctrl-C to exit now)  ")
                _orig_stdout.flush()
                time.sleep(1)
            _orig_stdout.write("\r" + " " * 40 + "\n")
            _orig_stdout.flush()
    return _exit_code


def _main_inner(args, logs_dir: Path, log_path: Path) -> int:
    print(f"=== Run started: {dt.datetime.now().isoformat(timespec='seconds')} ===")
    print(f"Log: {log_path}")

    for d in (args.processed_dir, args.posts_dir, args.unlisted_dir):
        d.mkdir(parents=True, exist_ok=True)

    load_env_file(args.blog_root)
    unsplash_key = args.unsplash_key or os.environ.get("UNSPLASH_ACCESS_KEY", "")

    if not args.dry_run:
        move_root_support_files(args.source_dir, args.artifacts_dir, args.source_dir / "runs")

    unprocessed = find_unprocessed_files([args.articles_dir, args.source_dir], args.processed_dir)
    if not unprocessed:
        if args.git_push and not args.dry_run:
            pending_paths = collect_pending_publish_paths(args.blog_root)
            if pending_paths:
                print(f"Nothing to process; pushing {len(pending_paths)} pending publish file(s).")
                git_result = run_git(args, pending_paths)

                validation_result = None
                if git_result[0]:
                    validation_result = validate_remote_push(
                        blog_root=args.blog_root,
                        written_paths=pending_paths,
                        remote=args.remote,
                        branch=args.branch,
                    )

                print_report([], None, git_result)

                if validation_result is not None:
                    ok, details = validation_result
                    print(f"\nPost-push validation: {'success' if ok else 'failure'}")
                    if details:
                        print(details)
                    if not ok:
                        return 6

                if not git_result[0]:
                    return 4

                cleanup_topics_file(args.source_dir.parent)
                return 0

        print("Nothing to process")
        return 0

    reports: List[FileReport] = []
    written_paths: List[Path] = []
    next_order = find_next_order(args.posts_dir, args.unlisted_dir, args.reverted_dir)

    image_style = args.image_style  # "auto", "photo", "sketch", or explicit theme name
    want_images = args.generate_images
    if want_images and image_style == "photo" and not unsplash_key:
        print("[image] --generate-images set but UNSPLASH_ACCESS_KEY not found; switching to auto theme mode.", file=sys.stderr)
        image_style = "auto"
    print(f"[image] Image mode: {image_style}")

    for source_file in unprocessed:
        original = read_text_utf8_replace(source_file)
        fixed_text, mojibake_changes = fix_mojibake(original)
        title = extract_title(fixed_text, source_file.name)
        slug = slugify_title(title)

        if slug_already_exists(args.posts_dir, args.unlisted_dir, slug, args.reverted_dir) and not args.overwrite_existing:
            print(
                f"Skipping {source_file.name}: slug '{slug}' already exists in _posts, _unlisted, or _reverted. "
                "Use --overwrite-existing to replace it."
            )
            continue

        # Extract image prompt BEFORE clean_sections strips it
        image_prompt = extract_image_prompt(fixed_text) if want_images else None

        # Extract category from front matter for theme detection
        _cat_match = re.search(r"^\s*category\s*:\s*(.+)$", fixed_text[:600], re.IGNORECASE | re.MULTILINE)
        post_category = _cat_match.group(1).strip().strip('"\'') if _cat_match else ""

        cleaned, removed = clean_sections(fixed_text)

        # Fetch hero image before normalize so path ends up in front matter
        image_bytes: Optional[bytes] = None
        image_filename: Optional[str] = None
        image_credit: Optional[str] = None
        if want_images and not args.dry_run:
            if image_style == "photo":
                query = extract_search_keywords(image_prompt, title)
                print(f"[image] Searching Unsplash for '{query}'…")
                result = fetch_unsplash_image(query, unsplash_key)
                if result:
                    image_bytes, image_credit = result
                    image_filename = f"/assets/images/posts/{args.publish_date}-{slug}.jpg"
                    print(f"[image] Found -> {args.publish_date}-{slug}.jpg")
                else:
                    print(f"[image] Unsplash fetch failed for '{title}'; continuing without image.", file=sys.stderr)
            else:
                # image_style is "auto", "sketch", "isometric", "watercolor", "glassmorphism", or "flat_vector"
                result = fetch_pollinations_image(
                    image_prompt, title,
                    model=args.pollinations_model,
                    theme=image_style,
                    category=post_category,
                )
                if result:
                    image_bytes, image_credit = result
                    image_filename = f"/assets/images/posts/{args.publish_date}-{slug}.jpg"
                    print(f"[image] Generated -> {args.publish_date}-{slug}.jpg")
                else:
                    print(f"[image] Pollinations.AI failed for '{title}'; continuing without image.", file=sys.stderr)

        normalized = normalize_front_matter(
            cleaned, title=title, publish_date=args.publish_date, order=next_order,
            image=image_filename, image_credit=image_credit
        )
        next_order += 1

        score, score_details = sensitivity_score(title, normalized)
        destination_name = "_unlisted" if score >= 3 else "_posts"
        destination_dir = args.unlisted_dir if score >= 3 else args.posts_dir

        output_path = destination_dir / f"{args.publish_date}-{slug}.md"

        if output_path.exists() and not args.overwrite_existing:
            print(
                f"Skipping {source_file.name}: {output_path.name} already exists. "
                "Use --overwrite-existing to replace it."
            )
            continue

        moved_supporting = []
        if not args.dry_run:
            output_path.write_text(normalized, encoding="utf-8", newline="\n")
            target_processed = args.processed_dir / source_file.name
            if target_processed.exists():
                target_processed.unlink()
            shutil.move(str(source_file), str(target_processed))

            # Save generated image and queue for git
            if image_bytes and image_filename:
                images_dir = args.blog_root / "assets" / "images" / "posts"
                images_dir.mkdir(parents=True, exist_ok=True)
                image_dest = images_dir / f"{args.publish_date}-{slug}.jpg"
                image_dest.write_bytes(image_bytes)
                written_paths.append(image_dest)

            # Move matching HEADLINES and IMAGE_PROMPT files
            moved_supporting = move_supporting_files(source_file, args.processed_dir)

            validations = validate_output(output_path, normalized)
            written_paths.append(output_path)

            # Include pre-generated TTS audio file in git push if front matter references one
            audio_match = re.search(r"^audio:\s*(\S+)", normalized, re.MULTILINE)
            if audio_match:
                audio_rel = audio_match.group(1).lstrip("/")
                audio_abs = args.blog_root / audio_rel
                if audio_abs.exists():
                    written_paths.append(audio_abs)
                    print(f"[audio] Queued for git push: {audio_rel}")
                else:
                    print(f"[audio] File not found, skipping: {audio_abs}", file=sys.stderr)
        else:
            validations = {
                "filename_pattern": bool(re.match(r"^\d{4}-\d{2}-\d{2}-.+\.md$", output_path.name)),
                "starts_with_front_matter": normalized.startswith("---\n"),
                "has_order_field": bool(re.search(r"^\s*order\s*:\s*\d+", normalized[:500], re.MULTILINE)),
                "no_headline_heading": not bool(HEADING_HEADLINE_RE.search(normalized)),
                "no_the_hook_heading": not bool(THE_HOOK_RE.search(normalized)),
                "no_image_prompt_heading": not bool(IMAGE_PROMPT_RE.search(normalized)),
                "no_mojibake_patterns": not bool(re.search(r"â€|Ã|Â·", normalized)),
                "utf8_no_bom": True,
            }

        reports.append(
            FileReport(
                source=source_file,
                output=output_path,
                title=title,
                slug=slug,
                destination=destination_name,
                score=score,
                score_details=score_details,
                removed=removed,
                mojibake_fixes=mojibake_changes,
                validations=validations,
                moved_supporting_files=moved_supporting,
                image_filename=image_filename,
                image_credit=image_credit,
            )
        )

    if not reports:
        print("Nothing to process")
        return 0

    build_result = run_jekyll_build(args.blog_root) if args.run_build and not args.dry_run else None

    # Pick up any pending publishable files (e.g. _reverted/) not created in this run
    if args.git_push and not args.dry_run:
        for p in collect_pending_publish_paths(args.blog_root):
            if p not in written_paths:
                written_paths.append(p)

    git_result = run_git(args, written_paths) if args.git_push and not args.dry_run else None

    validation_result = None
    if args.git_push and not args.dry_run and git_result and git_result[0]:
        validation_result = validate_remote_push(
            blog_root=args.blog_root,
            written_paths=written_paths,
            remote=args.remote,
            branch=args.branch,
        )

    print_report(reports, build_result, git_result)

    if validation_result is not None:
        ok, details = validation_result
        print(f"\nPost-push validation: {'success' if ok else 'failure'}")
        if details:
            print(details)
        if not ok:
            return 6

    failed_validation = any(not all(r.validations.values()) for r in reports)
    if failed_validation:
        return 2

    if build_result and build_result[0] == "failed":
        return 3

    if git_result and not git_result[0]:
        return 4

    # Cleanup and archive topics.txt
    cleanup_topics_file(args.source_dir.parent)

    return 0


if __name__ == "__main__":
    sys.exit(main())
