"""GLiNER recognizer: person names, addresses and dates of birth."""

from __future__ import annotations

from ..entity import Entity
from ..taxonomy import load_taxonomy
from ._model import extract, load_model

# Model label -> our label.
GLINER_LABELS = {"person": "person_name", "address": "address", "date_of_birth": "birth_date"}

# The model over-predicts "person" for organisations and products (model card),
# so its threshold is higher. Values tuned on golden set v0.
DEFAULT_THRESHOLDS = {"person": 0.6, "address": 0.4, "date_of_birth": 0.5}


class GlinerRecognizer:
    def __init__(self, model=None, thresholds: dict[str, float] | None = None) -> None:
        self._model = model
        self._thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._taxonomy = load_taxonomy()

    def find(self, text: str) -> list[Entity]:
        if not text.strip():
            return []
        if self._model is None:
            self._model = load_model()
        found = []
        spans = extract(self._model, text, list(GLINER_LABELS), min(self._thresholds.values()))
        for label, start, end, score in spans:
            if label not in GLINER_LABELS or score < self._thresholds[label]:
                continue
            ours = GLINER_LABELS[label]
            found.append(
                Entity(
                    label=ours,
                    text=text[start:end],
                    start=start,
                    end=end,
                    score=score,
                    source="gliner",
                    lgpd_category=self._taxonomy.labels[ours].lgpd_category,
                )
            )
        return found
