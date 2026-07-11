from typing import Any

from ...config import Settings
from .base import AIProvider, LocalEvidenceProvider


class OpenAIProvider(AIProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model_name = settings.openai_model if settings.openai_api_key else LocalEvidenceProvider.model_name
        self.fallback = LocalEvidenceProvider()

    def generate(self, prompt: str, evidence: dict[str, Any]) -> str:
        if not self.settings.openai_api_key:
            return self.fallback.generate(prompt, evidence)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.settings.openai_api_key)
            completion = client.chat.completions.create(
                model=self.settings.openai_model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Garmin training and recovery analyst. "
                            "Answer in Traditional Chinese. Use only the supplied evidence. "
                            "If evidence is insufficient, say so clearly. Do not make medical diagnoses."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            return completion.choices[0].message.content or self.fallback.generate(prompt, evidence)
        except Exception:
            return self.fallback.generate(prompt, evidence)
