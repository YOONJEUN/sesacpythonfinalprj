import koreanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt
import pandas as pd


CATEGORY_ORDER = [
    "지하철/버스", "주거지", "기타", "공공기관", "회사",
    "공원", "초중고", "대학교", "문화시설",
]
COMMUTE_CATEGORIES = ["지하철/버스", "주거지", "회사"]

PATTERNS = [
    ("지하철/버스", r"역|버스|정류장|터미널|공항|교통|환승"),
    ("대학교", r"대학교|대학|캠퍼스|대학원"),
    ("초중고", r"초등|중학교|고등|학교|유치원"),
    ("공원", r"공원|한강|호수|산|숲|생태|수변"),
    ("문화시설", r"문화|미술|박물|공연|예술|영화|극장|미디어|디자인|역사|전시"),
    ("공공기관", r"구청|주민센터|보건소|경찰|소방|우체국|시청|교육청|세무|법원|행정|복지|공단"),
    ("회사", r"회사|빌딩|타워|사옥|본사|지점|KT|SK|LG|삼성|현대|GS|은행|금융|방송|연구소"),
    ("주거지", r"아파트|APT|자이|래미안|푸르지오|힐스테이트|아이파크|주공|빌라|주택"),
]


def classify_station_names(names: pd.Series) -> pd.Series:
    result = pd.Series("기타", index=names.index, dtype="string")
    normalized = names.fillna("").astype("string")
    for category, pattern in PATTERNS:
        matches = normalized.str.contains(pattern, case=False, regex=True, na=False)
        result = result.mask(matches & result.eq("기타"), category)
    return result


def add_station_categories(rental_df: pd.DataFrame) -> pd.DataFrame:
    result = rental_df.copy()
    result["rent_category"] = classify_station_names(result["rent_nm"])
    result["rtn_category"] = classify_station_names(result["rtn_nm"])
    return result


def calculate_hourly_category_imbalance(categorized_df: pd.DataFrame) -> pd.DataFrame:
    rentals = categorized_df.groupby(["rent_hour", "rent_category"]).size().rename("rentals")
    returns = categorized_df.dropna(subset=["rtn_hour"]).groupby(["rtn_hour", "rtn_category"]).size().rename("returns")
    index = pd.MultiIndex.from_product([range(24), CATEGORY_ORDER], names=["hour", "category"])
    result = pd.concat([rentals, returns], axis=1).reindex(index, fill_value=0).fillna(0).reset_index()
    result["imbalance"] = result["rentals"] - result["returns"]
    return result


def create_hourly_category_imbalance_chart(
    hourly_df: pd.DataFrame,
    selected_categories: list[str] | None = None,
) -> plt.Figure:
    """선택한 대여소 유형만 시간대별 불균형 그래프에 표시합니다."""
    fig, ax = plt.subplots(figsize=(13, 6))
    categories = selected_categories or CATEGORY_ORDER
    filtered_df = hourly_df.loc[hourly_df["category"].isin(categories)]
    category_impact = filtered_df.groupby("category")["imbalance"].apply(lambda values: values.abs().sum())
    highlighted = set(category_impact.nlargest(4).index)
    for category in categories:
        data = filtered_df.loc[filtered_df["category"].eq(category)]
        ax.plot(
            data["hour"], data["imbalance"], label=category,
            linewidth=2 if category in highlighted else 1.2,
            alpha=1 if category in highlighted else 0.5,
        )
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.axvspan(7, 9, color="#E8EEF5", alpha=0.6, label="출근 시간대")
    ax.axvspan(17, 19, color="#F9E9DB", alpha=0.6, label="퇴근 시간대")
    ax.set_xticks(range(24))
    ax.set_xlabel("시간대")
    ax.set_ylabel("불균형 수치 (대여 건수 - 반납 건수)")
    ax.set_title("대여소 유형별 시간대 불균형 추이 (2026년 4월 1일~7일)")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="대여소 유형", ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.15))
    fig.tight_layout()
    return fig


