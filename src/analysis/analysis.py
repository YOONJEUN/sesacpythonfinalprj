"""Aggregation, rebalancing analysis, and chart creation functions."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def calculate_monthly_imbalance(df: pd.DataFrame) -> pd.DataFrame:
    """Rank months by the sum of station-level absolute imbalance."""
    return (df.groupby("stat_mn", as_index=False).agg(imbalance_abs_sum=("imbalance_abs", "sum"))
            .sort_values("imbalance_abs_sum", ascending=False))


def make_group_statistics(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Calculate demand, duration, and distance statistics for each time feature."""
    aggregations = {"trip_count": ("RENT_ID", "size"), "avg_use_min": ("use_min", "mean"),
                    "median_use_min": ("use_min", "median"), "avg_use_dst": ("use_dst", "mean")}
    return {feature: df.groupby(feature, as_index=False).agg(**aggregations)
            for feature in ("rent_year", "rent_month", "rent_day", "rent_hour")}


def calculate_hourly_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the number of returns for each return hour."""
    return df.dropna(subset=["rtn_hour"]).groupby("rtn_hour", as_index=False).size().rename(columns={"size": "return_count"})


def calculate_station_rebalancing(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate station net flow and the absolute rebalancing priority.

    Positive net_outflow means rentals exceed returns: deliver bikes there. Negative
    values mean returns exceed rentals: collect bikes from there.
    """
    rentals = df.groupby(["RENT_ID", "RENT_NM"]).size().rename("rentals")
    returns = df.groupby(["RTN_ID", "RTN_NM"]).size().rename("returns")
    rentals.index = rentals.index.set_names(["station_id", "station_name"])
    returns.index = returns.index.set_names(["station_id", "station_name"])
    result = pd.concat([rentals, returns], axis=1).fillna(0).reset_index()
    result["net_outflow"] = result["rentals"] - result["returns"]
    result["rebalancing_priority"] = result["net_outflow"].abs()
    return result.sort_values("rebalancing_priority", ascending=False)


def calculate_top_routes(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """Find frequent origin-destination routes for transfer-corridor planning."""
    return (df.groupby(["RENT_NM", "RTN_NM"], as_index=False).size()
            .rename(columns={"size": "trip_count"}).nlargest(n, "trip_count"))


def calculate_gender_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Summarize reported gender, retaining missing values as Unknown."""
    return df["SEX_CD"].fillna("Unknown").value_counts().rename_axis("sex").reset_index(name="trip_count")


def create_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, color: str = "#2F6B9A") -> plt.Figure:
    """Create a consistently styled bar chart for the Streamlit presentation."""
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.barplot(data=data, x=x, y=y, ax=ax, color=color)
    ax.set_title(title, fontweight="bold")
    fig.tight_layout()
    return fig
