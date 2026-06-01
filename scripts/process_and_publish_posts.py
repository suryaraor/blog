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
import base64
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
    # reconfigure() changes encoding on the existing wrapper without replacing it,
    # avoiding the buffer-ownership bug that io.TextIOWrapper reassignment causes
    # when stdout/stderr have no real console (e.g. subprocess capture).
    for _s in (sys.stdout, sys.stderr):
        if _s is not None and hasattr(_s, "reconfigure"):
            try:
                _s.reconfigure(encoding="utf-8")
            except Exception:
                pass

# ── optional TTS module ───────────────────────────────────────────────────────
_WORKSPACE_SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
sys.path.insert(0, str(_WORKSPACE_SCRIPTS))
try:
    from generate_audio import generate_audio_from_markdown as _tts_generate
    _AUDIO_AVAILABLE = True
except ImportError:
    _AUDIO_AVAILABLE = False

# ── optional OpenAI client (DeepSeek-compatible) for Excalidraw diagram ──────
try:
    from openai import OpenAI as _OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False


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
    "_delivery",   # matches *_DELIVERY*.md meta files; avoids false-positives on article titles containing "-delivery-"
    "metadata",
    "completion",
    "scheduled",
    "execution",
    "pre_claude",  # PRE_CLAUDE_PLAN_* pipeline reports
    # planning / admin files that live in the workspace root
    "sprint_",     # sprint_1.md, sprint_2.md, etc.
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
# Matches "## Hook", "## The Hook", "### Hook (2 paragraphs)", etc.
HOOK_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(?:the\s+)?hook\b", re.IGNORECASE)
THE_HOOK_RE = HOOK_HEADING_RE  # backward-compat alias used in validation
IMAGE_PROMPT_RE = re.compile(r"^\s{0,3}#{1,6}\s*image\s+prompt\b", re.IGNORECASE)
# "## Section 1: Title (220 words)" — group 1=hashes, group 2=title without word count
SECTION_N_HEADING_RE = re.compile(
    r"^(\s{0,3}#{1,6})\s*[Ss]ection\s+\d+\s*[:\-–]\s*(.+?)(?:\s*\(\d+\s*words?\))?\s*$"
)
# "## So What?", "## So What? subtitle", "## The So What?", "## The \"So What?\"", etc.
SO_WHAT_HEADING_RE = re.compile(
    r'^\s{0,3}#{1,6}\s*(?:the\s+)?[\'"“”]?so\s+what[?!]?', re.IGNORECASE
)
# "## Conclusion" bare (no subtitle after it)
CONCLUSION_BARE_RE = re.compile(r"^\s{0,3}#{1,6}\s*[Cc]onclusion\s*$")
# "## Conclusion: Subtitle" — group 1=hashes, group 2=subtitle
CONCLUSION_PREFIXED_RE = re.compile(r"^(\s{0,3}#{1,6})\s*[Cc]onclusion\s*[:\-–]\s*(.+?)\s*$")
# Standalone bold structural labels: **Hook (150 words)**, **Section 1: ...**, **So What (80 words)**
STRUCTURAL_BOLD_RE = re.compile(
    r"^\s*\*{1,2}\s*(?:the\s+)?(?:hook\b|section\s+\d+\b|so\s+what[?!]?\b)[^*]*\*{1,2}\s*$",
    re.IGNORECASE,
)
H1_RE = re.compile(r"^\s{0,3}#\s+(.+?)\s*$", re.MULTILINE)
ROOT_DRAFT_RE = re.compile(r"^(?:\d{4}[_-]\d{2}[_-]\d{2}|ARTICLE_|PRE_CLAUDE_PLAN_)", re.IGNORECASE)
# Metadata fields the AI template sometimes emits as orphan lines in the article body
# rather than in the front matter block. We hoist these into the front matter.
_BODY_FM_FIELD_RE = re.compile(r"^\s*(badge|quality_score)\s*:\s*(.+?)\s*$", re.IGNORECASE)


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
        "--no-audio",
        action="store_true",
        help="Disable automatic TTS audio generation (requires GOOGLE_TTS_API_KEY)",
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


