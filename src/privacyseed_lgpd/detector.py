"""Detector: runs recognizers, resolves overlaps and anonymizes."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .entity import Entity


def _overlaps(a: Entity, b: Entity) -> bool:
    return a.start < b.end and b.start < a.end


def resolve(candidates: Iterable[Entity]) -> tuple[list[Entity], list[Entity]]:
    """Pick non-overlapping spans; return (kept, discarded), both sorted by start.

    Rules, in order: a span that passed check-digit validation wins; then the
    longest span; then the highest score; then input order (the sort is stable).
    """
    candidates = list(candidates)
    ranked = sorted(
        (c for c in candidates if c.check != "failed"),
        key=lambda e: (e.check == "passed", e.end - e.start, e.score),
        reverse=True,
    )
    kept: list[Entity] = []
    for e in ranked:
        if not any(_overlaps(e, k) for k in kept):
            kept.append(e)
    discarded: list[Entity] = []
    for f in (c for c in candidates if c.check == "failed"):
        if not any(_overlaps(f, k) for k in kept) and not any(_overlaps(f, d) for d in discarded):
            discarded.append(f)
    return sorted(kept, key=lambda e: e.start), sorted(discarded, key=lambda e: e.start)


def redact(text: str, entities: Sequence[Entity], tags: dict[str, str]) -> str:
    """Replace each (non-overlapping) entity by its tag, using offsets only."""
    parts: list[str] = []
    cursor = 0
    for e in sorted(entities, key=lambda e: e.start):
        parts.append(text[cursor : e.start])
        parts.append(tags[e.label])
        cursor = e.end
    parts.append(text[cursor:])
    return "".join(parts)
