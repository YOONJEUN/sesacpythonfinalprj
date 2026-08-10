import streamlit as st
import pprint as pp
from src.api.bike_api import (get_bike_rental_data, get_station_use_info,)
from src.data.save_file import (save_json, save_csv,)

months = [
    # "202507","202508","202509","202510","202511","202512",
    "202601","202602","202603","202604","202605","202606",
]

def collect_month_data(mon):
    all_rows = []
    start_index = 1
    end_index = 1000

    table_name = None
    result_meta = None
    list_total_count = None

    while True :
        print(f"{mon}의 {start_index}부터 {end_index}까지의 페이지 수집중")
        data = get_station_use_info(start_index, end_index, mon)
        # data = data = {"rentBikeStatus": {...} } 딕션너리의 형태라서 iter(data)를 하면 키값들을 순서대로 꺼낼 수 있도록 함
        # 그 상태에서 가장 첫번째 값을 next()로 가져옴 > rentBikeStatus 가져옴 > table name
        if table_name is None : 
            table_name = next(iter(data))

        # .get("row", []) 사용하는 이유는 "row"가 있으면 그 값을 가져오고 없어도 [] 반환해서 오류 발생하지 않게 하기
        # rows = data[table_name].get("row", [])

        payload = data[table_name]

        if list_total_count is None:
            list_total_count = payload.get("list_total_count")

        result_meta = payload.get("RESULT", result_meta)

        rows = payload.get("row", [])
        if not rows:
            break

        all_rows.extend(rows)

        if len(rows) < 1000 : break

        start_index += 1000
        end_index += 1000

    raw_data = {
        table_name: {
            "list_total_count": list_total_count,
            "RESULT": result_meta,
            "row": all_rows
        }
    }

    
    return raw_data

# def collect_month_data(mon):
    all_rows = []
    start_index = 1
    end_index = 1000

    while True :
        print(f"{mon}의 {start_index}부터 {end_index}까지의 페이지 수집중")
        data = get_station_use_info(start_index, end_index, mon)
        # data = data = {"rentBikeStatus": {...} } 딕션너리의 형태라서 iter(data)를 하면 키값들을 순서대로 꺼낼 수 있도록 함
        # 그 상태에서 가장 첫번째 값을 next()로 가져옴 > rentBikeStatus 가져옴 > table name
        table_name = next(iter(data))

        # .get("row", []) 사용하는 이유는 "row"가 있으면 그 값을 가져오고 없어도 [] 반환해서 오류 발생하지 않게 하기
        rows = data[table_name].get("row", [])

        if not rows : break

        all_rows.extend(rows)

        if len(rows) < 1000 : break

        start_index += 1000
        end_index += 1000
    return all_rows


def save_month_data(months) :
    for mon in months : 
        rows = collect_month_data(mon)
        filename = f"Station_{mon}.json"
        save_json(rows, filename)


# 실행 코드
save_month_data(months)


# 따릉이 대여 이력 API 호출
# rent_data = get_bike_rental_data(1, 5, "2022-01-01", 1)

# print(rent_data)
# st.write(rent_data)

# save_json(rent_data,"SeoulBikeRentData.json")
# save_csv(rent_data,"SeoulBikeRentData.csv")

