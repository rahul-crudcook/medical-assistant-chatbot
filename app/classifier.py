"""Multi-intent classifier (regex/keyword routing only; no content injection)."""

from __future__ import annotations

import re
from typing import List, Optional

from .intents import IntentResult
from .regexes import (
    INTERACTION_RE,
    LAB_RE,
    SYMPTOMS_OF_RE,
    USE_OF_RE,
    SE_OF_RE,
    DIFF_PATTERNS,
    TESTS_PATTERNS_EXTRA,
    KEYWORDS,
    DURATION_RE,
)
from .safety import URGENT_RED_FLAGS
from .text_utils import norm_brand, split_list_like
from .memory import SessionMemory

#pylint: disable=C0301

class IntentClassifier:
    """Parses a user query into a multi-intent result with context fields."""

    def __init__(self, memory: SessionMemory) -> None:
        self._mem = memory

    @staticmethod
    def _extract_duration_days(text: str) -> Optional[int]:
        q = text.lower()
        m = DURATION_RE.search(q)
        if not m:
            return None
        if m.group(1) and m.group(2):  # range like 4-5
            try:
                lo = int(m.group(1))
                hi = int(m.group(2))
                return (lo + hi) // 2
            except ValueError:
                return None
        if m.group(3):
            try:
                return int(m.group(3))
            except ValueError:
                return None
        word = m.group(4)
        if word:
            if "yesterday" in word or "last night" in word or "tonight" in word:
                return 1
            if "today" in word:
                return 0
        return None

    def classify(self, query: str) -> IntentResult:
        q = query.strip()
        ql = q.lower()
        out = IntentResult()

        # Urgency
        out.urgent = any(flag in ql for flag in URGENT_RED_FLAGS)

        # Interaction
        m_int = INTERACTION_RE.search(ql)
        if m_int:
            out.intents.append("interaction")
            out.context["drug1"] = m_int.group(1).strip()
            out.context["drug2"] = m_int.group(2).strip()

        # Lab value
        m_lab = LAB_RE.search(ql)
        if m_lab:
            out.intents.append("lab_test")
            out.context["test_name"] = m_lab.group(1).strip()
            out.context["value"] = m_lab.group(2).strip()

        # Condition info: “symptoms of …”
        m_symof = SYMPTOMS_OF_RE.search(q)
        if m_symof:
            conds = split_list_like(m_symof.group(1))
            if conds:
                out.intents.append("condition_info")
                out.context["conditions"] = [c.strip("? .") for c in conds]

        # Medicine info
        med_targets: List[str] = []
        for pat in (USE_OF_RE, SE_OF_RE):
            m = pat.search(q)
            if m:
                med_targets.extend(split_list_like(m.group(1)))
        if any(k in ql for k in KEYWORDS["medicine"]) and not med_targets:
            tail = re.split(r"\bof\b", q, flags=re.I)
            if len(tail) > 1:
                med_targets.extend(split_list_like(tail[-1]))
            else:
                med_targets.append(q.strip())
        if med_targets:
            meds = [norm_brand(m) for m in med_targets]
            out.intents.append("medicine_info")
            out.context["medicines"] = meds

        # Differential
        if any(re.search(p, ql) for p in DIFF_PATTERNS):
            out.intents.append("differential")

        # Symptoms
        if any(w in ql for w in KEYWORDS["symptom"]):
            out.intents.append("symptom")
            out.context["symptoms"] = q
            self._mem.set_last_symptoms(q)
            dur = self._extract_duration_days(q)
            if dur is not None:
                out.context["duration_days"] = dur

        # Tests
        if any(w in ql for w in KEYWORDS["tests"]) or any(re.search(p, ql) for p in TESTS_PATTERNS_EXTRA):
            out.intents.append("tests")
            if "symptoms" not in out.context:
                remembered = self._mem.get_last_symptoms()
                if remembered:
                    out.context["symptoms"] = remembered
                    dur = self._extract_duration_days(remembered)
                    if dur is not None:
                        out.context["duration_days"] = dur

        # Terminology (only if not medicine/condition captured)
        if any(w in ql for w in KEYWORDS["terminology"]):
            if "medicine_info" not in out.intents and "condition_info" not in out.intents:
                out.intents.append("terminology")
                term = re.sub(r"^(what is|define|explain|meaning of)\s+(an?\s+|the\s+)?", "", ql).strip("? ")
                out.context["term"] = term

        # Default
        if not out.intents:
            out.intents = ["symptom", "differential"]
            out.context["symptoms"] = q
            self._mem.set_last_symptoms(q)
            dur = self._extract_duration_days(q)
            if dur is not None:
                out.context["duration_days"] = dur

        priority = [
            "interaction",
            "lab_test",
            "condition_info",
            "medicine_info",
            "terminology",
            "symptom",
            "differential",
            "tests",
        ]
        out.intents = sorted(set(out.intents), key=lambda i: priority.index(i) if i in priority else 999)
        return out
