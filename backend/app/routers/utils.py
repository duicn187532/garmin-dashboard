from datetime import date, timedelta


def range_to_days(value: str) -> int:
    mapping = {"7d": 7, "30d": 30, "90d": 90}
    return mapping.get(value, 30)


def cutoff_date(days: int) -> date:
    return date.today() - timedelta(days=days - 1)