def _truncate_title(title: str, max_chars: int = 80) -> str:
    """Trim an overly long title to max_chars at the nearest word boundary."""
    if len(title) <= max_chars:
        return title
    cut = title[:max_chars].rsplit(" ", 1)
    return cut[0].rstrip(" :—-") if len(cut) > 1 else title[:max_chars]


def extract_title(text: str, source_name: str) -> str:
    m = H1_RE.search(text)
    raw = m.group(1).strip() if m else filename_to_title(source_name)
    return _truncate_title(raw)


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
    negative = urllib.parse.quote("text, words, title, letters, labels, watermark, writing, typography")
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1200&height=675&model={model}&nologo=true&seed=42&negative={negative}"
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


def build_gemini_arch_prompt(title: str, image_prompt: Optional[str], category: str = "") -> str:
    """Build an architecture/flow-diagram prompt for Gemini Imagen from the post's building blocks."""
    _DIRECTIVE_LABELS_RE = re.compile(
        r"^\s*(style|lighting|camera|shot|color|mood|tone|composition|background|"
        r"setting|format|aspect|ratio|resolution|quality|render)\s*:",
        re.IGNORECASE,
    )
    concept_parts: List[str] = []
    if image_prompt:
        concept_parts = [
            line.strip()
            for line in image_prompt.splitlines()
            if line.strip() and not _DIRECTIVE_LABELS_RE.match(line)
        ][:4]

    concept_text = "; ".join(concept_parts) if concept_parts else title
    category_hint = f" (category: {category})" if category else ""

    return (
        f"A clean, minimal technical architecture and flow diagram{category_hint}. "
        f"Topic and key building blocks: {concept_text}. "
        f"Represent each major concept as a labeled rounded-rectangle node. "
        f"Each node must include a small relevant icon inside the box (e.g. a database cylinder icon for databases, "
        f"a cloud icon for cloud services, a gear icon for processing steps, a lock icon for security, "
        f"a server rack icon for infrastructure, a code bracket icon for APIs, a chart icon for analytics). "
        f"Connect nodes with directional arrows and concise relationship labels showing how the "
        f"components interact, depend on, or flow into each other. "
        f"Style: white background, flat design, professional color palette using blue, teal, and light gray, "
        f"bold readable sans-serif labels, clean lines, modern tech-infographic aesthetic. "
        f"No photographs, no people, no decorative clipart. Suitable as a 16:9 blog hero image."
    )


def fetch_gemini_image(
    title: str,
    image_prompt: Optional[str],
    api_key: str,
    category: str = "",
) -> Optional[Tuple[bytes, str]]:
    """Generate an architecture diagram via Gemini 2.5 Flash Image; return (jpeg_bytes, attribution) or None."""
    prompt_text = build_gemini_arch_prompt(title, image_prompt, category)
    print(f"[image] Generating architecture diagram via Gemini 2.5 Flash Image…")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models"
        f"/gemini-2.5-flash-image:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt_text}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]},
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[image] Gemini Flash Image error {exc.code}: {body[:300]}", file=sys.stderr)
        return None
    except urllib.error.URLError as exc:
        print(f"[image] Gemini Flash Image connection error: {exc}", file=sys.stderr)
        return None

    try:
        parts = data["candidates"][0]["content"]["parts"]
        image_bytes = next(
            base64.b64decode(p["inlineData"]["data"])
            for p in parts if "inlineData" in p
        )
    except (KeyError, IndexError, StopIteration, Exception) as exc:
        print(f"[image] Gemini Flash Image unexpected response shape: {exc}", file=sys.stderr)
        return None

    if len(image_bytes) < 1024:
        print("[image] Gemini Flash Image returned suspiciously small data; skipping.", file=sys.stderr)
        return None

    attribution = "Architecture diagram generated by [Google Gemini](https://ai.google.dev)"
    return image_bytes, attribution


