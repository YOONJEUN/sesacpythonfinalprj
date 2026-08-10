import streamlit as st
from src.api.bike_api import (
    get_bike_rental_data,
    get_station_use_info,
    save_json,
    save_csv
)

# 첫 번째 API 호출
rent_data = get_bike_rental_data(1, 5, "2022-01-01", 1)

print("공공자전거 대여 데이터")
print(rent_data)
st.write(rent_data)

# 두 번째 API 호출
station_data = get_station_use_info(1, 5, "202601")

print("대여소별 월별 이용정보")
print(station_data)
st.write(station_data)

save_json(rent_data,"SeoulBikeRentData.json")
save_csv(rent_data,"SeoulBikeRentData.csv")

save_json(station_data,"SeoulBikeStationData.json")
save_csv(station_data,"SeoulBikeStationData.csv")