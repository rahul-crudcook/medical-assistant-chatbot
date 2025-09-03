"""Streamlit UI for the Medical Assistant Chatbot (Model-led)."""

from __future__ import annotations

import streamlit as st

from app.config import AppConfig
from app.constants import STYLE_PREFS
from app.generator import ModelGenerator
from app.memory import SessionMemory
from app.classifier import IntentClassifier
from app.prompt_builder import PromptBuilder
from app.postprocessor import MarkdownPostprocessor


def _init_state() -> None:
    if "mem" not in st.session_state:
        st.session_state.mem = SessionMemory()
    if "cfg" not in st.session_state:
        st.session_state.cfg = AppConfig()
    if "gen" not in st.session_state:
        st.session_state.gen = ModelGenerator(st.session_state.cfg)
    if "classifier" not in st.session_state:
        st.session_state.classifier = IntentClassifier(st.session_state.mem)
    if "prompt_builder" not in st.session_state:
        st.session_state.prompt_builder = PromptBuilder(st.session_state.cfg)
    if "post" not in st.session_state:
        st.session_state.post = MarkdownPostprocessor(STYLE_PREFS)


def main() -> None:
    """Streamlit entrypoint."""
    st.set_page_config(page_title="Medical Assistant (Model-led)", page_icon="🩺", layout="centered")
    _init_state()

    st.title("🩺 Medical Assistant (Model-led)")
    st.caption(
        "Ask about symptoms, tests, interactions, medicine uses/precautions/side-effects, "
        "lab meanings, or condition info (e.g., 'symptoms of dengue')."
    )

    with st.expander("Settings (read-only defaults)", expanded=False):
        cfg: AppConfig = st.session_state.cfg
        st.text(f"Model: {cfg.model_name}")
        st.text(
        f"Max new tokens: {cfg.max_new_tokens}, Temperature: {cfg.temperature}, Top-p: {cfg.top_p}")
        st.text(f"Feature flags → heuristics: {cfg.use_heuristic_test_injection}, "
                f"duration hints: {cfg.include_duration_hints}, "
                f"OTC anchors: {cfg.include_otc_anchors}")

    user_q = st.text_input("Your question",
                           placeholder="e.g., I have fever and body ache since 3 days…")
    go = st.button("Get answer", use_container_width=True)

    if go and user_q.strip():
        classifier: IntentClassifier = st.session_state.classifier
        ir = classifier.classify(user_q)

        # Attach remembered symptoms for tests/differential if missing
        if any(i in ir.intents for i in ["tests", "differential"]) and "symptoms" not in ir.context:
            remembered = st.session_state.mem.get_last_symptoms()
            if remembered:
                ir.context["symptoms"] = remembered

        # Persist latest symptoms
        if "symptom" in ir.intents and ir.context.get("symptoms"):
            st.session_state.mem.set_last_symptoms(str(ir.context["symptoms"]))

        builder: PromptBuilder = st.session_state.prompt_builder
        prompt = builder.build(ir)

        gen: ModelGenerator = st.session_state.gen
        with st.spinner("Thinking…"):
            raw = gen.generate(prompt)

        post = st.session_state.post
        md = post.process(raw)
        st.markdown(md)


if __name__ == "__main__":
    main()
