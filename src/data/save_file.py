import json
import pandas as pd
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT/"data"/"raw"
PROCESSED_DATA_DIR = PROJECT_ROOT/"data"/"processed"

def save_json(data, filename) : 
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_path = RAW_DATA_DIR/filename
    with open(save_path, "w", encoding="utf-8") as file : 
        json.dump(data, file, ensure_ascii=False, indent=4)

    print(f"json 저장 완료 : {save_path}")


def save_json_to_csv(data, filename) : 
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_path = RAW_DATA_DIR/filename

    table_name = next(iter(data))
    rows = data[table_name].get("row", [])

    # DataFrame 변환
    df = pd.DataFrame(rows)

    # CSV 저장
    df.to_csv(save_path,index=False,encoding="utf-8-sig")

    print(f"csv 저장 완료 : {save_path}/{filename}")


def save_processed_csv(data, filename):
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    save_path = PROCESSED_DATA_DIR/filename
    data.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"csv 저장 완료: {save_path}")