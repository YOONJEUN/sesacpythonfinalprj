"""서울 공공자전거 수요 불균형 및 재배치 분석 Streamlit 대시보드."""

import koreanize_matplotlib  # noqa: F401 - matplotlib 한글 폰트 설정
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

from src.analysis.analysis import calculate_monthly_imbalance, create_bar_chart
from src.data.loader import PROCESSED_DATA_DIR, load_csv
from src.data.preprocessing import add_imbalance, clean_station_df, preprocess_rental_data
from src.data.save_file import save_rental_week
from src.ui.dashboard_fragments import render_demand_section, render_rebalancing_section

st.set_page_config(page_title="서울 공공자전거 재배치 분석", layout="wide")
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

st.title("서울 공공자전거 수요 불균형·재배치 분석")
st.caption("월별 불균형 진단과 2026년 4월 1주 대여 이력 기반 운영 의사결정 지원")
loading_skeleton = st.skeleton(height=220)

# 1. API 호출 → CSV 저장: 최초 1회 실행 뒤에는 다음 줄을 주석 처리한다.
# rental_file_path = save_rental_week(start_date="2026-04-01", days=7)
# 이후 실행 시에는 위 줄을 주석 처리하고 아래 줄의 주석을 해제한다.
rental_file_path = PROCESSED_DATA_DIR / "SeoulBikeRental_20260401_7days.csv"

# 2. 저장 CSV 재로딩 → 전처리 → 연·월·일·시간대 파생변수 생성
raw_rental_df = load_csv(rental_file_path.name, data_dir=PROCESSED_DATA_DIR)
rental_df = preprocess_rental_data(raw_rental_df)

# 3. 월별 대여소 이용 데이터 로딩 → 불균형 변수 생성 → 월별 집계
station_files = ["SeoulBikeStationUseInfo_2507to2512.csv", "SeoulBikeStationUseInfo_2601to2606.csv"]
station_df = add_imbalance(clean_station_df(load_csv(station_files)))
monthly_top10 = calculate_monthly_imbalance(station_df).head(10)
loading_skeleton.empty()

with st.container(border=True):
    st.header("1. 월별 대여·반납 불균형 진단")
    st.write("절대 불균형 합계가 클수록 대여소별 대여·반납 차이가 커, 재배치 운영을 우선 검토해야 하는 달입니다.")
    c1, c2 = st.columns(2)
    c1.metric("불균형 절대값 합계가 가장 큰 월", str(monthly_top10.iloc[0]["stat_mn"]))
    c2.metric("최대 절대 불균형 합계", f"{monthly_top10.iloc[0]['imbalance_abs_sum']:,.0f}건")
    c1, c2 = st.columns((1, 1.35))
    with c1:
        st.dataframe(monthly_top10, hide_index=True, use_container_width=True)
    with c2:
        st.pyplot(create_bar_chart(monthly_top10.sort_values("imbalance_abs_sum"), "imbalance_abs_sum", "stat_mn", "월별 절대 불균형 합계 상위 10개", "#356FA8"), clear_figure=True)

# 각 fragment 내부 위젯을 변경하면 해당 분석 박스만 다시 실행된다.
render_demand_section(rental_df)
render_rebalancing_section(rental_df)
