import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


import re
from datetime import date
import streamlit as st

from src.data.preprocessing import preprocess_rental_data
from src.analysis.station_category import CATEGORY_COLORS

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
    selected_categories: list[str] | None = None,
    start_date: str = "2026-04-01",
    end_date: str = "2026-04-07",
) -> pd.DataFrame:
    """선택한 대여소 유형을 기준으로 시간대별 평균 불균형을 계산합니다."""
    start = pd.Timestamp(start_date).normalize()
    end = pd.Timestamp(end_date).normalize()

    # --------------------------------------------------
    # 대여 데이터
    # --------------------------------------------------
    rental_mask = rental_df["rent_dt"].dt.normalize().between(start, end)
    rentals_data = rental_df.loc[rental_mask].copy()
    if selected_categories is not None:
        rentals_data = rentals_data.loc[
            rentals_data["rent_category"].isin(selected_categories)
        ]
    rentals = (
        rental_df.loc[rental_mask]
        .assign(date=lambda df: df["rent_dt"].dt.normalize())
        .groupby(["date", "rent_id", "rent_hour"])
        .size()
        .rename("rentals")
        .reset_index()
        .rename(columns={"rent_id": "station_id", "rent_hour": "hour"})
    )

    # --------------------------------------------------
    # 반납 데이터
    # --------------------------------------------------
    return_mask = rental_df["rtn_dt"].dt.normalize().between(start, end)
    returns_data = rental_df.loc[return_mask].copy()
    if selected_categories is not None:
        returns_data = returns_data.loc[
            returns_data["rtn_category"].isin(selected_categories)
        ]

    returns = (
        rental_df.loc[return_mask]
        .assign(date=lambda df: df["rtn_dt"].dt.normalize())
        .groupby(["date", "rtn_id", "rtn_hour"])
        .size()
        .rename("returns")
        .reset_index()
        .rename(columns={"rtn_id": "station_id", "rtn_hour": "hour"})
    )

    # --------------------------------------------------
    # 대상 대여소
    # --------------------------------------------------
    station_ids = pd.Index(pd.concat([rentals["station_id"], returns["station_id"]]).dropna().unique())
    if station_ids.empty:
        return pd.DataFrame({"hour": range(24), "average_imbalance": [0.0] * 24, "average_absolute_imbalance": [0.0] * 24,})

    # --------------------------------------------------
    # 모든 날짜 × 대여소 × 시간 조합 생성
    # --------------------------------------------------
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

    # --------------------------------------------------
    # 불균형
    # --------------------------------------------------
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

def calculate_station_rebalancing(df: pd.DataFrame, selected_categories: list[str] | None = None,) -> pd.DataFrame:
    """선택한 대여소 유형의 재배치 우선순위를 계산합니다."""

    # --------------------------------------------------
    # 대여
    # --------------------------------------------------
    rental_data = df.copy()
    if selected_categories is not None:
        rental_data = rental_data.loc[
            rental_data["rent_category"].isin(selected_categories)
        ]
    rentals = rental_data.groupby(["rent_id", "rent_nm"]).size().rename("rentals")

    # --------------------------------------------------
    # 반납
    # --------------------------------------------------
    return_data = df.copy()
    if selected_categories is not None:
        return_data = return_data.loc[
            return_data["rtn_category"].isin(selected_categories)
        ]

    returns = return_data.groupby(["rtn_id", "rtn_nm"]).size().rename("returns")
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

def create_bar_chart(
    data: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str = "#2F6B9A",
    x_label: str | None = None,
    y_label: str | None = None,
) -> plt.Figure:
    """막대그래프를 만들고, 필요하면 화면용 한글 축 라벨을 지정합니다."""
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x=x, y=y, ax=ax, color=color)
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel(x_label or x)
    ax.set_ylabel(y_label or y)
    fig.tight_layout()
    return fig

# ====================================================================================================================================
# ====================================================================================================================================
# ====================================================================================================================================
# ====================================================================================================================================

def create_commute_priority_bar_chart(
    priority_df: pd.DataFrame,
    top_n: int = 20,
) -> plt.Figure:
    """재배치 우선순위 상위 대여소를 가로 막대그래프로 표시합니다."""

    data = (
        priority_df
        .head(top_n)
        .sort_values("commute_priority", ascending=True)
        .copy()
    )

    fig, ax = plt.subplots(figsize=(10, 8))

    # 대여소 유형별 색상
    colors = [
        CATEGORY_COLORS.get(category, "#999999")
        for category in data["category"]
    ]

    bars = ax.barh(
        data["station_name"].tolist(),
        data["commute_priority"].tolist(),
        color=colors,
    )

    # 막대 끝에 수치 표시
    ax.bar_label(
        bars,
        labels=[
            f"{value:,.0f}"
            for value in data["commute_priority"]
        ],
        padding=5,
        fontsize=9,
    )

    ax.set_xlabel("재배치 우선순위")
    ax.set_ylabel("", rotation=70)
    ax.set_title(f"재배치 우선순위 상위 {top_n}개 대여소")

    ax.grid(axis="x", alpha=0.25)

    fig.tight_layout()

    return fig
