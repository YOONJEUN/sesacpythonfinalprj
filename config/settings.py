# 인증키, API 기본 주소 관리

import os
from dotenv import load_dotenv

load_dotenv()

SEOUL_BIKE_API_KEY = os.getenv("SEOUL_BIKE_API_KEY")

SEOUL_BIKE_API_BASE_URL = f"http://openapi.seoul.go.kr:8088/{SEOUL_BIKE_API_KEY}/json"

# "http://openapi.seoul.go.kr:8088/(인증키)/json/tbCycleRentData/1/5/2022-10-01/1"
# START_INDEX/END_INDEX/

# "http://openapi.seoul.go.kr:8088/(인증키)/json/tbCycleStationUseMonthInfo/1/5/202208"
# START_INDEX/END_INDEX/STATMN


# 서울시 공공자전거 대여이력 정보
BIKE_RENTAL_DATA_URL = f"{SEOUL_BIKE_API_BASE_URL}/tbCycleRentData"

# 서울시 공공자전거 대여소별 이용정보(월별)
BIKE_STATION_USE_INFO_URL = f"{SEOUL_BIKE_API_BASE_URL}/tbCycleStationUseMonthInfo"