_DIAGRAM_MODEL = "deepseek-chat"
_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
_DIAGRAM_SYSTEM = (
    "You are an expert Excalidraw diagram JSON generator. "
    "Output ONLY valid JSON — no prose, no markdown, no code fences."
)
_DIAGRAM_USER_TMPL = """\
Generate an Excalidraw diagram JSON for this blog post.

Title: {title}
Diagram concept: {image_prompt}

Output valid JSON only. No other text.

JSON wrapper:
{{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {{"viewBackgroundColor": "#ffffff", "gridSize": 20}},
  "files": {{}}
}}

Required fields on every element: id (descriptive string), x, y, width, height,
seed (random int), version:1, versionNonce (random int), isDeleted:false,
groupIds:[], link:null, locked:false

RECTANGLE: type "rectangle", add roundness:{{"type":3}}, boundElements lists its text and arrows
ELLIPSE: type "ellipse", same fields, no roundness
TEXT free: type "text", containerId:null, originalText same as text, fontSize, fontFamily:3,
  textAlign ("left"/"center"), verticalAlign ("top"/"middle"), lineHeight:1.25
TEXT inside shape: same but containerId = parent id; add {{"id":text_id,"type":"text"}} to parent boundElements
ARROW: type "arrow", points:[[0,0],[dx,dy]], startBinding:{{"elementId":src,"focus":0,"gap":2}},
  endBinding:{{"elementId":dst,"focus":0,"gap":2}}, startArrowhead:null, endArrowhead:"arrow";
  add to both endpoint shapes boundElements

Semantic colors:
AI/LLM → fill #ddd6fe stroke #6d28d9
Process → fill #3b82f6 stroke #1e3a5f (text #ffffff inside)
Start → fill #fed7aa stroke #c2410c
End/Success → fill #a7f3d0 stroke #047857
Warning → fill #fef3c7 stroke #b45309 (text #374151)
Failure/Error → fill #fecaca stroke #b91c1c
Failure callout → fill #fee2e2 stroke #dc2626 strokeStyle:dashed
Code box → fill #1e293b stroke #1e293b (text #22c55e)
Title → strokeColor #1e40af | Subtitle → #3b82f6 | Body → #64748b
On-light fills → #374151 | On-dark fills → #ffffff

Rules: roughness:0 and opacity:100 on ALL elements. Pipeline flows left-to-right
with shapes ~180×80 spaced ~60px apart. Failure callouts hang below pipeline stages
connected by dashed red arrows. Diagram ≤1300px wide, ≤750px tall. Include a large
title (fontSize:28, strokeColor:#1e40af) and subtitle at top. Shape choice mirrors
concept: pipeline→assembly line, failure modes→callout boxes, code→dark box.
"""


