"""Detect and anonymize personal data (LGPD) in Brazilian Portuguese text."""

from .detector import Detector
from .entity import Entity, Result

__version__ = "0.1.0"

__all__ = ["Detector", "Entity", "Result", "__version__"]
