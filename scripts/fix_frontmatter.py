#!/usr/bin/env python3
import re
from pathlib import Path

POSTS_DIR = Path(__file__).resolve().parents[1] / '_posts'

FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
LINE_RE = re.compile(r"^(\s*[-\w]+):\s*(.+)$")

def needs_quoting(val: str) -> bool:
    v = val.strip()
    if not v:
        return False
    if v[0] in ('|', '>', '[', '{', '"', "'", '-'):
        return False
    if v.lower() in ('true', 'false', 'null'):
        return False
    if re.match(r'^\d+$', v):
        return False
    # If value contains YAML-sensitive chars, quote it
    if any(ch in v for ch in [':', '*', '&', '%', '{', '}', '<', '>']):
        return True
    # If value contains unescaped quotes, quote it
    if '"' in v or "'" in v:
        return True
    return False

def quote_value(val: str) -> str:
    v = val.rstrip()
    import re
    from pathlib import Path

    ROOT = Path(__file__).resolve().parents[1]
    POSTS_DIR = ROOT / '_posts'
    REVERTED_DIR = ROOT / '_reverted'

    FRONT_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    LINE_RE = re.compile(r"^(\s*[-\w]+):\s*(.*)$")

    SMART_QUOTES = {
        '“': '"', '”': '"', '‘': "'", '’': "'", '\u2013': '-', '\u2014': '-', '\u2026': '...'
    }

    def normalize_quotes(s: str) -> str:
        for k, v in SMART_QUOTES.items():
            s = s.replace(k, v)
        return s

    def safe_quote(val: str) -> str:
        v = val.strip()
        if v.startswith('|') or v.startswith('>') or v.startswith('[') or v.startswith('{'):
            return val
        if v.startswith('"') or v.startswith("'"):
            return val
        v = v.replace('"', '\\"')
        return '"' + v + '"'

    def clean_front(front: str) -> (str, bool):
        changed = False
        lines = []
        for line in front.splitlines():
            # remove stray terminal output lines
            if any(cmd in line for cmd in ('Get-Content', 'Set-Location', 'Write-Output', 'echo', 'PS C:\\')):
                changed = True
                continue
            line = normalize_quotes(line)
            m = LINE_RE.match(line)
            if m:
                key = m.group(1)
                val = m.group(2).strip()
                # ensure some common keys are quoted
                if key.strip() in ('title', 'description', 'image_credit', 'audio', 'difficulty'):
                    new_val = safe_quote(val)
                    if new_val != val:
                        line = f"{key}: {new_val}"
                        changed = True
                else:
                    # If value contains colon or unbalanced quotes, quote it
                    if ':' in val and not (val.startswith('"') or val.startswith("'")):
                        line = f"{key}: {safe_quote(val)}"
                        changed = True
            lines.append(line)
        return '\n'.join(lines), changed

    def wrap_liquid_raw(txt: str) -> (str, bool):
        changed = False
        # find occurrences of '{{' that look like JSON and are not in raw tags
        idx = 0
        out = ''
        while True:
            start = txt.find('{\{', idx)
            if start == -1:
                out += txt[idx:]
                break
            # skip if already inside a raw block
            raw_open = txt.rfind('{% raw %}', 0, start)
            raw_close = txt.rfind('{% endraw %}', 0, start)
            if raw_open != -1 and (raw_close == -1 or raw_close < raw_open):
                out += txt[idx:start+2]
                idx = start+2
                continue
            # find matching '}}'
            end = txt.find('}}', start)
            if end == -1:
                out += txt[idx:]
                break
            # wrap this segment in raw tags
            out += txt[idx:start]
            segment = txt[start:end+2]
            out += '{% raw %}' + segment + '{% endraw %}'
            changed = True
            idx = end+2
        return out, changed

    def process_path(path: Path) -> bool:
        txt = path.read_text(encoding='utf-8')
        m = FRONT_RE.match(txt)
        changed_any = False
        if m:
            front = m.group(1)
            new_front, changed = clean_front(front)
            if changed:
                changed_any = True
            new_txt = FRONT_RE.sub(f"---\n{new_front}\n---\n", txt, count=1)
        else:
            new_txt = txt

        # fix Liquid JSON collisions by wrapping '{{...}}' in raw
        new_txt2, changed2 = wrap_liquid_raw(new_txt)
        if changed2:
            changed_any = True
        if changed_any:
            path.write_text(new_txt2, encoding='utf-8')
        return changed_any

    def main():
        targets = []
        if POSTS_DIR.exists():
            targets += sorted(POSTS_DIR.glob('*.md'))
        if REVERTED_DIR.exists():
            targets += sorted(REVERTED_DIR.glob('*.md'))
        if not targets:
            print('No markdown targets found')
            return
        modified = []
        for p in targets:
            try:
                if process_path(p):
                    modified.append(p.relative_to(ROOT))
            except Exception as e:
                print('Error processing', p, e)
        if modified:
            print('Modified files:')
            for m in modified:
                print(' -', m)
        else:
            print('No changes needed')

    if __name__ == '__main__':
        main()
