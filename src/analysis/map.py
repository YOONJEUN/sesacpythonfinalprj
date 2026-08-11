from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from folium import folium

from streamlit_folium import st_folium

import folium


def render_commute_priority_map(priority_df: pd.DataFrame, station_location_df: pd.DataFrame, top_n: int = 15) -> None:
    """Render high-priority commute stations for delivery and collection planning."""
    priority_data = priority_df.head(top_n).copy()
    priority_data["location_station_id"] = "ST-" + pd.to_numeric(
        priority_data["station_id"], errors="coerce"
    ).astype("Int64").astype("string")
    locations = station_location_df.copy()
    locations["station_id"] = locations["station_id"].astype("string")
    map_data = priority_data.merge(
        locations[["station_id", "lat", "lon"]],
        left_on="location_station_id",
        right_on="station_id",
        how="inner",
    ).dropna(subset=["lat", "lon"])
    if map_data.empty:
        st.warning("우선 대여소의 위치 정보를 찾을 수 없습니다.")
        return

    station_map = folium.Map(
        location=[map_data["lat"].mean(), map_data["lon"].mean()],
        zoom_start=11,
        tiles="CartoDB positron",
    )
    max_priority = max(1, map_data["commute_priority"].max())
    for _, row in map_data.iterrows():
        needs_supply = row["net_imbalance"] >= 0
        color = "#C9534B" if needs_supply else "#356FA8"
        action = "자전거 공급 우선" if needs_supply else "자전거 회수 우선"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=6 + 16 * row["commute_priority"] / max_priority,
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.72,
            tooltip=(
                f"{row['priority_rank']}위 | {row['station_name']}<br>"
                f"{row['category']} | {action}<br>"
                f"오전: {row['morning_imbalance']:+,.0f} / 오후: {row['evening_imbalance']:+,.0f}<br>"
            ),
        ).add_to(station_map)

    legend_html = """
    <div style='position: fixed; bottom: 25px; left: 25px; z-index: 1000;
                background: white; border: 1px solid #999; border-radius: 4px; padding: 10px;'>
      <b>출퇴근 재배치 우선순위</b><br>
      <span style='color:#C9534B;'>●</span> 자전거 공급 우선<br>
      <span style='color:#356FA8;'>●</span> 자전거 회수 우선<br>
      원이 클수록 우선순위가 높음
    </div>
    """
    station_map.get_root().html.add_child(folium.Element(legend_html))
    st_folium(station_map, height=620, use_container_width=True, returned_objects=[])
def render_station_map(station_location_df: pd.DataFrame) -> None:
    st.subheader("따릉이 대여소 위치")

    center_lat = station_location_df["lat"].mean()
    center_lon = station_location_df["lon"].mean()

    station_map = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles="Stamen Toner"
)

    for _, row in station_location_df.iterrows():
        popup_text = "123123"

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="#356FA8",
            fill=True,
            fill_opacity=0.7,
            popup=popup_text,
        ).add_to(station_map)

    folium(station_map, width=800, height=500)
def render_station_flow_map(station_flow_df: pd.DataFrame, min_trip_count: int = 30) -> None:
    """Render proportional flow circles: red for net outflow, blue for net inflow."""
    map_data = station_flow_df.loc[
        (station_flow_df["rentals"] + station_flow_df["returns"]) >= min_trip_count
    ].copy()
    map_data = map_data.dropna(subset=["lat", "lon", "net_outflow"])
    if map_data.empty:
        st.warning("No stations match the selected minimum trip count.")
        return

    center = [map_data["lat"].mean(), map_data["lon"].mean()]
    station_map = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")
    max_abs_flow = max(1, map_data["net_outflow"].abs().max())

    for _, row in map_data.iterrows():
        net_outflow = int(row["net_outflow"])
        radius = 60 + 440 * abs(net_outflow) / max_abs_flow
        color = "#C9534B" if net_outflow > 0 else "#356FA8"
        direction = "Net outflow (bikes needed)" if net_outflow > 0 else "Net inflow (bikes to collect)"
        if net_outflow == 0:
            color = "#808080"
            direction = "Balanced"

        folium.Circle(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.55,
            tooltip=(
                f"{row['station_name']}<br>"
                f"{direction}<br>"
                f"Net flow: {net_outflow:+,}<br>"
                f"Rentals: {int(row['rentals']):,} | Returns: {int(row['returns']):,}"
            ),
        ).add_to(station_map)

    legend_html = """
    <div style='position: fixed; bottom: 25px; left: 25px; z-index: 1000;
                background: white; border: 1px solid #999; border-radius: 4px; padding: 10px;'>
      <b>Station net flow</b><br>
      <span style='color:#C9534B;'>?</span> Net outflow: bikes needed<br>
      <span style='color:#356FA8;'>?</span> Net inflow: bikes to collect<br>
      Circle area indicates absolute net-flow size
    </div>
    """
    station_map.get_root().html.add_child(folium.Element(legend_html))
    st_folium(station_map, height=700, use_container_width=True, returned_objects=[])

def render_district_flow_choropleth(
    district_flow_df: pd.DataFrame,
    geojson_path: Path,
) -> None:
    """Render a diverging choropleth of district-level net bike flow."""
    import json
    from branca.colormap import LinearColormap

    with geojson_path.open(encoding="utf-8") as file:
        geojson_data = json.load(file)

    values_by_district = district_flow_df.set_index("district_en").to_dict("index")
    max_abs_flow = max(1, district_flow_df["net_outflow"].abs().max())
    color_scale = LinearColormap(
        colors=["#356FA8", "#F7F7F7", "#C9534B"],
        vmin=-max_abs_flow,
        vmax=max_abs_flow,
        caption="District net flow (rentals - returns)",
    )

    for feature in geojson_data["features"]:
        properties = feature["properties"]
        flow = values_by_district.get(properties["name_eng"], {})
        properties["net_outflow"] = int(flow.get("net_outflow", 0))
        properties["rentals"] = int(flow.get("rentals", 0))
        properties["returns"] = int(flow.get("returns", 0))

    district_map = folium.Map(location=[37.5665, 126.9780], zoom_start=11, tiles="CartoDB positron")
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature: {
            "fillColor": color_scale(feature["properties"]["net_outflow"]),
            "color": "#555555",
            "weight": 1,
            "fillOpacity": 0.72,
        },
        highlight_function=lambda feature: {"weight": 3, "fillOpacity": 0.9},
        tooltip=folium.GeoJsonTooltip(
            fields=["name_eng", "net_outflow", "rentals", "returns"],
            aliases=["District", "Net flow", "Rentals", "Returns"],
            localize=True,
            sticky=False,
        ),
    ).add_to(district_map)
    color_scale.add_to(district_map)
    st_folium(district_map, height=700, use_container_width=True, returned_objects=[])
