# app/generator.py
"""LLM generator using the Hugging Face Inference API."""

from __future__ import annotations
import os
import requests
from .config import AppConfig


class ModelGenerator:
    """Uses the Hugging Face Inference API to generate text."""

    def __init__(self, cfg: AppConfig) -> None:
        self._cfg = cfg
        # Securely get the API token from environment secrets (like HF Space secrets)
        self._api_token = os.environ.get("HF_TOKEN")
        if not self._api_token:
            raise ValueError("HF_TOKEN secret not found. Please add it to your Space's Settings tab.")

        self._api_url = f"https://api-inference.huggingface.co/models/{self._cfg.model_name}"
        self._headers = {"Authorization": f"Bearer {self._api_token}"}

    def generate(self, prompt: str) -> str:
        """Sends a prompt to the HF Inference API and returns the model's response."""

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": self._cfg.max_new_tokens,
                "temperature": self._cfg.temperature,
                "top_p": self._cfg.top_p,
                "repetition_penalty": self._cfg.repetition_penalty,
                "do_sample": True,
            },
        }

        response = requests.post(self._api_url, headers=self._headers, json=payload)

        if response.status_code == 200:
            full_response = response.json()[0]['generated_text']
            # The API often returns the full prompt in its response, so we strip it out.
            if "[/INST]" in full_response:
                return full_response.split("[/INST]")[-1].strip()
            # Fallback if the prompt structure changes
            if full_response.strip().startswith(prompt.strip()):
                return full_response[len(prompt) :].strip()
            return full_response.strip()

        elif "currently loading" in response.text:
            return "The model is currently warming up. Please wait a moment and try your query again."

        else:
            return f"Error: API call failed with status {response.status_code}. Response: {response.text}"
