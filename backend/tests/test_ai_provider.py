from app.config import Settings
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.provider import create_ai_provider


def test_default_provider_uses_local_fallback_without_gemini_key():
    settings = Settings(ai_provider="gemini", gemini_api_key=None)
    provider = create_ai_provider(settings)

    assert provider.model_name == "local-rule-based"
    assert "Garmin" in provider.generate("question", {"has_data": False})


def test_gemini_provider_sends_generate_content_payload(monkeypatch):
    calls = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": "gemini answer"}]}}]}

    class FakeClient:
        def __init__(self, timeout):
            calls["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, params, json):
            calls["url"] = url
            calls["params"] = params
            calls["json"] = json
            return FakeResponse()

    import app.services.ai.gemini_provider as gemini_provider

    monkeypatch.setattr(gemini_provider.httpx, "Client", FakeClient)
    settings = Settings(
        ai_provider="gemini",
        gemini_api_key="gemini-key",
        gemini_model="gemini-test",
    )

    answer = GeminiProvider(settings).generate("Analyze this evidence", {"has_data": True})

    assert answer == "gemini answer"
    assert calls["url"].endswith("/models/gemini-test:generateContent")
    assert calls["params"] == {"key": "gemini-key"}
    assert calls["json"]["contents"][0]["parts"][0]["text"] == "Analyze this evidence"
    assert "Traditional Chinese" in calls["json"]["system_instruction"]["parts"][0]["text"]
