"""Collect image prompt sections from Jekyll posts into a single text file.

The script scans _posts/*.md, extracts any section headed by an Image Prompt
marker, and writes the combined results to image_prompt.txt in the repository
root. The source posts are not modified.
"""

from __future__ import annotations

import argparse
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional


ROOT = Path(__file__).resolve().parents[1]
POSTS_DIR = ROOT / "_posts"
DEFAULT_OUTPUT = ROOT / "image_prompt.txt"


IMAGE_PROMPT_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(?:image\s*prompt(?:\s+for\s+this\s+article)?|image\s*prompt)\b.*$", re.IGNORECASE)
IMAGE_PROMPT_BOLD_RE = re.compile(r"^\s*\*\*\s*image\s*prompt\s*:?\s*\*\*\s*$", re.IGNORECASE)
MARKDOWN_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
HORIZONTAL_RULE_RE = re.compile(r"^\s*[-*_]{3,}\s*$")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$", re.IGNORECASE)


@dataclass
class PromptEntry:
    post_file: Path
    title: str
    date: str
    prompt: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract image prompt sections from Jekyll posts into a text file."
    )
    parser.add_argument(
        "--posts-dir",
        type=Path,
        default=POSTS_DIR,
        help="Directory containing Jekyll posts (default: _posts).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output text file path (default: image_prompt.txt).",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        default=None,
        help="Optional directory where original posts are copied after extraction.",
    )
    parser.add_argument(
        "--strip-source-sections",
        action="store_true",
        help="Remove extracted image prompt sections from the source posts in place.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    posts_dir = args.posts_dir.resolve()
    output_path = args.output.resolve()
    archive_dir = args.archive_dir.resolve() if args.archive_dir else None

    if not posts_dir.exists():
        raise SystemExit(f"Posts directory not found: {posts_dir}")

    entries = collect_prompts(posts_dir)
    write_output(output_path, entries)

    if archive_dir is not None:
        archive_dir.mkdir(parents=True, exist_ok=True)
        for post_path in sorted(posts_dir.glob("*.md")):
            shutil.copy2(post_path, archive_dir / post_path.name)

    if args.strip_source_sections:
        strip_prompts_from_posts(posts_dir)

    print(f"Scanned {len(list(posts_dir.glob('*.md')))} posts")
    print(f"Extracted {len(entries)} image prompt sections")
    print(f"Wrote {output_path}")
    if archive_dir is not None:
        print(f"Archived source posts to {archive_dir}")
    if args.strip_source_sections:
        print("Removed image prompt sections from source posts")
    return 0


def collect_prompts(posts_dir: Path) -> List[PromptEntry]:
    entries: List[PromptEntry] = []

    for post_path in sorted(posts_dir.glob("*.md")):
        text = read_text(post_path)
        title = extract_title(text, post_path)
        date = extract_date(post_path)
        prompt_blocks = extract_prompt_blocks(text)

        for prompt in prompt_blocks:
            cleaned_prompt = clean_prompt(prompt)
            if cleaned_prompt:
                entries.append(
                    PromptEntry(
                        post_file=post_path,
                        title=title,
                        date=date,
                        prompt=cleaned_prompt,
                    )
                )

    return entries


def strip_prompts_from_posts(posts_dir: Path) -> None:
    for post_path in sorted(posts_dir.glob("*.md")):
        original = read_text(post_path)
        updated = remove_prompt_sections(original)
        if updated != original:
            post_path.write_text(updated, encoding="utf-8", newline="\n")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def extract_date(post_path: Path) -> str:
    match = DATE_RE.match(post_path.name)
    return match.group(1) if match else ""


def extract_title(text: str, post_path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()

    fallback = DATE_RE.match(post_path.name)
    if fallback:
        slug = fallback.group(2).replace("-", " ")
        return slug.title()

    return post_path.stem


def extract_prompt_blocks(text: str) -> List[str]:
    lines = text.splitlines()
    blocks: List[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if is_image_prompt_marker(line):
            block_lines, next_index = collect_block(lines, index + 1)
            if block_lines:
                blocks.append("\n".join(block_lines))
            index = next_index
            continue

        index += 1

    return blocks


def remove_prompt_sections(text: str) -> str:
    lines = text.splitlines()
    kept: List[str] = []
    index = 0

    while index < len(lines):
        line = lines[index]

        if is_image_prompt_marker(line):
            index += 1
            while index < len(lines):
                next_line = lines[index]
                if is_block_terminator(next_line) or is_image_prompt_marker(next_line):
                    break
                index += 1
            while index < len(lines) and not lines[index].strip():
                index += 1
            continue

        kept.append(line)
        index += 1

    result = "\n".join(kept).rstrip() + "\n"
    return result


def is_image_prompt_marker(line: str) -> bool:
    return bool(IMAGE_PROMPT_HEADING_RE.match(line) or IMAGE_PROMPT_BOLD_RE.match(line))


def collect_block(lines: List[str], start_index: int) -> tuple[list[str], int]:
    block: List[str] = []
    index = start_index

    while index < len(lines):
        line = lines[index]

        if is_block_terminator(line):
            break

        if IMAGE_PROMPT_HEADING_RE.match(line) or IMAGE_PROMPT_BOLD_RE.match(line):
            break

        block.append(line)
        index += 1

    return block, index


def is_block_terminator(line: str) -> bool:
    stripped = line.strip()
    return bool(
        MARKDOWN_HEADING_RE.match(line)
        or HORIZONTAL_RULE_RE.match(line)
        or stripped.lower().startswith("**word count")
        or stripped.lower().startswith("**status")
    )


def clean_prompt(raw_prompt: str) -> str:
    lines = raw_prompt.splitlines()
    cleaned: List[str] = []
    previous_blank = False

    for line in lines:
        stripped = line.rstrip()

        if stripped.strip() in {"```", "```markdown", "```text"}:
            continue

        if not stripped.strip():
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue

        previous_blank = False
        cleaned.append(fix_mojibake(stripped))

    while cleaned and not cleaned[0].strip():
        cleaned.pop(0)
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    return "\n".join(cleaned).strip()


def fix_mojibake(text: str) -> str:
    replacements = [
        ("â€”", "—"),
        ("â€“", "–"),
        ("â€™", "’"),
        ("â€œ", "“"),
        ("â€", "”"),
        ("â€", "”"),
        ("Â·", "·"),
        ("â€¢", "•"),
        ("clichÃ©", "cliché"),
        ("naÃ¯vetÃ©", "naïveté"),
        ("ÃƒÆ'‚¬â€", "–"),
    ]

    fixed = text
    for old, new in replacements:
        fixed = fixed.replace(old, new)

    return fixed


def write_output(output_path: Path, entries: Iterable[PromptEntry]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content_lines: List[str] = ["# Image Prompts"]

    entry_list = list(entries)
    if not entry_list:
        content_lines.extend(["", "No image prompt sections were found."])
    else:
        for entry in entry_list:
            content_lines.extend(
                [
                    "",
                    "---",
                    f"Title: {entry.title}",
                    f"Date: {entry.date}",
                    f"Source: {entry.post_file.name}",
                    "",
                    entry.prompt,
                ]
            )

    content = "\n".join(content_lines).rstrip() + "\n"
    output_path.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    raise SystemExit(main())