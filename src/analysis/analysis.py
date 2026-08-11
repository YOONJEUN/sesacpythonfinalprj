import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


import re
from datetime import date
import streamlit as st

from src.data.preprocessing import preprocess_rental_data

def calculate_monthly_imbalance(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("stat_mn", as_index=False).agg(imbalance_abs_sum=("imbalance_abs", "sum"))
            .sort_values("imbalance_abs_sum", ascending=False))

def calculate_daily_station_hourly_imbalance(
    station_usage_df: pd.DataFrame,
    rental_df: pd.DataFrame,
    target_date: str = "2026-04-01",
) -> tuple[str, int, pd.DataFrame]:
    """Return hourly rental-minus-return imbalance for the most imbalanced station."""
    station_scores = (
        station_usage_df.groupby("station_name", as_index=False)
        .agg(imbalance_abs_sum=("imbalance_abs", "sum"))
        .sort_values("imbalance_abs_sum", ascending=False)
    )
    if station_scores.empty:
        raise ValueError("Station usage data is empty.")

    station_name = station_scores.iloc[0]["station_name"]
    station_id_match = re.match(r"\s*(\d+)", str(station_name))
    if station_id_match is None:
        raise ValueError(f"No leading station ID found in station name: {station_name}")
    station_id = int(station_id_match.group(1))

    target_day = pd.Timestamp(target_date).date()
    rentals_on_day = rental_df.loc[rental_df["rent_dt"].dt.date.eq(target_day)].copy()
    returns_on_day = rental_df.loc[rental_df["rtn_dt"].dt.date.eq(target_day)].copy()
    rentals_on_day["station_id_num"] = pd.to_numeric(rentals_on_day["rent_id"], errors="coerce")
    returns_on_day["station_id_num"] = pd.to_numeric(returns_on_day["rtn_id"], errors="coerce")

    rental_counts = rentals_on_day.loc[rentals_on_day["station_id_num"].eq(station_id)].groupby("rent_hour").size()
    return_counts = returns_on_day.loc[returns_on_day["station_id_num"].eq(station_id)].groupby("rtn_hour").size()
    hourly = pd.DataFrame({"hour": range(24)})
    hourly["rentals"] = hourly["hour"].map(rental_counts).fillna(0).astype(int)
    hourly["returns"] = hourly["hour"].map(return_counts).fillna(0).astype(int)
    hourly["imbalance"] = hourly["rentals"] - hourly["returns"]
    return str(station_name), station_id, hourly


def calculate_weekly_average_station_hourly_imbalance(
    rental_df: pd.DataFrame,
    start_date: str = "2026-04-01",
    end_date: str = "2026-04-07",
) -> pd.DataFrame:
    """Calculate the hourly mean station imbalance across a date range.

    Station-hour combinations without trips are included as zero so that the
    result represents the average across all stations and all seven days.
    """
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()

    rental_mask = rental_df["rent_dt"].dt.normalize().between(start, end)
    return_mask = rental_df["rtn_dt"].dt.normalize().between(start, end)
    rentals = (
        rental_df.loc[rental_mask]
        .assign(date=lambda df: df["rent_dt"].dt.normalize())
        .groupby(["date", "rent_id", "rent_hour"])
        .size()
        .rename("rentals")
        .reset_index()
        .rename(columns={"rent_id": "station_id", "rent_hour": "hour"})
    )
    returns = (
        rental_df.loc[return_mask]
        .assign(date=lambda df: df["rtn_dt"].dt.normalize())
        .groupby(["date", "rtn_id", "rtn_hour"])
        .size()
        .rename("returns")
        .reset_index()
        .rename(columns={"rtn_id": "station_id", "rtn_hour": "hour"})
    )
    station_ids = pd.Index(pd.concat([rentals["station_id"], returns["station_id"]]).dropna().unique())
    if station_ids.empty:
        return pd.DataFrame({"hour": range(24), "average_imbalance": [0.0] * 24})

    index = pd.MultiIndex.from_product(
        [pd.date_range(start, end, freq="D"), station_ids, range(24)],
        names=["date", "station_id", "hour"],
    )
    station_hourly = (
        pd.merge(rentals, returns, on=["date", "station_id", "hour"], how="outer")
        .set_index(["date", "station_id", "hour"])
        .reindex(index, fill_value=0)
        .fillna(0)
        .reset_index()
    )
    station_hourly["imbalance"] = station_hourly["rentals"] - station_hourly["returns"]
    return (
        station_hourly.groupby("hour", as_index=False)
        .agg(
            average_imbalance=("imbalance", "mean"),
            average_absolute_imbalance=("imbalance", lambda values: values.abs().mean()),
        )
    )


