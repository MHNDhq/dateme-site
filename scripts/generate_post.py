#!/usr/bin/env python3
"""Generate one blog post headlessly via `claude -p`, lint it, and rebuild the blog.

Picks the first topic in blog/topics.txt without an existing file in blog/src/
(or takes an explicit "slug | title | angle" line as argv). Does NOT deploy —
review the post, then run scripts/deploy.sh.

Usage:
  .venv/bin/python scripts/generate_post.py            # next topic from backlog
  .venv/bin/python scripts/generate_post.py "my-slug | My Title | query/angle"
"""
import datetime
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "blog" / "src"


def find_claude():
    candidates = [os.environ.get("CLAUDE_BIN"),
                  os.path.expanduser("~/.local/bin/claude"),
                  "/opt/homebrew/bin/claude",
                  shutil.which("claude")]
    for c in candidates:
        if c and os.path.exists(c) and "cmux-cli-shims" not in c:
            return c
    sys.exit("claude CLI not found — set CLAUDE_BIN or install claude code")


CLAUDE = find_claude()

BANNED = [
    "in today's digital age", "game-changer", "game changer", "unlock your",
    "elevate your", "dive in", "it's important to note", "partner in crime",
    "photofeeler", "roast.dating", "rizzgpt", "looksmax",
]


def pick_topic(arg):
    if arg:
        line = arg
    else:
        line = None
        for raw in (ROOT / "blog" / "topics.txt").read_text().splitlines():
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            slug = raw.split("|")[0].strip()
            if not (SRC / f"{slug}.md").exists():
                line = raw
                break
        if line is None:
            sys.exit("topics.txt: backlog exhausted — add topics before generating.")
    slug, title, angle = (part.strip() for part in line.split("|", 2))
    return slug, f'"{title}" — {angle}'


def lint(path):
    text = path.read_text(encoding="utf-8")
    problems = []
    low = text.lower()
    for phrase in BANNED:
        if phrase in low:
            problems.append(f"banned phrase: {phrase!r}")
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        problems.append("missing frontmatter")
    else:
        fm = dict(line.partition(":")[::2] for line in m.group(1).splitlines())
        fm = {k.strip(): v.strip() for k, v in fm.items()}
        if len(fm.get("title", "")) > 65:
            problems.append(f"title too long ({len(fm['title'])} chars)")
        if len(fm.get("description", "")) > 160:
            problems.append(f"description too long ({len(fm['description'])} chars)")
    words = len(re.findall(r"\w+", text))
    if not 700 <= words <= 1900:
        problems.append(f"word count {words} outside 700-1900")
    if "## FAQ" not in text:
        problems.append("missing ## FAQ section")
    if "http" not in text:
        problems.append("no source links at all")
    return problems


def main():
    slug, topic = pick_topic(" ".join(sys.argv[1:]).strip() or None)
    dest = SRC / f"{slug}.md"
    prompt = (ROOT / "automation" / "post-prompt.md").read_text()
    prompt = (prompt.replace("{{DEST}}", str(dest))
                    .replace("{{SLUG}}", slug)
                    .replace("{{TOPIC}}", topic)
                    .replace("{{DATE}}", datetime.date.today().isoformat()))

    print(f"generating: {slug}")
    SRC.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [CLAUDE, "-p", prompt,
         "--model", "sonnet",
         "--permission-mode", "acceptEdits",
         "--allowedTools", "WebSearch,WebFetch,Read,Write,Glob"],
        cwd=ROOT, capture_output=True, text=True, timeout=1200)
    print(result.stdout.strip()[-2000:])
    if result.returncode != 0:
        sys.exit(f"claude -p failed ({result.returncode}):\n{result.stderr[-2000:]}")
    if not dest.exists():
        sys.exit(f"claude finished but {dest} was not written")

    problems = lint(dest)
    if problems:
        quarantine = dest.with_suffix(".md.rejected")
        dest.rename(quarantine)
        sys.exit("LINT FAILED — post quarantined at "
                 f"{quarantine}:\n  " + "\n  ".join(problems))

    subprocess.run([str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "build_blog.py")], check=True, cwd=ROOT)
    print(f"OK: {dest.relative_to(ROOT)} written, linted, and built.")
    print("Review it, then publish with: scripts/deploy.sh")


if __name__ == "__main__":
    main()
