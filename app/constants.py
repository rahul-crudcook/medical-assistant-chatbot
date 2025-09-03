"""Constants for persona, OTC anchors, brand normalization, and style prefs."""

from __future__ import annotations

ASSISTANT_PERSONA = (
    "You are a cautious, reliable Medical Assistant (not a doctor).\n"
    "Be concise, precise, and clear for a layperson without dumbing down.\n"
    "Never provide a definitive diagnosis; give likely considerations and next steps.\n"
    "Avoid inventing drug names; if unsure, say you’re unsure.\n"
    "Prefer Indian-common OTC names when appropriate (e.g., paracetamol / acetaminophen)."
)

BRAND_MAP = {
    "dolo-650": "paracetamol 650 mg",
    "dolo 650": "paracetamol 650 mg",
    "calpol": "paracetamol",
    "crocin": "paracetamol",
}

OTC_DOSING_ANCHORS = (
    "Common OTC anchors (for reference; do not show if not relevant):\n"
    "- Paracetamol (acetaminophen): typical adult 500–650 mg every 6–8 h as needed; "
    "**max 3,000 mg/day** total from all sources.\n"
    "- Ibuprofen: typical adult 200–400 mg every 6–8 h as needed; **max 1,200 mg/day OTC**.\n"
    "- Naproxen (OTC): 220 mg every 8–12 h; **max 660 mg/day OTC**.\n"
)

STYLE_PREFS = {
    "max_sections": 4,
    "max_bullets_per_section": 4,
    "max_chars": 1600,
}
