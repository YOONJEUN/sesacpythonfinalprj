import streamlit as st

from src.analysis.map import render_station_map
from src.data.preprocessing import preprocess_station_location

from src.data.loader import RAW_DATA_DIR, PROCESSED_DATA_DIR, load_csv

st.set_page_config(page_title="대여소 지도")

station_location_df = preprocess_station_location(load_csv("SeoulBikeStationMaster.csv"))
render_station_map(station_location_df)