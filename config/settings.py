import os
from dotenv import load_dotenv

load_dotenv()

SEOUL_BIKE_API_KEY = os.getenv("SEOUL_BIKE_API_KEY")

# 서울시 공공자전거 대여이력 정보
SEOUL_API_BASE_URL = "http://openapi.seoul.go.kr:8088/(인증키)/json/tbCycleRentData/1/5/2022-10-01/1"

# 서울시 공공자전거 대여소별 이용정보(월별)
SEOUL_API_BASE_URL = "http://openapi.seoul.go.kr:8088/(인증키)/json/tbCycleStationUseMonthInfo/1/5/202208"
