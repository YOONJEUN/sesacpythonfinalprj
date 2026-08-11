import requests

from config.settings import BIKE_RENTAL_DATA_URL, BIKE_STATION_USE_INFO_URL


def get_bike_rental_data(start_idx: int, end_idx: int, date: str, hour: int) -> dict:
    if not 0 <= hour <= 23:
        raise ValueError("hour must be between 0 and 23")
    url = f"{BIKE_RENTAL_DATA_URL}/{start_idx}/{end_idx}/{date}/{hour}"
    response = requests.get(url)
    response.raise_for_status()
    payload = response.json()
    result = payload.get("rentData", {}).get("RESULT", {})
    if result.get("CODE") != "INFO-000":
        raise RuntimeError(f"Rental API error: {result.get('CODE')} - {result.get('MESSAGE')}")
    return payload


def get_station_use_info(start_idx: int, end_idx: int, date: str) -> dict:
    response = requests.get(f"{BIKE_STATION_USE_INFO_URL}/{start_idx}/{end_idx}/{date}", timeout=30)
    response.raise_for_status()
    return response.json()
