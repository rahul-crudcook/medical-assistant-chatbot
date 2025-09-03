"""All compiled regex patterns used by the classifier."""
#pylint: disable=C0301

from __future__ import annotations

import re

INTERACTION_RE = re.compile(r"(?:can i|should i)?\s*take\s+(.+?)\s+(?:together\s+with|with)\s+(.+)", re.I)
LAB_RE = re.compile(r"([\w\s-]+?)\s+(?:level|value)\s+(?:is|=)\s*([\w\.\-+/]+)", re.I)

SYMPTOMS_OF_RE = re.compile(
    r"(?:what\s+are\s+the\s+symptoms\s+of|symptoms\s+of|signs\s+of|how\s+does\s+.+\s+present)\s+(.+?)\??$",
    re.I,
)
USE_OF_RE = re.compile(r"(?:what\s+is\s+the?\s*use\s+of|use\s+of|what\s+is\s+.+\s+used\s+for)\s+(.+)", re.I)
SE_OF_RE = re.compile(r"(?:side\s*effects\s*of|what\s+are\s+the\s+side\s*effects\s+of)\s+(.+)", re.I)

DIFF_PATTERNS = [
    r"what (could|might) (this|it) be",
    r"what (could be the cause|is causing)",
    r"possible (causes|conditions|diseases)",
    r"which disease (do i have|might i have|i have)",
    r"what disease (do i have|i have|might i have)",
    r"do i have (.+)",
    r"is it (.+)\?",
]

TESTS_PATTERNS_EXTRA = [
    r"\bwhat test should i get\b",
    r"\bwhich test should i get\b",
    r"\bwhat tests should i get\b",
    r"\bwhich tests should i get\b",
    r"\bwhat test should i get done\b",
    r"\bwhich test should i get done\b",
    r"\bwhat tests should i get done\b",
    r"\bwhich tests should i get done\b",
    r"\bwhat investigation(s)? should i\b",
    r"\bwork[\s-]?up\b",
]

KEYWORDS = {
    "interaction": [
        "together with", "can i take", "should i take", "mix with", "combine with", "interaction",
    ],
    "lab_test": ["level is", "value is", "value =", "level =", "reference range", "lab report"],
    "terminology": ["what is", "define", "explain", "meaning of", "layman terms"],
    "symptom": [
        "i have", "i feel", "pain in", "fever", "chills", "vomit", "nausea", "cough", "sore throat",
        "diarrhea", "breathless", "shortness of breath", "chest pain", "headache", "rash",
        "fatigue", "body ache", "cold", "flu", "burning urination", "back pain", "stomach ache",
        "loose motions", "earache", "dizziness", "lightheaded", "runny nose",
    ],
    "tests": [
        "what tests should i", "which tests", "what blood test", "suggest tests",
        "investigations", "which scan",
    ],
    "medicine": [
        "side effects", "dosage", "use of", "used for", "tablet", "capsule", "syrup",
        "is x safe", "how to take", "when to take", "before or after food",
    ],
}

DURATION_RE = re.compile(
    r"(?:since\s+)(?:(\d+)\s*-\s*(\d+)|(\d+))(?:\s*days?)|since\s+(yesterday|last night|tonight|today)",
    re.I,
)
