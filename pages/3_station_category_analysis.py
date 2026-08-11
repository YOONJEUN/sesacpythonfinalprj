import streamlit as st

from src.analysis.station_category import (
    add_station_categories,
    calculate_hourly_category_imbalance,
    create_hourly_category_imbalance_chart,
)
from src.data.loader import PROCESSED_DATA_DIR, load_csv
from src.data.save_file import save_processed_data


st.set_page_config(page_title="\ub300\uc5ec\uc18c \uc720\ud615\ubcc4 \ubd88\uade0\ud615", layout="wide")
st.title("\ub300\uc5ec\uc18c \uc720\ud615\ubcc4 \uc2dc\uac04\ub300 \ubd88\uade0\ud615")
st.write("\ub300\uc5ec\uc18c\uba85\uc5d0 \ud3ec\ud568\ub41c \uc2dc\uc124 \ud0a4\uc6cc\ub4dc\ub97c \ubc14\ud0d5\uc73c\ub85c \uc720\ud615\uc744 \ubd84\ub958\ud588\uc2b5\ub2c8\ub2e4. \ubd88\uade0\ud615 \uc218\uce58\ub294 7\uc77c\uac04 \uc720\ud615\ubcc4 \uc2dc\uac04\ub300 \ub300\uc5ec \uac74\uc218\uc5d0\uc11c \ubc18\ub0a9 \uac74\uc218\ub97c \ube80 \uac12\uc785\ub2c8\ub2e4.")


@st.cache_data(show_spinner="\ub300\uc5ec\uc18c\uba85\uc744 \uc720\ud615\ubcc4\ub85c \ubd84\ub958\ud558\ub294 \uc911...")
def load_categorized_rentals():
    rentals = load_csv("SeoulBikeRental_20260401_7days_processed.csv", data_dir=PROCESSED_DATA_DIR)
    return add_station_categories(rentals)


categorized_rentals = load_categorized_rentals()
output_filename = "SeoulBikeRental_20260401_7days_station_categories.csv"
output_path = PROCESSED_DATA_DIR / output_filename
if not output_path.exists():
    save_processed_data(categorized_rentals, output_filename)

hourly_imbalance = calculate_hourly_category_imbalance(categorized_rentals)
st.pyplot(create_hourly_category_imbalance_chart(hourly_imbalance), clear_figure=True)

st.subheader("\uc720\ud615\ubcc4 \uc694\uc57d")
summary = hourly_imbalance.groupby("category", as_index=False).agg(
    total_imbalance=("imbalance", "sum"),
    hourly_peak_abs_imbalance=("imbalance", lambda values: values.abs().max()),
)
st.dataframe(summary, hide_index=True, use_container_width=True)
st.dataframe(hourly_imbalance, hide_index=True, use_container_width=True)
