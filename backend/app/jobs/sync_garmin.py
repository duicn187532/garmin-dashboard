from ..config import get_settings
from ..database import init_db
from ..services.garmin.unofficial import UnofficialGarminConnector
from ..store import MongoDataStore, store_context


def main() -> None:
    settings = get_settings()
    if settings.database_backend == "mongodb":
        MongoDataStore(settings).ensure_indexes()
    else:
        init_db()
    with store_context() as store:
        response = store.sync(UnofficialGarminConnector(settings), days=30)
        print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
