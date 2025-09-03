"""Lightweight, explicit session memory for last symptom text."""

from __future__ import annotations

from typing import Optional


class SessionMemory:
    """Explicit store for last symptoms string."""

    def __init__(self) -> None:
        self._last_symptoms: Optional[str] = None

    def set_last_symptoms(self, text: str) -> None:
        self._last_symptoms = text

    def get_last_symptoms(self) -> Optional[str]:
        return self._last_symptoms

    def reset(self) -> None:
        self._last_symptoms = None
