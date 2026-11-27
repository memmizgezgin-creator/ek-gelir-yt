"""Shared helpers: paths, script parsing, logging."""
from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
ASSETS = ROOT / "assets"
OUT = ROOT / "out"
MODELS = ROOT / "models"
TOPICS = ROOT / "topics.json"


def log(msg: str) -> None:
    print(f"[ek-gelir-yt] {msg}", flush=True)


def fail(msg: str) -> None:
    print(f"[ek-gelir-yt] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


@dataclass
class Section:
    index: int
    title: str
    image_keys: list[str]
    paragraphs: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n\n".join(self.paragraphs)


@dataclass
class Script:
    meta: dict
    sections: list[Section]

    @property
    def vid(self) -> str:
        return str(self.meta["id"])

    @property
    def word_count(self) -> int:
        return sum(len(s.text.split()) for s in self.sections)


def find_script(vid: str) -> Path:
    hits = sorted(SCRIPTS.glob(f"{vid}-*.md"))
    hits = [h for h in hits if not h.name.endswith("-check.md")]
    if not hits:
        fail(f"no script for id {vid} in {SCRIPTS}")
    return hits[0]


def parse_script(path: Path) -> Script:
    raw = path.read_text(encoding="utf-8")
    meta: dict = {}
    m = re.match(r"^---\n(.*?)\n---\n", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip('"')
        raw = raw[m.end():]
    sections: list[Section] = []
    cur: Section | None = None
    buf: list[str] = []

    def flush_par():
        if cur is not None and buf:
            par = " ".join(x.strip() for x in buf).strip()
            if par:
                cur.paragraphs.append(par)
        buf.clear()

    for line in raw.splitlines():
        if line.startswith("## "):
            flush_par()
            cur = Section(len(sections) + 1, line[3:].strip(), [])
            sections.append(cur)
        elif cur is not None and line.lower().startswith("images:"):
            cur.image_keys = [k.strip() for k in line.split(":", 1)[1].split(",") if k.strip()]
        elif line.lower().startswith("on screen:"):
            continue
        elif not line.strip():
            flush_par()
        elif cur is not None:
            buf.append(line)
    flush_par()
    if "id" not in meta:
        fail(f"{path.name}: front matter needs an id")
    return Script(meta, sections)


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])", text.strip())
    return [p.strip() for p in parts if p.strip()]


def load_json(p: Path, default=None):
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, data) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