def generate_excalidraw_diagram(
    title: str,
    image_prompt: Optional[str],
    publish_date: str,
    slug: str,
    artifacts_dir: Path,
    images_dir: Path,
    workspace_root: Path,
    api_key: str,
) -> Optional[Tuple[Path, str]]:
    """Generate an Excalidraw diagram via DeepSeek and render to PNG.
    Returns (png_path, attribution) or None on failure.
    """
    render_script = workspace_root / ".claude" / "skills" / "excalidraw-diagram" / "references" / "render_svg.py"
    if not render_script.exists():
        print(f"[image] render_svg.py not found at {render_script}; skipping Excalidraw", file=sys.stderr)
        return None

    concept = image_prompt or f"Architecture diagram for: {title}"
    user_prompt = _DIAGRAM_USER_TMPL.format(title=title, image_prompt=concept)

    print(f"[image] Generating Excalidraw diagram via {_DIAGRAM_MODEL} …")
    try:
        client = _OpenAI(api_key=api_key, base_url=_DEEPSEEK_BASE_URL)
        resp = client.chat.completions.create(
            model=_DIAGRAM_MODEL,
            max_tokens=8192,
            messages=[
                {"role": "system", "content": _DIAGRAM_SYSTEM},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[image] DeepSeek diagram call failed: {exc}", file=sys.stderr)
        return None

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fenced:
        raw = fenced.group(1)
    brace = raw.find("{")
    if brace > 0:
        raw = raw[brace:]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"[image] Invalid JSON from DeepSeek diagram: {exc}", file=sys.stderr)
        return None

    if not data.get("elements"):
        print("[image] Empty diagram elements from DeepSeek; skipping", file=sys.stderr)
        return None

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    excalidraw_path = artifacts_dir / f"{publish_date}-{slug}.excalidraw"
    excalidraw_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    png_dest = images_dir / f"{publish_date}-{slug}.png"
    images_dir.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [sys.executable, str(render_script), str(excalidraw_path), "--output", str(png_dest)],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            print(f"[image] Excalidraw render failed: {result.stderr[:300]}", file=sys.stderr)
            return None
    except Exception as exc:
        print(f"[image] Excalidraw render error: {exc}", file=sys.stderr)
        return None

    attribution = "Architecture diagram generated via DeepSeek + Excalidraw"
    print(f"[image] Excalidraw diagram → {png_dest.name}")
    return png_dest, attribution


def _inject_audio_field(text: str, audio_url: str) -> str:
    """Insert audio: field before the closing --- of the front matter block."""
    if not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    return text[:end] + f"\naudio: {audio_url}" + text[end:]


def clean_sections(text: str) -> Tuple[str, Dict[str, int]]:
    lines = text.splitlines()
    out: List[str] = []
    i = 0
    removed_headline_blocks = 0
    removed_hook_headings = 0
    removed_image_prompts = 0
    removed_section_labels = 0
    removed_so_what_headings = 0
    removed_structural_bold = 0

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

        # Hook heading: ## Hook, ## The Hook, ### Hook (2 paragraphs), etc.
        if HOOK_HEADING_RE.match(line):
            removed_hook_headings += 1
            i += 1
            continue

        # Section N: Title → strip the "Section N:" prefix, keep the title
        m = SECTION_N_HEADING_RE.match(line)
        if m:
            hashes, title = m.group(1), m.group(2).strip()
            out.append(f"{hashes} {title}")
            removed_section_labels += 1
            i += 1
            continue

        # So What? headings (any variant) → remove the heading line
        if SO_WHAT_HEADING_RE.match(line):
            removed_so_what_headings += 1
            i += 1
            continue

        # Bare Conclusion heading → remove
        if CONCLUSION_BARE_RE.match(line):
            removed_so_what_headings += 1
            i += 1
            continue

        # Conclusion: Subtitle → strip prefix, keep subtitle as heading
        m = CONCLUSION_PREFIXED_RE.match(line)
        if m:
            hashes, title = m.group(1), m.group(2).strip()
            out.append(f"{hashes} {title}")
            removed_section_labels += 1
            i += 1
            continue

        # Standalone bold structural labels: **Hook (150 words)**, **Section 1: ...**, **So What**
        if STRUCTURAL_BOLD_RE.match(line):
            removed_structural_bold += 1
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
        "section_labels": removed_section_labels,
        "so_what_headings": removed_so_what_headings,
        "structural_bold": removed_structural_bold,
    }


def _strip_leading_code_fence(text: str) -> str:
    """Strip an outer code fence that the model wrapped around its entire response.

    Handles the case where the body (after real front matter is extracted) still
    starts with ```[lang] ... ``` wrapping a duplicate front matter block and the
    article content.  Only strips when the fence opens on the very first line.
    """
    stripped = text.lstrip("\n")
    m = re.match(r"^```[a-zA-Z]*\n(.*\n?)```[ \t]*$", stripped, re.DOTALL)
    if m:
        return m.group(1).rstrip("\n")
    # Also handle an unclosed opening fence (no matching closing ```)
    m2 = re.match(r"^```[a-zA-Z]*\n", stripped)
    if m2:
        return stripped[m2.end():]
    return text


