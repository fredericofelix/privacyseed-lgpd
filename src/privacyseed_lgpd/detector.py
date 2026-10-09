"""Detector: runs recognizers, resolves overlaps and anonymizes."""

from __future__ import annotations

import dataclasses
import importlib.util
import warnings
from collections.abc import Iterable, Sequence

from .entity import Entity, Result
from .recognizers.base import Recognizer
from .recognizers.regex import RegexRecognizer
from .taxonomy import load_taxonomy

ML_MISSING = (
    "privacyseed-lgpd[ml] is not installed: only identifiers, e-mail, phone, CEP and dates "
    "of birth are detected; names, addresses and sensitive data are not. "
    "Install with: pip install 'privacyseed-lgpd[ml]'"
)

_ml_warning_shown = False


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


def ml_available() -> bool:
    return importlib.util.find_spec("gliner2") is not None and importlib.util.find_spec("torch") is not None


def _warn_ml_missing_once() -> None:
    global _ml_warning_shown
    if not _ml_warning_shown:
        warnings.warn(ML_MISSING, UserWarning, stacklevel=3)
        _ml_warning_shown = True


def default_recognizers() -> list[Recognizer]:
    recognizers: list[Recognizer] = [RegexRecognizer()]
    if ml_available():
        from .recognizers.gliner import GlinerRecognizer
        from .recognizers.sensitive import SensitiveRecognizer

        recognizers += [GlinerRecognizer(), SensitiveRecognizer()]
    return recognizers


class Detector:
    def __init__(
        self,
        recognizers: Sequence[Recognizer] | None = None,
        labels: Iterable[str] | None = None,
        anonymize: Iterable[str] | None = None,
    ) -> None:
        self._taxonomy = load_taxonomy()
        known = set(self._taxonomy.labels)
        self._labels = set(labels) if labels is not None else known
        forced = set(anonymize or ())
        unknown = (self._labels | forced) - known
        if unknown:
            raise ValueError(f"unknown labels: {sorted(unknown)}")
        self._to_anonymize = {
            label for label, info in self._taxonomy.labels.items() if info.default_action == "anonymize"
        } | forced
        self._tags = {label: self._taxonomy.tag(label) for label in known}
        self._warnings: tuple[str, ...] = ()
        if recognizers is None:
            recognizers = default_recognizers()
            if not ml_available():
                self._warnings = (ML_MISSING,)
                _warn_ml_missing_once()
        self._recognizers = list(recognizers)

    def analyze(self, text: str) -> Result:
        candidates = [e for r in self._recognizers for e in r.find(text) if e.label in self._labels]
        kept, discarded = resolve(candidates)
        anonymized = [e for e in kept if e.label in self._to_anonymize]
        flagged = [self._with_label_note(e) for e in kept if e.label not in self._to_anonymize]
        return Result(
            anonymized=redact(text, anonymized, self._tags),
            entities=tuple(anonymized),
            flagged=tuple(flagged),
            discarded=tuple(discarded),
            warnings=self._warnings,
        )

    def _with_label_note(self, e: Entity) -> Entity:
        note = self._taxonomy.labels[e.label].note
        return e if e.note or not note else dataclasses.replace(e, note=note)
