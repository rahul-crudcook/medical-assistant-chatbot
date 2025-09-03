"""Dataclasses and types for intent classification results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Union


@dataclass
class IntentResult:
    """Container for multi-intent routing and context."""
    intents: List[str] = field(default_factory=list)
    context: Dict[str, Union[str, List[str], int]] = field(default_factory=dict)
    urgent: bool = False
