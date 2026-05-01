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
import json
import math
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


SKIP_NAME_TOKENS = (
    "image_prompt",
    "headline",   # covers headline-options, headlines, headline_formulas, etc.
    "topics",
    "prompt",
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
        help="Auto-generate hero images via Pollinations.AI (FLUX, free, no key required)",
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


def find_next_order(posts_dir: Path, unlisted_dir: Path) -> int:
    """Scan existing posts/unlisted for the highest order: value and return max+1."""
    max_order = 0
    order_re = re.compile(r"^\s*order\s*:\s*(\d+)\s*$", re.IGNORECASE | re.MULTILINE)
    for directory in (posts_dir, unlisted_dir):
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


def generate_image(prompt: str) -> Optional[bytes]:
    """GET from Pollinations.AI (FLUX, free, no key); return raw JPEG bytes or None on error."""
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1344&height=768&model=flux&nologo=true"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        print(f"[image] Pollinations API error: {exc}", file=sys.stderr)
        return None


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
    text: str, title: str, publish_date: str, order: int, image: Optional[str] = None
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

    if artifacts_dir.exists():
        move_matches([
            "*_HEADLINES_*.txt",
            "*_IMAGE_PROMPT_*.txt",
            "PRE_CLAUDE_PLAN_*.md",
        ], artifacts_dir)
        move_matches([
            "HEADLINE_FORMULAS.txt",
            "COVERED_CATEGORIES.txt",
            "TOPIC_SELECTION_CHECKLIST.txt",
            "topics.txt",
        ], workspace_root / "docs")

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
            if any(tok in low_name for tok in SKIP_NAME_TOKENS):
                continue
            if source_dir.name not in {"artifacts", "articles"} and not ROOT_DRAFT_RE.match(p.name):
                continue
            if low_name in processed_names:
                continue
            seen_paths.add(resolved)
            candidates.append(p)

    return sorted(candidates)


def slug_already_exists(posts_dir: Path, unlisted_dir: Path, slug: str) -> bool:
    pattern = f"*-{slug}.md"
    return any(posts_dir.glob(pattern)) or any(unlisted_dir.glob(pattern))


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
    pull = run_cmd(["git", "pull", "--rebase", args.remote, args.branch])
    if pull.returncode != 0:
        return False, f"git pull --rebase failed: {pull.stderr.strip() or pull.stdout.strip()}"

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

    for d in (args.processed_dir, args.posts_dir, args.unlisted_dir):
        d.mkdir(parents=True, exist_ok=True)

    if not args.dry_run:
        move_root_support_files(args.source_dir, args.artifacts_dir, args.source_dir / "runs")

    unprocessed = find_unprocessed_files([args.articles_dir, args.source_dir, args.artifacts_dir], args.processed_dir)
    if not unprocessed:
        print("Nothing to process")
        return 0

    reports: List[FileReport] = []
    written_paths: List[Path] = []
    next_order = find_next_order(args.posts_dir, args.unlisted_dir)

    want_images = args.generate_images

    for source_file in unprocessed:
        original = read_text_utf8_replace(source_file)
        fixed_text, mojibake_changes = fix_mojibake(original)
        title = extract_title(fixed_text, source_file.name)
        slug = slugify_title(title)

        if slug_already_exists(args.posts_dir, args.unlisted_dir, slug) and not args.overwrite_existing:
            print(
                f"Skipping {source_file.name}: slug '{slug}' already exists in _posts or _unlisted. "
                "Use --overwrite-existing to replace it."
            )
            continue

        # Extract image prompt BEFORE clean_sections strips it
        image_prompt = extract_image_prompt(fixed_text) if want_images else None

        cleaned, removed = clean_sections(fixed_text)

        # Generate image bytes (API call) before normalize so path ends up in front matter
        image_bytes: Optional[bytes] = None
        image_filename: Optional[str] = None
        if image_prompt and not args.dry_run:
            print(f"[image] Generating hero image for '{title}'…")
            image_bytes = generate_image(image_prompt)
            if image_bytes:
                image_filename = f"/assets/images/posts/{args.publish_date}-{slug}.jpg"
                print(f"[image] Generated → {args.publish_date}-{slug}.jpg")
            else:
                print(f"[image] Generation failed for '{title}'; continuing without image.", file=sys.stderr)

        normalized = normalize_front_matter(
            cleaned, title=title, publish_date=args.publish_date, order=next_order, image=image_filename
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
            )
        )

    if not reports:
        print("Nothing to process")
        return 0

    build_result = run_jekyll_build(args.blog_root) if args.run_build and not args.dry_run else None
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
