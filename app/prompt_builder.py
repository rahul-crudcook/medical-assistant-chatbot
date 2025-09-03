"""Prompt builder for multi-intent, model-led completions."""

from __future__ import annotations

from typing import List

from .config import AppConfig
from .constants import ASSISTANT_PERSONA, OTC_DOSING_ANCHORS
from .intents import IntentResult

#pylint: disable=C0301

class PromptBuilder:
    """Builds a single consolidated prompt string for the LLM."""

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg

    @staticmethod
    def _section_templates() -> dict:
        return {
            "symptom": {
                "allowed": (
                    "- What to do now (short, actionable)\n"
                    "- OTC Recommendation & Dose (only common OTCs)\n"
                    "- Self-care advice\n"
                    "- Likely considerations (not a diagnosis)\n"
                    "- Red Flags (seek urgent care if...)\n"
                    "- Next Steps / When to see a doctor\n"
                ),
                "forbidden": "Avoid prescription drug names and antibiotics.",
                "ordering": "Start with 'What to do now' (include OTC + starting dose + max daily limit if relevant).",
            },
            "tests": {
                "allowed": (
                    "- Top Tests (3–5) with 1-line reason each (named tests)\n"
                    "- When to skip vs. defer\n"
                    "- Red Flags (seek urgent care if...)\n"
                    "- Next Steps / How to discuss with your clinician\n"
                ),
                "forbidden": "Do NOT give medication dosing.",
                "ordering": "Prefer named tests (e.g., CBC, Malaria RDT/smear, Dengue NS1/IgM per timing, Urine routine & culture, Chest X-ray/CRP/ESR).",
            },
            "differential": {
                "allowed": (
                    "- Likely considerations (common first)\n"
                    "- What supports/argues against each (1 line)\n"
                    "- Red Flags\n"
                    "- What to monitor at home\n"
                ),
                "forbidden": "No definitive diagnoses or prescribing.",
                "ordering": "List 3–5 possibilities with 1-line rationale each.",
            },
            "medicine_info": {
                "allowed": (
                    "- For EACH medicine: What it is & Uses (primary indications)\n"
                    "- Key Precautions (contraindications, interactions, special populations)\n"
                    "- Common Side Effects (3–6 bullets)\n"
                    "- Typical OTC Dose (adults) [ONLY if that medicine is OTC]\n"
                    "- When to seek medical advice / follow-up\n"
                ),
                "forbidden": "If prescription-only, do NOT give numeric dosing; describe clinician-based dosing.",
                "ordering": "Organize by medicine name: Uses → Precautions → Side effects → (OTC dose if OTC).",
            },
            "condition_info": {
                "allowed": (
                    "- Symptoms (common + hallmark)\n"
                    "- Who is at risk / typical triggers\n"
                    "- Red Flags (seek urgent care if...)\n"
                    "- Basic Tests / First steps (if helpful)\n"
                ),
                "forbidden": "Do not prescribe. No definitive diagnoses.",
                "ordering": "Start with 'Symptoms' (short, prioritized list).",
            },
            "interaction": {
                "allowed": (
                    "- Interaction Risk Level (None/Mild/Moderate/Severe)\n"
                    "- Clinical Explanation (short)\n"
                    "- Recommendation (what to do)\n"
                ),
                "forbidden": "No dosing.",
                "ordering": "Start with 'Interaction risk level: X'.",
            },
            "lab_test": {
                "allowed": (
                    "- What the test measures\n"
                    "- Typical reference ranges (general guidance)\n"
                    "- What high/low can mean\n"
                    "- Next Steps (recheck/follow-ups)\n"
                    "- Red Flags\n"
                ),
                "forbidden": "No medication dosing.",
                "ordering": "Start with a plain-English 'what this means'.",
            },
            "terminology": {
                "allowed": (
                    "- What it means (Definition)\n"
                    "- Why it matters / Common contexts\n"
                    "- Red Flags\n"
                    "- Next Steps (what to ask your doctor)\n"
                ),
                "forbidden": "No treatment/dosing specifics.",
                "ordering": "Start with a 1–2 line definition.",
            },
        }

    def build(self, ir: IntentResult) -> str:
        """Return full instruction prompt for the model."""
        lines: List[str] = []

        if "symptom" in ir.intents:
            sym = ir.context.get("symptoms", "Not restated")
            dur = ir.context.get("duration_days")
            if isinstance(dur, int):
                lines.append(f"- Symptoms described: {sym} (duration ~{dur} day(s)).")
            else:
                lines.append(f"- Symptoms described: {sym}.")
        if "differential" in ir.intents:
            lines.append("- They want likely causes (not a definitive diagnosis).")
        if "tests" in ir.intents:
            lines.append("- They are asking which tests would clarify the cause.")
        if "medicine_info" in ir.intents:
            meds = ir.context.get("medicines", [])
            if isinstance(meds, list) and meds:
                lines.append(
                    "- Medicine info requested for: "
                    f"{', '.join(meds)} (Uses, Precautions, Side effects; OTC dose only if OTC)."
                )
        if "condition_info" in ir.intents:
            conds = ir.context.get("conditions", [])
            if isinstance(conds, list) and conds:
                lines.append(
                    f"- Condition info requested for: {', '.join(conds)} "
                    "(Symptoms, Red flags, Basic tests if helpful)."
                )
        if "interaction" in ir.intents:
            lines.append(f"- Interaction question: {ir.context.get('drug1','?')} with {ir.context.get('drug2','?')}.")
        if "lab_test" in ir.intents:
            lines.append(f"- Lab question: {ir.context.get('test_name','?')} = {ir.context.get('value','?')}.")
        if "terminology" in ir.intents and "condition_info" not in ir.intents and "medicine_info" not in ir.intents:
            lines.append(f"- Explain term: {ir.context.get('term','?')}.")

        task_block = "The user’s request (multi-part):\n" + "\n".join(lines) if lines else \
            "The user asked a general health question."

        allowed_parts, forbidden_parts, ordering_rules = [], [], []
        templ = self._section_templates()
        for intent in ir.intents:
            t = templ[intent]
            allowed_parts.append(t["allowed"])
            forbidden_parts.append(t["forbidden"])
            ordering_rules.append(t["ordering"])

        urgent_line = ""
        if ir.urgent:
            urgent_line = (
                "If severe/urgent red flags appear (e.g., severe chest pain, trouble breathing, fainting, "
                "confusion, seizures, one-sided weakness, very high fever, pregnancy with bleeding), "
                'start with: **"Seek emergency care now."**\n'
            )

        dosing_guardrails = (
            "Dosing rules:\n"
            "- Provide **typical adult starting dose** only for common OTCs (paracetamol, ibuprofen, naproxen) "
            "with **max daily limits**.\n"
            "- For prescription medicines: describe clinician-determined dosing; avoid numeric schedules.\n"
            "- Always add: 'Actual dosing must be decided by your clinician.'\n"
        )

        needs_action_block = any(i in ir.intents for i in ["symptom", "tests", "differential"])
        if needs_action_block:
            formatting = (
                "Formatting rules:\n"
                "1) Begin with **What to do now** (1–3 lines, direct). If symptoms are involved, include OTC rec + "
                "dosing first line if appropriate.\n"
                "2) Then include only the 1–3 most relevant sections from the allowed list below (≤4 bullets or ~3 "
                "lines per section).\n"
                "3) Use clear markdown headings for included sections only.\n"
                "4) Keep it compact and readable; avoid long paragraphs.\n"
                "5) End with this exact bold line: "
                "\"This information is for educational purposes only and does not constitute medical advice. "
                "Consult a qualified healthcare professional for diagnosis and treatment.\""
            )
        else:
            formatting = (
                "Formatting rules:\n"
                "1) Skip any generic 'what to do now' block unless it adds real value.\n"
                "2) Provide 1–3 most relevant sections from the allowed list below (≤4 bullets or ~3 lines per section).\n"
                "3) Use clear markdown headings for included sections only.\n"
                "4) Keep it compact and readable; avoid long paragraphs.\n"
                "5) End with this exact bold line: "
                "\"This information is for educational purposes only and does not constitute medical advice. "
                "Consult a qualified healthcare professional for diagnosis and treatment.\""
            )

        anchors = OTC_DOSING_ANCHORS if (self._cfg.include_otc_anchors and any(i in ir.intents for i in ["symptom", "medicine_info"])) else ""

        return (
            "<s>[INST]\n"
            f"{ASSISTANT_PERSONA}\n\n"
            f"{task_block}\n\n"
            "Choose ONLY from these sections (pick 2–3 that add real value):\n"
            f"{chr(10).join(allowed_parts)}\n\n"
            "Forbidden for this response:\n"
            f"{' • '.join(forbidden_parts)}\n\n"
            "Ordering preferences:\n"
            f"{' | '.join(ordering_rules)}\n\n"
            f"{urgent_line}"
            f"{dosing_guardrails}\n"
            f"{formatting}\n"
            f"{anchors}\n"
            "[/INST]"
        )
