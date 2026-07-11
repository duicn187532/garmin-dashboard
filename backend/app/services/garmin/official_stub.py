from ...config import Settings
from .base import GarminConnector, GarminConnectorError, GarminPayload


class OfficialGarminConnector(GarminConnector):
    """Placeholder for Garmin Connect Developer Program API integration."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def fetch(self, days: int = 30) -> GarminPayload:
        raise GarminConnectorError(
            "Official Garmin API connector is not configured yet. Use the unofficial connector or demo mode."
        )

