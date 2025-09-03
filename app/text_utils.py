"""Small text helpers and normalization utilities."""

from __future__ import annotations

import re
from typing import List

from .constants import BRAND_MAP


def split_list_like(text: str) -> List[str]:
    """Split a phrase like 'A, B and C' into clean tokens."""
    if not text:
        return []
    parts = re.split(r",|\band\b", text, flags=re.I)
    return [p.strip(" .;:/\\|\"'()[]{}") for p in parts if p.strip(" .;:/\\|\"'()[]{}")]


def norm_brand(name: str) -> str:
    """Normalize common India brand names to generic medicine names."""
    ql = name.strip().lower()
    return BRAND_MAP.get(ql, name.strip())