def _strip_leading_orphan_fm(text: str) -> str:
    """Strip an unclosed front matter block at the start of text.

    The model sometimes emits ``---\\nlayout: ...\\ntitle: ...\\n`` without a
    closing ``---``.  That block ends up embedded in the body after
    normalize_front_matter prepends the real header.  Remove it here so the
    body starts cleanly at the first heading or paragraph.
    """
    # First remove any outer code fence the model may have added
    text = _strip_leading_code_fence(text)
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    # Walk forward: if we find a closing --- within 30 lines it's a REAL block
    for i in range(1, min(30, len(lines))):
        if lines[i].strip() == "---":
            return text  # properly closed — leave it alone
        if re.match(r"^\s{0,3}#{1,6}\s+", lines[i]):
            # Found a heading before any closing --- → definitely unclosed FM
            break
    # The block is unclosed.  Advance past YAML-looking lines + blank lines to
    # find where the real content starts.
    i = 1
    while i < len(lines):
        stripped = lines[i].strip()
        if stripped == "":
            i += 1
            continue
        if re.match(r"^[A-Za-z_][\w]*\s*:", stripped):
            i += 1  # looks like a YAML key: value line
            continue
        break  # first non-YAML, non-blank line — real content starts here
    return "\n".join(lines[i:]).lstrip("\n")


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
        # Unclosed front matter — parse what we can, treat rest as body
        front_lines = []
        for idx in range(1, len(lines)):
            stripped = lines[idx].strip()
            if stripped == "" or re.match(r"^\s{0,3}#{1,6}\s+", lines[idx]):
                body_start = idx
                break
            front_lines.append(lines[idx])
        else:
            body_start = len(lines)
        body = "\n".join(lines[body_start:]).lstrip("\n")
        return front_lines, body

    front_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return front_lines, body


def normalize_front_matter(
    text: str, title: str, publish_date: str, order: int,
    image: Optional[str] = None, image_credit: Optional[str] = None
) -> str:
    front_lines, body = parse_front_matter(text)
    # Remove any orphan front matter block that slipped into the body
    body = _strip_leading_orphan_fm(body)

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

    # Hoist badge/quality_score that the AI template sometimes emits as orphan
    # YAML lines in the body (after the hook section) instead of in front matter.
    extra_keys = {
        re.match(r"^\s*(\w+)\s*:", l).group(1).lower()
        for l in extra_lines
        if re.match(r"^\s*(\w+)\s*:", l)
    }
    clean_body: List[str] = []
    for line in body.splitlines():
        m = _BODY_FM_FIELD_RE.match(line)
        if m and m.group(1).lower() not in extra_keys:
            extra_lines.append(f"{m.group(1).lower()}: {m.group(2)}")
            extra_keys.add(m.group(1).lower())
        else:
            clean_body.append(line)
    body = "\n".join(clean_body)

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