def calculate_commute_station_priorities(
    categorized_df: pd.DataFrame,
    morning_hours: range = range(7, 10),
    evening_hours: range = range(17, 20),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return commute-hour station imbalances and rebalancing priorities."""
    rentals = (
        categorized_df.groupby(["rent_id", "rent_nm", "rent_category", "rent_hour"]).size().rename("rentals").reset_index()
        .rename(columns={"rent_id": "station_id", "rent_nm": "station_name", "rent_category": "category", "rent_hour": "hour"})
    )
    returns = (
        categorized_df.dropna(subset=["rtn_hour"]).groupby(["rtn_id", "rtn_nm", "rtn_category", "rtn_hour"]).size().rename("returns").reset_index()
        .rename(columns={"rtn_id": "station_id", "rtn_nm": "station_name", "rtn_category": "category", "rtn_hour": "hour"})
    )
    station_hourly = pd.merge(rentals, returns, on=["station_id", "station_name", "category", "hour"], how="outer").fillna({"rentals": 0, "returns": 0})
    station_hourly["imbalance"] = station_hourly["rentals"] - station_hourly["returns"]
    station_hourly = station_hourly.loc[
        station_hourly["category"].isin(COMMUTE_CATEGORIES)
        & station_hourly["hour"].isin([*morning_hours, *evening_hours])
    ].copy()
    station_hourly["period"] = station_hourly["hour"].isin(morning_hours).map({True: "오전 출근", False: "오후 퇴근"})
    period_imbalance = (
        station_hourly.groupby(["station_id", "station_name", "category", "period"], as_index=False)["imbalance"].sum()
        .pivot(index=["station_id", "station_name", "category"], columns="period", values="imbalance")
        .fillna(0).reset_index()
    )
    for period in ("오전 출근", "오후 퇴근"):
        if period not in period_imbalance:
            period_imbalance[period] = 0
    priority = period_imbalance.rename(columns={"오전 출근": "morning_imbalance", "오후 퇴근": "evening_imbalance"})
    priority["commute_priority"] = priority["morning_imbalance"].abs() + priority["evening_imbalance"].abs()
    priority["net_imbalance"] = priority["morning_imbalance"] + priority["evening_imbalance"]
    priority["recommended_action"] = priority["net_imbalance"].ge(0).map({True: "자전거 공급 우선", False: "자전거 회수 우선"})
    priority = priority.sort_values("commute_priority", ascending=False).reset_index(drop=True)
    priority.index += 1
    priority.index.name = "priority_rank"
    return priority.reset_index(), station_hourly


def create_commute_priority_bubble_chart(priority_df: pd.DataFrame, top_n: int = 20) -> plt.Figure:
    """Show morning/evening imbalance patterns; bubble size encodes priority."""
    data = priority_df.head(top_n).copy()
    colors = data["category"].map({"지하철/버스": "#356FA8", "주거지": "#4B9B70", "회사": "#D9873D"})
    fig, ax = plt.subplots(figsize=(11, 8))
    ax.scatter(data["morning_imbalance"], data["evening_imbalance"], s=data["commute_priority"].clip(lower=1) * 3, c=colors, alpha=0.7, edgecolors="white", linewidth=0.8)
    for _, row in data.head(10).iterrows():
        ax.annotate(str(row["station_name"]), (row["morning_imbalance"], row["evening_imbalance"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.axhline(0, color="#666666", linewidth=0.8)
    ax.axvline(0, color="#666666", linewidth=0.8)
    ax.set_xlabel("오전 출근 불균형 (07~09시, 대여 - 반납)")
    ax.set_ylabel("오후 퇴근 불균형 (17~19시, 대여 - 반납)")
    ax.set_title("출퇴근 불균형 패턴")
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=color, label=category) for category, color in {"지하철/버스": "#356FA8", "주거지": "#4B9B70", "회사": "#D9873D"}.items()]
    ax.legend(handles=handles, title="대여소 유형", loc="best")
    ax.grid(alpha=0.25)
    fig.tight_layout()
    return fig


def create_commute_imbalance_dumbbell_chart(priority_df: pd.DataFrame, top_n: int = 15) -> plt.Figure:
    """Compare each high-priority station's morning and evening imbalance."""
    data = priority_df.head(top_n).sort_values("commute_priority").copy()
    fig, ax = plt.subplots(figsize=(11, 8))
    for _, row in data.iterrows():
        ax.hlines(
            y=row["station_name"],
            xmin=row["morning_imbalance"],
            xmax=row["evening_imbalance"],
            color="#B9B9B9",
            linewidth=2,
            zorder=1,
        )
    ax.scatter(data["morning_imbalance"], data["station_name"], color="#356FA8", s=70, label="오전 출근", zorder=3)
    ax.scatter(data["evening_imbalance"], data["station_name"], color="#D9873D", s=70, label="오후 퇴근", zorder=3)
    ax.axvline(0, color="#555555", linewidth=0.8)
    ax.set_xlabel("불균형 지수 (대여 - 반납)")
    ax.set_ylabel("")
    ax.set_title("우선 대여소의 출근·퇴근 시간대 불균형 비교")
    ax.grid(axis="x", alpha=0.25)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig
