import requests
import json
import streamlit as st
import pandas as pd
from pathlib import Path
from config.settings import BIKE_RENTAL_DATA_URL, BIKE_STATION_USE_INFO_URL

def get_bike_rental_data(start_idx, end_idx, date, num):
    # date가 숫자인지 -가 포함된 숫자인지 if로 걸러내기
    url = f"{BIKE_RENTAL_DATA_URL}/{start_idx}/{end_idx}/{date}/{num}"
    response = requests.get(url)
    response.raise_for_status() # 오류가 발생하면 예외를 발생시킴
    return response.json()

def get_station_use_info(start_idx, end_idx, date):
    url = f"{BIKE_STATION_USE_INFO_URL}/{start_idx}/{end_idx}/{date}"
    response = requests.get(url)
    response.raise_for_status() 
    return response.json()

def save_json(data, filename) : 
    save_dir = Path("data/raw")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir/filename

    with open(save_path, "w", encoding="utf-8") as file : 
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"json 저장 완료 : {save_path}/{filename}")


def save_csv(data, filename) : 
    save_dir = Path("data/raw")
    save_dir.mkdir(parents=True, exist_ok=True)
    save_path = save_dir/filename

    table_name = next(iter(data)) # 이게 뭐임?
    rows = data[table_name].get("row", []) # 이것도 뭐임?

    # DataFrame 변환
    df = pd.DataFrame(rows)

    # CSV 저장
    df.to_csv(save_path,index=False,encoding="utf-8-sig")

    print(f"csv 저장 완료 : {save_path}/{filename}")







