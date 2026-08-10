from src.data.loader import (load_csv,)
from src.data.preprocessing import (clean_station_df,)
from src.analysis.analysis import (add_imbalance,)

raw_df = load_csv("SeoulBikeStationUseInfo_2601to2606.csv") # 불러오기
df = clean_station_df(raw_df) # 전처리
df = add_imbalance(df).copy() # 파생변수 생성

print(df.head())