# 저장된 데이터를 DataFrame으로 읽기
# 읽기만 담당

import json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DARA_DIR = PROJECT_ROOT/"data"/"raw"

def load_json(filename) : 
    file_path = RAW_DARA_DIR/filename
    with open(file_path, "r", encoding="utf-8") as file : 
        data = json.load(file)
    return pd.DataFrame(data)

# df = load_json("SeoulBikeRentData.json")

# def load_csv(filename) : 
#     file_path = RAW_DARA_DIR / filename
#     return pd.read_csv(file_path, encoding="utf-8-sig")

def load_csv(filenames) : 
    dfs = []
    for filename in filenames : 
        file_path = RAW_DARA_DIR / filename
        df = pd.read_csv(file_path, encoding="utf-8-sig")
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)

# df = load_csv("SeoulBikeStationUseInfo_2601to2606.csv")
# print(df)
# print(df.columns)
# SeoulBikeStationUseInfo_2601to2606 : ['자치구', '대여소명', '기준년월', '대여건수', '반납건수']

# print(df["rentData"]["row"][0].keys())
# ['BIKE_ID', 'RENT_DT', 'RENT_ID', 'RENT_NM', 'RENT_HOLD', 'RTN_DT', 'RTN_ID', 'RTN_NM', 'RTN_HOLD', 'USE_MIN', 'USE_DST', 'USR_CLS_CD', 'BIRTH_YEAR', 'RENT_STATION_ID', 'RETURN_STATION_ID', 'BIKE_SE_CD', 'START_INDEX', 'END_INDEX', 'RNUM']











