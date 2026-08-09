from src.api.bikeapi import (
    get_bike_rental_data,
    get_station_use_info
)


# 첫 번째 API 호출
rent_data = get_bike_rental_data(1, 5, "2022-01-01", 1)

print("공공자전거 대여 데이터")
print(rent_data)


# 두 번째 API 호출
station_data = get_station_use_info(1, 5, "202208")

print("대여소별 월별 이용정보")
print(station_data)