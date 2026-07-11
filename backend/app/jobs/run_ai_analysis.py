from ..config import get_settings
from ..database import init_db
from ..store import MongoDataStore, store_context


def main() -> None:
    settings = get_settings()
    if settings.database_backend == "mongodb":
        MongoDataStore(settings).ensure_indexes()
    else:
        init_db()
    with store_context() as store:
        report = store.analyze_today()
        print({"id": report["id"], "report_date": report["report_date"], "model": report["model"]})


if __name__ == "__main__":
    main()
