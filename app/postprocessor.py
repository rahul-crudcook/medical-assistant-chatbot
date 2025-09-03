"""Output formatting utilities for markdown compactness & limits."""

from __future__ import annotations

import re
from typing import Dict, List


class MarkdownPostprocessor:
    """Tidy markdown: trim sections/bullets/length without changing content."""

    def __init__(self, style_prefs: Dict[str, int]) -> None:
        self._prefs = style_prefs

    def _trim_bullets(self, block: str) -> str:
        bullets = block.strip().split("\n")
        trimmed: List[str] = []
        seen = 0
        for line in bullets:
            if line.lstrip().startswith(("-", "*")):
                seen += 1
            if seen <= self._prefs["max_bullets_per_section"]:
                trimmed.append(line)
        return "\n".join(trimmed)

    def process(self, md: str) -> str:
        """Apply formatting constraints (sections, bullets, char cap)."""
        md = re.sub(r"\n{3,}", "\n\n", md).strip()

        # Limit total H2 sections
        heads = re.findall(r"^#{2,}\s.*", md, flags=re.MULTILINE)
        if heads:
            allowed = self._prefs["max_sections"]
            lines, kept, count = md.splitlines(), [], 0
            for ln in lines:
                if re.match(r"^#{2,}\s", ln):
                    count += 1
                if count <= allowed:
                    kept.append(ln)
            md = "\n".join(kept).strip()

        # Trim bullets per section
        parts = re.split(r"(\n## .*\n)", md)
        for i in range(2, len(parts), 2):
            parts[i] = self._trim_bullets(parts[i])
        md = "".join(parts)

        # Character cap
        if len(md) > self._prefs["max_chars"]:
            md = md[: self._prefs["max_chars"]].rsplit("\n", 1)[0].rstrip()
            md += "\n\n…"
        return md
