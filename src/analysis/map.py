from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium


def render_station_map(station_location_df: pd.DataFrame) -> None:
    """대여소 위치를 지도 위에 마커로 표시합니다."""
    st.subheader("따릉이 대여소 위치")

    center_lat = station_location_df["lat"].mean()
    center_lon = station_location_df["lon"].mean()

    station_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
)

    for _, row in station_location_df.iterrows():
        popup_text = f"{row['station_id']}<br>{row['addr1']} {row.get('addr2', '')}"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="#356FA8",
            fill=True,
            fill_opacity=0.7,
            popup=popup_text,
        ).add_to(station_map)

    st_folium(station_map, width=800, height=500)