def inject_hero_into_body(
    text: str, image_filename: str, title: str, image_credit: Optional[str] = None
) -> str:
    """Insert the hero image into the post body after the intro, before the first ## heading.

    The image: front matter field is kept for OG/Twitter meta tags.
    """
    front_lines, body = parse_front_matter(text)

    escaped_alt = title.replace('"', '&quot;').replace("'", "&#39;")
    img_parts = [
        '<figure class="post-hero-image">',
        f'<img class="post-hero" src="{image_filename}" alt="Hero image for {escaped_alt}" loading="lazy">',
    ]
    if image_credit:
        img_parts.append(f"<figcaption>{image_credit}</figcaption>")
    img_parts.append("</figure>")
    img_block = "\n".join(img_parts)

    lines = body.splitlines()
    insert_idx = None

    # Prefer inserting right before the first ## heading (after intro paragraphs)
    for i, line in enumerate(lines):
        if re.match(r"^\s{0,3}##\s+", line):
            insert_idx = i
            break

    if insert_idx is None:
        # No ## heading — insert after the H1's first paragraph
        for i, line in enumerate(lines):
            if re.match(r"^\s{0,3}#\s+", line):
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                while j < len(lines) and lines[j].strip():
                    j += 1
                insert_idx = j
                break

    if insert_idx is None:
        insert_idx = len(lines)

    new_lines = lines[:insert_idx] + [img_block, ""] + lines[insert_idx:]
    new_body = "\n".join(new_lines)

    if front_lines is not None:
        return "---\n" + "\n".join(front_lines) + "\n---\n" + new_body
    return new_body


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
    source_slug: str          # slug derived from source filename (for detecting rewrites)
    destination: str
    score: int
    score_details: List[Tuple[str, str, int]]
    removed: Dict[str, int]
    mojibake_fixes: List[str]
    validations: Dict[str, bool]
    moved_supporting_files: List[str] = None
    image_filename: Optional[str] = None
    image_credit: Optional[str] = None
    audio_filename: Optional[str] = None
    audio_size_kb: Optional[int] = None
    audio_reason: Optional[str] = None
    quality_score: Optional[float] = None


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
    except FileNotFoundError:
        return "warning", "bundle not installed — install Ruby+Bundler to enable local render validation"

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
        if rep.source_slug and rep.source_slug != rep.slug:
            print(f"Title rewrite: {rep.source_slug} → {rep.slug}")
        print(f"Destination: {rep.destination}")
        if rep.quality_score is not None:
            badge = ""
            if rep.quality_score >= 9.0:
                badge = "  [editors_pick]"
            elif rep.quality_score >= 8.5:
                badge = "  [featured]"
            print(f"Quality score: {rep.quality_score:.1f}/10{badge}")
        else:
            print("Quality score: not scored  (run via run_agent.py to score)")
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

        if rep.audio_filename:
            size_str = f"  ({rep.audio_size_kb} KB)" if rep.audio_size_kb is not None else ""
            print(f"Audio: {rep.audio_filename}{size_str}")
        else:
            reason_str = f"  ({rep.audio_reason})" if rep.audio_reason else ""
            print(f"Audio: none{reason_str}")

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
        if status == "warning":
            print(f"\nJekyll build: ⚠  SKIPPED — {details}", file=sys.stderr)
        else:
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
    voice_reference_wav = os.environ.get("VOICE_REFERENCE_WAV", "") or None
    gemini_image_key = os.environ.get("GOOGLE_AI_STUDIO_IMAGE_API_KEY", "")

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
        source_slug = slugify_title(filename_to_title(source_file.name))

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

        # Use pre-rendered Excalidraw diagram if one already exists at the expected path.
        # The Excalidraw skill (run interactively by Claude Code) saves PNG before publish.
        if not args.dry_run:
            _images_dir = args.blog_root / "assets" / "images" / "posts"
            for _ext in (".png", ".jpg"):
                _pre = _images_dir / f"{args.publish_date}-{slug}{_ext}"
                if _pre.exists():
                    image_filename = f"/assets/images/posts/{args.publish_date}-{slug}{_ext}"
                    want_images = False
                    written_paths.append(_pre)
                    print(f"[image] Using pre-rendered diagram -> {_pre.name}")
                    break

        # Generate Excalidraw diagram via DeepSeek (preferred; runs even without a Claude Code session)
        if want_images and not args.dry_run:
            _deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")
            if _OPENAI_AVAILABLE and _deepseek_key:
                _exc_result = generate_excalidraw_diagram(
                    title=title,
                    image_prompt=image_prompt,
                    publish_date=args.publish_date,
                    slug=slug,
                    artifacts_dir=args.artifacts_dir,
                    images_dir=args.blog_root / "assets" / "images" / "posts",
                    workspace_root=args.blog_root.parent.parent,
                    api_key=_deepseek_key,
                )
                if _exc_result:
                    _png_path, image_credit = _exc_result
                    image_filename = f"/assets/images/posts/{args.publish_date}-{slug}.png"
                    written_paths.append(_png_path)
                    want_images = False
            elif not _OPENAI_AVAILABLE:
                print("[image] openai package not installed; skipping Excalidraw (pip install openai)", file=sys.stderr)
            else:
                print("[image] DEEPSEEK_API_KEY not set; skipping Excalidraw diagram", file=sys.stderr)

        if want_images and not args.dry_run:
            # Try Gemini Imagen 3 first (architecture/flow diagram).
            # On any error or missing key, fall back to the configured style.
            result: Optional[Tuple[bytes, str]] = None
            if gemini_image_key:
                result = fetch_gemini_image(title, image_prompt, gemini_image_key, category=post_category)
                if result:
                    image_bytes, image_credit = result
                    image_filename = f"/assets/images/posts/{args.publish_date}-{slug}.jpg"
                    print(f"[image] Gemini diagram -> {args.publish_date}-{slug}.jpg")
                else:
                    print("[image] Gemini Imagen failed; falling back to configured style.", file=sys.stderr)

            if not result:
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

        # Use a per-file datetime so posts generated on the same day sort correctly.
        # The filename still uses args.publish_date (YYYY-MM-DD) for stable URLs.
        file_datetime = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        normalized = normalize_front_matter(
            cleaned, title=title, publish_date=file_datetime, order=next_order,
            image=image_filename, image_credit=image_credit
        )
        if image_filename and not args.dry_run:
            normalized = inject_hero_into_body(normalized, image_filename, title, image_credit)
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

        # Extract quality score and audio path from normalized front matter (set by run_agent.py)
        _qs_match = re.search(r"^\s*quality_score\s*:\s*([\d.]+)", normalized, re.MULTILINE)
        quality_score: Optional[float] = float(_qs_match.group(1)) if _qs_match else None

        audio_filename: Optional[str] = None
        audio_size_kb: Optional[int] = None
        audio_reason: Optional[str] = None

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

            # Generate TTS audio if not already present in front matter
            audio_match = re.search(r"^audio:\s*(\S+)", normalized, re.MULTILINE)
            if audio_match:
                audio_rel = audio_match.group(1).lstrip("/")
                audio_abs = args.blog_root / audio_rel
                if audio_abs.exists():
                    written_paths.append(audio_abs)
                    audio_filename = audio_rel
                    audio_size_kb = audio_abs.stat().st_size // 1024
                    print(f"[audio] Queued for git push: {audio_rel}  ({audio_size_kb} KB)")
                else:
                    audio_reason = "file not found"
                    print(f"[audio] File not found, skipping: {audio_abs}", file=sys.stderr)
            elif _AUDIO_AVAILABLE and not getattr(args, "no_audio", False):
                audio_dir = args.blog_root / "assets" / "audio" / "posts"
                audio_dir.mkdir(parents=True, exist_ok=True)
                audio_wav = audio_dir / f"{args.publish_date}-{slug}.wav"
                audio_url = f"/assets/audio/posts/{args.publish_date}-{slug}.wav"
                try:
                    if audio_wav.exists():
                        # Reuse WAV already generated by run_agent.py — no model load needed
                        size = audio_wav.stat().st_size
                        print(f"[audio] Reusing pre-generated audio → {audio_wav.name}  ({size // 1024} KB)")
                    else:
                        print(f"\n[audio] Generating TTS audio (VoxCPM2)…")
                        size = _tts_generate(normalized, audio_wav, reference_audio=voice_reference_wav)
                        print(f"[audio] Saved → {audio_wav.name}  ({size // 1024} KB)")
                    updated = _inject_audio_field(normalized, audio_url)
                    output_path.write_text(updated, encoding="utf-8", newline="\n")
                    written_paths.append(audio_wav)
                    audio_filename = audio_url.lstrip("/")
                    audio_size_kb = size // 1024
                except Exception as exc:
                    audio_reason = f"TTS error: {exc}"
                    print(f"[audio] Failed: {exc}; continuing without audio", file=sys.stderr)
            else:
                if not _AUDIO_AVAILABLE:
                    audio_reason = "generate_audio module not found"
                else:
                    audio_reason = "--no-audio flag"
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
                source_slug=source_slug,
                destination=destination_name,
                score=score,
                score_details=score_details,
                removed=removed,
                mojibake_fixes=mojibake_changes,
                validations=validations,
                moved_supporting_files=moved_supporting,
                image_filename=image_filename,
                image_credit=image_credit,
                audio_filename=audio_filename,
                audio_size_kb=audio_size_kb,
                audio_reason=audio_reason,
                quality_score=quality_score,
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
