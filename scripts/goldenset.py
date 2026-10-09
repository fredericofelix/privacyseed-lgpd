"""Golden set: hand-written fictional sentences with inline entity markup."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parent.parent / "tests" / "golden" / "golden_v0.jsonl"
_MARK = re.compile(r"\[\[([a-z_]+)(?::([a-z_]+))?\|(.+?)\]\]")


@dataclass(frozen=True)
class Span:
    label: str
    start: int
    end: int
    subcategory: str | None = None


@dataclass(frozen=True)
class Example:
    id: str
    text: str
    spans: tuple[Span, ...]
    tags: tuple[str, ...]


def key(label: str, subcategory: str | None) -> str:
    return f"{label}:{subcategory}" if subcategory else label


def parse_marked(marked: str) -> tuple[str, tuple[Span, ...]]:
    parts: list[str] = []
    spans: list[Span] = []
    cursor = length = 0
    for m in _MARK.finditer(marked):
        before = marked[cursor : m.start()]
        parts.append(before)
        length += len(before)
        value = m.group(3)
        spans.append(Span(m.group(1), length, length + len(value), m.group(2)))
        parts.append(value)
        length += len(value)
        cursor = m.end()
    parts.append(marked[cursor:])
    return "".join(parts), tuple(spans)


def load_golden(path: Path = GOLDEN_PATH) -> list[Example]:
    examples = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        text, spans = parse_marked(raw["marked"])
        examples.append(Example(raw["id"], text, spans, tuple(raw.get("tags", []))))
    return examples
