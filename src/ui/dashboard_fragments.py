"""Independently rerunnable Streamlit dashboard sections."""

import math

import streamlit as st

from src.analysis.analysis import (
    calculate_gender_mix,
    calculate_hourly_returns,
    calculate_station_rebalancing,
    calculate_top_routes,
    create_bar_chart,
    make_group_statistics,
)


@st.fragment
def render_demand_section(rental_df):
    """Render demand charts; changing its duration filter reruns only this section."""
    with st.container(border=True):
        st.header("2. 2026년 4월 1주 대여 수요")
        st.subheader("이용시간 필터")
        st.caption("아래 이용시간 범위는 이 박스 안의 시간대별 수요와 이용 특성 그래프에만 적용됩니다.")
        filter_col, _ = st.columns([1, 2])
        with filter_col:
            max_use_hour = max(1, math.ceil(rental_df["use_min"].max() / 60))
            use_hour_range = st.slider("분석할 이용시간 범위(시간)", 0, max_use_hour, (0, max_use_hour), key="demand_duration")

        filtered_df = rental_df[rental_df["use_min"].between(use_hour_range[0] * 60, use_hour_range[1] * 60)].copy()
        if filtered_df.empty:
            st.warning("선택한 이용시간 범위에 해당하는 데이터가 없습니다.")
            return

        statistics = make_group_statistics(filtered_df)
        hourly = statistics["rent_hour"]
        hourly_returns = calculate_hourly_returns(filtered_df)
        c1, c2, c3 = st.columns(3)
        c1.metric("필터 적용 이용 건수", f"{len(filtered_df):,}건")
        c2.metric("평균 이용시간", f"{filtered_df['use_min'].mean():.1f}분")
        c3.metric("평균 이용거리", f"{filtered_df['use_dst'].mean():,.0f}m")

        st.subheader("수요 발생 시간")
        st.caption("대여와 반납 집중 시간을 파악하면, 수요가 몰리기 전에 자전거를 선제적으로 배치할 수 있습니다.")
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "trip_count", "시간대별 대여 건수", "#356FA8"), clear_figure=True)
        with c2:
            st.pyplot(create_bar_chart(hourly_returns, "rtn_hour", "return_count", "시간대별 반납 건수", "#4B9B70"), clear_figure=True)
        st.subheader("이용 특성")
        st.caption("평균 이용시간과 거리는 자전거 회전 속도를 보여주므로 재배치 시점 산정에 도움이 됩니다.")
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "avg_use_min", "시간대별 평균 이용시간", "#D9873D"), clear_figure=True)
        with c2:
            st.pyplot(create_bar_chart(hourly, "rent_hour", "avg_use_dst", "시간대별 평균 이용거리", "#A65D8B"), clear_figure=True)


@st.fragment
def render_rebalancing_section(rental_df):
    """Render rebalancing charts; changing its count filter reruns only this section."""
    with st.container(border=True):
        st.header("3. 자전거 재배치 우선순위")
        st.subheader("최소 이용 건수 필터")
        st.caption("아래 기준은 이 박스의 대여소 재배치 우선순위와 주요 이동 경로에서 소규모 사례를 제외합니다.")
        filter_col, _ = st.columns([1, 2])
        with filter_col:
            min_trip_count = st.number_input("분석할 최소 이용 건수", min_value=0, value=30, step=10, key="rebalancing_min_count")

        station_flow = calculate_station_rebalancing(rental_df)
        station_flow = station_flow[(station_flow["rentals"] + station_flow["returns"]) >= min_trip_count]
        top_routes = calculate_top_routes(rental_df)
        top_routes = top_routes[top_routes["trip_count"] >= min_trip_count]
        gender_mix = calculate_gender_mix(rental_df)

        st.caption("순유출량은 대여 건수−반납 건수입니다. 양수인 대여소는 자전거 공급이, 음수인 대여소는 자전거 회수가 우선입니다.")
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(create_bar_chart(station_flow.nlargest(15, "net_outflow").sort_values("net_outflow"), "net_outflow", "station_name", "자전거 공급 우선 대여소", "#C9534B"), clear_figure=True)
        with c2:
            st.pyplot(create_bar_chart(station_flow.nsmallest(15, "net_outflow").sort_values("net_outflow", ascending=False), "net_outflow", "station_name", "자전거 회수 우선 대여소", "#40845D"), clear_figure=True)

        st.subheader("운영 의사결정 참고 자료")
        tab1, tab2, tab3 = st.tabs(["재배치 우선 대여소", "주요 이동 경로", "성별 이용 분포"])
        with tab1:
            st.caption("절대 순유출량이 큰 대여소부터 재배치 차량의 방문 후보로 검토합니다.")
            st.dataframe(station_flow.head(30), hide_index=True, use_container_width=True)
        with tab2:
            st.caption("빈도가 높은 출발-도착 경로는 재배치 차량의 이동 축 또는 대여소 묶음 운영을 검토하는 근거가 됩니다.")
            st.dataframe(top_routes, hide_index=True, use_container_width=True)
        with tab3:
            st.caption("성별 미입력 건은 미상으로 포함한 보조적 수요 특성 자료입니다.")
            st.pyplot(create_bar_chart(gender_mix, "sex", "trip_count", "성별 대여 건수", "#6D78AD"), clear_figure=True)