def calculate_average_station_imbalance_by_bins(
    rental_df: pd.DataFrame,
    feature: str,
    bins: list[float],
    labels: list[str],
) -> pd.DataFrame:
    """Calculate average station rental-minus-return imbalance for feature bins."""
    data = rental_df.dropna(subset=[feature]).copy()
    data["feature_group"] = pd.cut(
        data[feature], bins=bins, labels=labels, include_lowest=True, right=False
    )
    data = data.dropna(subset=["feature_group"])
    rentals = (
        data.groupby(["feature_group", "rent_id"], observed=False)
        .size()
        .rename("rentals")
        .reset_index()
        .rename(columns={"rent_id": "station_id"})
    )
    returns = (
        data.groupby(["feature_group", "rtn_id"], observed=False)
        .size()
        .rename("returns")
        .reset_index()
        .rename(columns={"rtn_id": "station_id"})
    )
    station_imbalance = pd.merge(
        rentals, returns, on=["feature_group", "station_id"], how="outer"
    ).fillna({"rentals": 0, "returns": 0})
    station_imbalance["imbalance"] = station_imbalance["rentals"] - station_imbalance["returns"]
    result = (
        station_imbalance.groupby("feature_group", observed=False, as_index=False)
        .agg(
            average_imbalance=("imbalance", "mean"),
            average_absolute_imbalance=("imbalance", lambda values: values.abs().mean()),
        )
    )
    return result.dropna(subset=["average_imbalance"])


def calculate_weekday_hourly_imbalance(rental_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate rental-minus-return imbalance for every weekday and hour."""
    rentals = (
        rental_df.assign(weekday=lambda df: df["rent_dt"].dt.dayofweek)
        .groupby(["weekday", "rent_hour"])
        .size()
        .rename("rentals")
    )
    returns = (
        rental_df.dropna(subset=["rtn_hour"])
        .assign(weekday=lambda df: df["rtn_dt"].dt.dayofweek)
        .groupby(["weekday", "rtn_hour"])
        .size()
        .rename("returns")
    )
    index = pd.MultiIndex.from_product([range(7), range(24)], names=["weekday", "hour"])
    result = pd.concat([rentals, returns], axis=1).reindex(index, fill_value=0).fillna(0).reset_index()
    result["imbalance"] = result["rentals"] - result["returns"]
    return result


def calculate_weektype_hourly_average_imbalance(weekday_hourly_df: pd.DataFrame) -> pd.DataFrame:
    """Average weekday-hour imbalance into weekday (Mon-Fri) and weekend groups."""
    result = weekday_hourly_df.copy()
    result["day_type"] = result["weekday"].lt(5).map({True: "평일 (월~금)", False: "주말 (토~일)"})
    return (
        result.groupby(["day_type", "hour"], as_index=False)
        .agg(
            average_rentals=("rentals", "mean"),
            average_returns=("returns", "mean"),
            average_imbalance=("imbalance", "mean"),
        )
    )


def make_group_statistics(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    aggregations = {"trip_count": ("rent_id", "size"), "avg_use_min": ("use_min", "mean"),
                    "median_use_min": ("use_min", "median"), "avg_use_dst": ("use_dst", "mean")}
    return {feature: df.groupby(feature, as_index=False).agg(**aggregations)
            for feature in ("rent_year", "rent_month", "rent_day", "rent_hour")}

def calculate_hourly_returns(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(subset=["rtn_hour"]).groupby("rtn_hour", as_index=False).size().rename(columns={"size": "return_count"})

def calculate_station_rebalancing(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate station net flow and the absolute rebalancing priority.

    Positive net_outflow means rentals exceed returns: deliver bikes there. Negative
    values mean returns exceed rentals: collect bikes from there.
    """
    rentals = df.groupby(["rent_id", "rent_nm"]).size().rename("rentals")
    returns = df.groupby(["rtn_id", "rtn_nm"]).size().rename("returns")
    rentals.index = rentals.index.set_names(["station_id", "station_name"])
    returns.index = returns.index.set_names(["station_id", "station_name"])
    result = pd.concat([rentals, returns], axis=1).fillna(0).reset_index()
    result["net_outflow"] = result["rentals"] - result["returns"]
    result["rebalancing_priority"] = result["net_outflow"].abs()
    return result.sort_values("rebalancing_priority", ascending=False)

def calculate_top_routes(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    return (df.groupby(["rent_nm", "rtn_nm"], as_index=False).size()
            .rename(columns={"size": "trip_count"}).nlargest(n, "trip_count"))

def calculate_gender_mix(df: pd.DataFrame) -> pd.DataFrame:
    return df["sex_cd"].fillna("Unknown").value_counts().rename_axis("sex").reset_index(name="trip_count")

def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, color: str = "#2F6B9A") -> plt.Figure:
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x=x, y=y, ax=ax, color=color)
    ax.set_title(title, fontweight="bold")
    fig.tight_layout()
    return fig

# ====================================================================================================================================
# ====================================================================================================================================
# ====================================================================================================================================
# ====================================================================================================================================


