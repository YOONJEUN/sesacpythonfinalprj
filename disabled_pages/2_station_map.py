# Disabled Streamlit page: retained as source only. Move it back under `pages/` to re-enable.
import pandas as pd
import streamlit as st

from src.analysis.analysis import calculate_station_rebalancing
from src.analysis.map import render_station_flow_map
from src.data.loader import PROCESSED_DATA_DIR, RAW_DATA_DIR, load_csv
from src.analysis.map import render_district_flow_choropleth
from src.data.preprocessing import preprocess_rental_data

st.set_page_config(page_title="Seoul Bike Station Flow Map", layout="wide", page_icon="???")
st.title("Seoul Bike Station Net Flow Map")
st.write("Red circles show net outflow (bikes needed); blue circles show net inflow (bikes to collect). Circle area represents the absolute net-flow size.")

@st.cache_data(show_spinner="Loading station flow data...")
def load_station_flow_data() -> pd.DataFrame:
    station_locations = load_csv("SeoulBikeStationMaster_processed.csv", data_dir=PROCESSED_DATA_DIR)
    rental_df = preprocess_rental_data(
        load_csv("SeoulBikeRental_20260401_7days.csv", data_dir=RAW_DATA_DIR)
    )
    station_flow = calculate_station_rebalancing(rental_df)
    station_flow["station_id"] = "ST-" + pd.to_numeric(
        station_flow["station_id"], errors="coerce"
    ).astype("Int64").astype("string")
    return station_flow.merge(station_locations, on="station_id", how="inner")

station_flow_df = load_station_flow_data()
district_name_en = {"\uac15\ub0a8\uad6c": "Gangnam-gu", "\uac15\ub3d9\uad6c": "Gangdong-gu", "\uac15\ubd81\uad6c": "Gangbuk-gu", "\uac15\uc11c\uad6c": "Gangseo-gu", "\uad00\uc545\uad6c": "Gwanak-gu", "\uad11\uc9c4\uad6c": "Gwangjin-gu", "\uad6c\ub85c\uad6c": "Guro-gu", "\uae08\ucc9c\uad6c": "Geumcheon-gu", "\ub178\uc6d0\uad6c": "Nowon-gu", "\ub3c4\ubd09\uad6c": "Dobong-gu", "\ub3d9\ub300\ubb38\uad6c": "Dongdaemun-gu", "\ub3d9\uc791\uad6c": "Dongjak-gu", "\ub9c8\ud3ec\uad6c": "Mapo-gu", "\uc11c\ub300\ubb38\uad6c": "Seodaemun-gu", "\uc11c\ucd08\uad6c": "Seocho-gu", "\uc131\ub3d9\uad6c": "Seongdong-gu", "\uc131\ubd81\uad6c": "Seongbuk-gu", "\uc1a1\ud30c\uad6c": "Songpa-gu", "\uc591\ucc9c\uad6c": "Yangcheon-gu", "\uc601\ub4f1\ud3ec\uad6c": "Yeongdeungpo-gu", "\uc6a9\uc0b0\uad6c": "Yongsan-gu", "\uc740\ud3c9\uad6c": "Eunpyeong-gu", "\uc885\ub85c\uad6c": "Jongno-gu", "\uc911\uad6c": "Jung-gu", "\uc911\ub791\uad6c": "Jungnang-gu"}
# radio 버튼으로 
map_mode = st.radio("Map view", ["Station net flow", "District imbalance cluster"], horizontal=True)
original_station_renderer = render_station_flow_map

def render_station_flow_map(station_data: pd.DataFrame, min_trip_count: int) -> None:
    if map_mode == "Station net flow":
        original_station_renderer(station_data, min_trip_count)
        return
    district_data = station_data.copy()
    district_data["district"] = district_data["addr1"].astype("string").str.extract(r"([^\s]+\uad6c)", expand=False)
    district_data["district_en"] = district_data["district"].map(district_name_en)
    district_data = district_data.dropna(subset=["district_en"])
    district_data = district_data.groupby("district_en", as_index=False).agg(
        net_outflow=("net_outflow", "sum"), rentals=("rentals", "sum"), returns=("returns", "sum"), station_count=("station_id", "size")
    )
    st.write("District color indicates summed net flow. Red: more rentals; blue: more returns.")
    st.caption("Use this to form hypotheses; validate commute effects with time-of-day filters or land-use data.")
    render_district_flow_choropleth(district_data, RAW_DATA_DIR / "seoul_municipalities_geo_simple.json")
    st.dataframe(district_data.sort_values("net_outflow", key=lambda value: value.abs(), ascending=False), hide_index=True, use_container_width=True)

min_trip_count = st.slider("Minimum number of trips", 0, 200, 30, 10)
st.caption(f"Mapped stations: {len(station_flow_df):,}")
render_station_flow_map(station_flow_df, min_trip_count=min_trip_count)
