#!/usr/bin/env python3
"""
Auto-assign difficulty badge (Beginner/Intermediate/Advanced) to posts
that don't already have a difficulty: front matter key.

Heuristic:
  - Content mentions advanced keywords  -> Advanced
  - Word count > 1000 OR moderate terms  -> Intermediate
  - Otherwise                             -> Beginner
"""
import re
import glob
import sys
from pathlib import Path

POSTS_DIR = Path(__file__).parent.parent / "github_push" / "blog" / "_posts"

ADVANCED_TERMS = re.compile(
    r'\b(distributed system|consensus|raft|paxos|CRDT|compaction|sharding|'
    r'kernel|syscall|bytecode|jit compiler|lock-free|memory model|'
    r'zero-copy|eBPF|WASM|WebAssembly|formal proof|type theory|'
    r'concurrency model|actor model|byzantine|gossip protocol)\b',
    re.IGNORECASE,
)

BEGINNER_TERMS = re.compile(
    r'\b(introduction|getting started|beginner|basics|fundamentals|'
    r'what is|how to|101|primer|simple|easy|first time|tutorial)\b',
    re.IGNORECASE,
)

FRONT_MATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)


def infer_difficulty(body: str, word_count: int) -> str:
    if ADVANCED_TERMS.search(body):
        return "Advanced"
    if BEGINNER_TERMS.search(body) and word_count < 900:
        return "Beginner"
    if word_count > 1200:
        return "Intermediate"
    return "Intermediate"


updated = 0
for path in sorted(POSTS_DIR.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    m = FRONT_MATTER_RE.match(text)
    if not m:
        continue
    front = m.group(1)
    if "difficulty:" in front:
        continue
    body = text[m.end():]
    word_count = len(body.split())
    difficulty = infer_difficulty(body, word_count)
    new_front = front + f"\ndifficulty: {difficulty}"
    new_text = f"---\n{new_front}\n---\n{body}"
    path.write_text(new_text, encoding="utf-8")
    updated += 1

print(f"Added difficulty badge to {updated} posts.")
