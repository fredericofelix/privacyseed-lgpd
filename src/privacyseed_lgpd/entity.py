"""Data model shared by recognizers, the resolver and the detector."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Literal

# "passed"/"failed": the label has a check digit and it was verified.
# "none": the label has no check digit (e-mail, phone, names...).
Check = Literal["passed", "failed", "none"]


@dataclass(frozen=True)
class Entity:
    label: str
    text: str
    start: int
    end: int
    score: float
    source: str
    lgpd_category: str
    sensitive_subcategory: str | None = None
    experimental: bool = False
    check: Check = "none"
    note: str | None = None


@dataclass(frozen=True)
class Result:
    anonymized: str
    entities: tuple[Entity, ...] = ()
    flagged: tuple[Entity, ...] = ()
    discarded: tuple[Entity, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, indent: int | None = None) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)
