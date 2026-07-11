import sys
from types import SimpleNamespace

from app.config import Settings
from app.services.garmin.unofficial import UnofficialGarminConnector


def test_connector_uses_persisted_token_blob_and_saves_refreshed_blob(monkeypatch, tmp_path):
    loaded_blob = "old-" + ("x" * 600)
    refreshed_blob = "new-" + ("y" * 600)
    login_tokenstores = []
    saved_blobs = []

    class FakeInnerClient:
        def dumps(self):
            return refreshed_blob

    class FakeGarmin:
        def __init__(self, email, password, prompt_mfa=None):
            self.client = FakeInnerClient()

        def login(self, tokenstore=None):
            login_tokenstores.append(tokenstore)

        def get_activities_by_date(self, start, end):
            return []

    monkeypatch.setitem(sys.modules, "garminconnect", SimpleNamespace(Garmin=FakeGarmin))
    settings = Settings(
        demo_mode=False,
        garmin_email="athlete@example.com",
        garmin_password="secret",
        garmin_tokenstore=str(tmp_path / "tokens"),
    )

    connector = UnofficialGarminConnector(
        settings,
        token_reader=lambda: loaded_blob,
        token_writer=saved_blobs.append,
    )

    payload = connector.fetch(days=1)

    assert payload["source"] == "garminconnect"
    assert login_tokenstores == [loaded_blob]
    assert saved_blobs
    assert saved_blobs[-1] == refreshed_blob


def test_connector_mfa_prompt_prefers_request_code():
    settings = Settings(demo_mode=False, garmin_mfa_code="__unset__")
    connector = UnofficialGarminConnector(settings, mfa_code="123456")

    assert connector._prompt_mfa() == "123456"
