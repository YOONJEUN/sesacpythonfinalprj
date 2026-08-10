"""Functions that only read CSV and JSON files into DataFrames."""

import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"


def load_csv(filenames: str | list[str], data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Read one or more UTF-8-sig CSV files from the selected directory."""
    names = [filenames] if isinstance(filenames, str) else filenames
    return pd.concat([pd.read_csv(data_dir / name, encoding="utf-8-sig") for name in names], ignore_index=True)


def load_json(filename: str, data_dir: Path = RAW_DATA_DIR) -> pd.DataFrame:
    """Read a JSON file from the selected directory into a DataFrame."""
    with (data_dir / filename).open("r", encoding="utf-8") as file:
        return pd.DataFrame(json.load(file))
