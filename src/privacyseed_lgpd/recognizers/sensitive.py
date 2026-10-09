"""Sensitive data recognizer (LGPD art. 5, II). Experimental.

Two sources: a curated lexicon (exact terms, accent- and case-insensitive) and
GLiNER zero-shot with a Portuguese description per subcategory.
"""

from __future__ import annotations

import re
import unicodedata
from importlib import resources

from ..entity import Entity
from ..taxonomy import load_taxonomy
from ._model import extract, load_model

DEFAULT_THRESHOLD = 0.6

# Each base letter matches its accented forms, so offsets stay on the original text.
_ACCENTS = {"a": "aáàâã", "e": "eéê", "i": "ií", "o": "oóôõ", "u": "uúü", "c": "cç"}


def _strip_accents(term: str) -> str:
    decomposed = unicodedata.normalize("NFD", term.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _term_pattern(term: str) -> str:
    out = []
    for ch in _strip_accents(term):
        if ch in _ACCENTS:
            out.append(f"[{_ACCENTS[ch]}]")
        elif ch.isspace():
            out.append(r"\s+")
        else:
            out.append(re.escape(ch))
    return "".join(out)


def load_lexicon() -> dict[str, list[str]]:
    root = resources.files("privacyseed_lgpd").joinpath("lexicon")
    lexicon = {}
    for sub_id in load_taxonomy().subcategories:
        lines = root.joinpath(f"{sub_id}.txt").read_text(encoding="utf-8").splitlines()
        lexicon[sub_id] = [t.strip() for t in lines if t.strip() and not t.lstrip().startswith("#")]
    return lexicon


def compile_lexicon(lexicon: dict[str, list[str]]) -> dict[str, re.Pattern[str]]:
    patterns = {}
    for sub_id, terms in lexicon.items():
        if not terms:
            continue
        alternatives = sorted({_term_pattern(t) for t in terms}, key=len, reverse=True)
        patterns[sub_id] = re.compile(r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)", re.IGNORECASE)
    return patterns


class SensitiveRecognizer:
    def __init__(self, model=None, threshold: float = DEFAULT_THRESHOLD,
                 lexicon: dict[str, list[str]] | None = None) -> None:
        self._model = model
        self._threshold = threshold
        self._taxonomy = load_taxonomy()
        self._patterns = compile_lexicon(load_lexicon() if lexicon is None else lexicon)
        self._by_description = {s.gliner_description: s.id for s in self._taxonomy.subcategories.values()}

    def find(self, text: str) -> list[Entity]:
        found = [
            self._entity(text, m.start(), m.end(), sub_id, 1.0, "lexicon")
            for sub_id, pattern in self._patterns.items()
            for m in pattern.finditer(text)
        ]
        if not text.strip():
            return found
        if self._model is None:
            self._model = load_model()
        for label, start, end, score in extract(self._model, text, list(self._by_description), self._threshold):
            sub_id = self._by_description.get(label)
            if sub_id:
                found.append(self._entity(text, start, end, sub_id, score, "gliner"))
        return found

    def _entity(self, text: str, start: int, end: int, sub_id: str, score: float, source: str) -> Entity:
        return Entity(
            label="sensitive_data",
            text=text[start:end],
            start=start,
            end=end,
            score=score,
            source=source,
            lgpd_category="art5_II",
            sensitive_subcategory=sub_id,
            experimental=True,
        )
