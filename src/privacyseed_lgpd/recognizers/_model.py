"""Loads the GLiNER2 model once per process, for local CPU inference only.

gliner2 also ships a client for a hosted inference service. This module never
uses it: that would send the user's text to a third party.
"""

from __future__ import annotations

from functools import lru_cache

MODEL_ID = "fastino/gliner2-privacy-filter-PII-multi"
MODEL_REVISION = "1cb4166094dc58fa8d836429f060d6c95f62b495"


@lru_cache(maxsize=1)
def load_model():
    from gliner2 import GLiNER2
    from huggingface_hub import snapshot_download

    path = snapshot_download(MODEL_ID, revision=MODEL_REVISION)
    return GLiNER2.from_pretrained(path, map_location="cpu")


def extract(model, text: str, labels: list[str], threshold: float) -> list[tuple[str, int, int, float]]:
    """Return (label, start, end, score) per span, trusting offsets only when they match the text."""
    raw = model.extract_entities_long(
        text, labels, threshold=threshold, include_confidence=True, include_spans=True
    )
    spans = []
    for label, items in (raw.get("entities") or {}).items():
        for item in items:
            if not isinstance(item, dict) or "start" not in item or "end" not in item:
                continue
            start, end = int(item["start"]), int(item["end"])
            if not 0 <= start < end <= len(text):
                continue
            if "text" in item and text[start:end] != item["text"]:
                continue
            spans.append((label, start, end, float(item.get("confidence", 0.0))))
    return spans
