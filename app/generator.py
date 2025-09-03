# app/generator.py
"""LLM loader and generator (Transformers on MPS/CPU for macOS)."""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from .config import AppConfig


class ModelGenerator:
    """Load the model once and provide a typed generate() API using Transformers."""

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        self._device = self._detect_device()
        self._model, self._tokenizer = self._load_model()

    def _detect_device(self) -> str:
        # Prefer Apple GPU (MPS) if available, else CPU
        if torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_model(self):
        # For 7B models on Mac, use float16 on MPS if possible, otherwise bfloat16/float32.
        dtype = torch.float16 if self._device == "mps" else torch.float32

        tokenizer = AutoTokenizer.from_pretrained(
            self._cfg.model_name,
            use_fast=True,
            trust_remote_code=False,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self._cfg.model_name,
            torch_dtype=dtype,
            low_cpu_mem_usage=True,
            device_map=None,  # we move it manually
            trust_remote_code=False,
        )
        model = model.to(self._device)
        model.eval()
        return model, tokenizer

    def generate(self, prompt: str) -> str:
        """Return the raw model completion text (post [/INST])."""
        inputs = self._tokenizer(prompt, return_tensors="pt", padding=True)
        # MPS needs .to("mps"); CPU will ignore safely.
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=self._cfg.max_new_tokens,
                do_sample=True,
                temperature=self._cfg.temperature,
                top_p=self._cfg.top_p,
                repetition_penalty=self._cfg.repetition_penalty,
                eos_token_id=self._tokenizer.eos_token_id,
                pad_token_id=self._tokenizer.pad_token_id,
            )

        full = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        return full.split("[/INST]")[-1].strip()
