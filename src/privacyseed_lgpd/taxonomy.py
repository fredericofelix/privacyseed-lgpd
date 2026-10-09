"""Loads taxonomy.yaml, the single source of labels."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import resources

import yaml

ACTIONS = ("anonymize", "flag")


@dataclass(frozen=True)
class LabelInfo:
    id: str
    name: str
    tag: str
    lgpd_category: str
    article: str
    description: str
    default_action: str
    note: str | None
    maps_to: dict[str, str | None]


@dataclass(frozen=True)
class Subcategory:
    id: str
    wording: str
    gliner_description: str


@dataclass(frozen=True)
class Taxonomy:
    labels: dict[str, LabelInfo]
    subcategories: dict[str, Subcategory]

    def tag(self, label: str) -> str:
        return f"[{self.labels[label].tag}]"


def parse_taxonomy(data: dict) -> Taxonomy:
    labels = {}
    for label_id, raw in data["labels"].items():
        action = raw["default_action"]
        if action not in ACTIONS:
            raise ValueError(f"{label_id}: default_action must be one of {ACTIONS}, got {action!r}")
        labels[label_id] = LabelInfo(
            id=label_id,
            name=raw["name"],
            tag=raw["tag"],
            lgpd_category=raw["lgpd_category"],
            article=raw["article"],
            description=raw["description"],
            default_action=action,
            note=raw.get("note"),
            maps_to=dict(raw.get("maps_to") or {}),
        )
    subcategories = {
        sub_id: Subcategory(id=sub_id, wording=raw["wording"], gliner_description=raw["gliner_description"])
        for sub_id, raw in (data.get("subcategories") or {}).items()
    }
    return Taxonomy(labels=labels, subcategories=subcategories)


@lru_cache(maxsize=1)
def load_taxonomy() -> Taxonomy:
    text = resources.files("privacyseed_lgpd").joinpath("taxonomy.yaml").read_text(encoding="utf-8")
    return parse_taxonomy(yaml.safe_load(text))
