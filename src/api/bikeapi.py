import requests
from config.settings import BIKE_RENTAL_DATA_URL, BIKE_STATION_USE_INFO_URL

def get_bike_rental_data(start_idx, end_idx, date, num):
    # date가 숫자인지 -가 포함된 숫자인지 if로 걸러내기
    url = f"{BIKE_RENTAL_DATA_URL}/{start_idx}/{end_idx}/{date}/{num}"
    response = requests.get(url)

    return response.json()

def get_station_use_info(start_idx, end_idx, date):
    url = f"{BIKE_STATION_USE_INFO_URL}/{start_idx}/{end_idx}/{date}"
    response = requests.get(url)

    return response.json()