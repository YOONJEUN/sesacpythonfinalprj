"""API collection helpers that return station-use data without saving files."""

from src.api.bike_api import get_station_use_info


def collect_month_data(month: str, page_size: int = 1000) -> dict:
    """Collect every page of one month of station-use API data."""
    rows: list[dict] = []
    start = 1
    table_name = ""
    result: dict = {}
    total_count = 0
    while True:
        response = get_station_use_info(start, start + page_size - 1, month)
        table_name = table_name or next(iter(response))
        payload = response[table_name]
        result = payload.get("RESULT", result)
        total_count = payload.get("list_total_count", total_count)
        page_rows = payload.get("row", [])
        rows.extend(page_rows)
        if len(page_rows) < page_size:
            break
        start += page_size
    return {table_name: {"list_total_count": total_count, "RESULT": result, "row": rows}}
