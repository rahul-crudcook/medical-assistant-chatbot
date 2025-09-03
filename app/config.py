"""Application configuration and feature flags."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Immutable configuration holder for the app and model behavior."""

    # Model name for the Inference API
    model_name: str = "BioMistral/BioMistral-7B-DARE"

    # Generation parameters sent to the API
    max_new_tokens: int = 540
    temperature: float = 0.4
    top_p: float = 0.9
    repetition_penalty: float = 1.05

    # Feature flags (these affect the prompt, so they stay)
    use_heuristic_test_injection: bool = False
    include_duration_hints: bool = False
    include_otc_anchors: bool = False
