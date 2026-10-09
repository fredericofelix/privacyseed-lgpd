"""The interface every recognizer implements."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..entity import Entity


@runtime_checkable
class Recognizer(Protocol):
    def find(self, text: str) -> list[Entity]: ...
