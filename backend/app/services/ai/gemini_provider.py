from typing import Any
from urllib.parse import quote

import httpx

from ...config import Settings
from .base import AIProvider, LocalEvidenceProvider


SYSTEM_INSTRUCTION = (
    "You are a Garmin training and recovery analyst. "
    "Answer in Traditional Chinese. Use only the supplied evidence. "
    "If evidence is insufficient, say so clearly. Do not make medical diagnoses."
)


class GeminiProvider(AIProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_name = settings.gemini_model if settings.gemini_api_key else LocalEvidenceProvider.model_name
        self.fallback = LocalEvidenceProvider()

    def generate(self, prompt: str, evidence: dict[str, Any]) -> str:
        if not self.settings.gemini_api_key:
            return self.fallback.generate(prompt, evidence)

        try:
            model = quote(self.settings.gemini_model, safe="")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            payload = {
                "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200},
            }
            with httpx.Client(timeout=45) as client:
                response = client.post(url, params={"key": self.settings.gemini_api_key}, json=payload)
                response.raise_for_status()
            return self._extract_text(response.json()) or self.fallback.generate(prompt, evidence)
        except Exception:
            return self.fallback.generate(prompt, evidence)

    def _extract_text(self, data: dict[str, Any]) -> str | None:
        for candidate in data.get("candidates") or []:
            parts = ((candidate.get("content") or {}).get("parts")) or []
            text = "\n".join(part.get("text", "") for part in parts if part.get("text"))
            if text.strip():
                return text.strip()
        return None
