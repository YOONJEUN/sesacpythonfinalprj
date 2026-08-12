"""Functions that only read CSV and JSON files into DataFrames."""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_csv(filenames: str | list[str], data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Read one or more CSV files, supporting common Korean CSV encodings."""
    names = [filenames] if isinstance(filenames, str) else filenames
    frames = []
    for name in names:
        path = data_dir / name
        for encoding in ("utf-8-sig", "cp949"):
            try:
                frames.append(pd.read_csv(path, encoding=encoding))
                break
            except UnicodeDecodeError:
                continue
        else:
            raise UnicodeError(f"Unsupported CSV encoding: {path}")
    return pd.concat(frames, ignore_index=True)


def load_json(filename: str, data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Read a JSON file from the selected directory into a DataFrame."""
    with (data_dir / filename).open("r", encoding="utf-8") as file:
        return pd.DataFrame(json.load(file))




def load_parquet(filename: str, data_dir: Path) -> pd.DataFrame:
    """저장된 parquet 파일을 로드합니다."""
    return pd.read_parquet(data_dir / filename)
