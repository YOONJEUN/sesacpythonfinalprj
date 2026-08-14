# 🚲 서울 공공자전거 수요 불균형 분석

> 서울시 공공자전거 '따릉이'의 대여·반납 데이터를 분석하여  
> **대여소별 수요 불균형을 파악하고, 재배치가 필요한 대여소의 우선순위를 도출하는 데이터 분석 프로젝트**

<br>

[![GitHub](https://img.shields.io/badge/GitHub-Repository-181717?logo=github)](https://github.com/YOONJEUN/sesacpythonfinalprj)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](https://sesacpythonfinalprj-eun.streamlit.app/)

## 🔗 Project Links

- **GitHub**: https://github.com/YOONJEUN/sesacpythonfinalprj
- **Live Dashboard**: https://sesacpythonfinalprj-eun.streamlit.app/

---

## 1. 프로젝트 개요

서울시 공공자전거 따릉이는 대여와 반납이 서로 다른 장소에서 이루어지는 특성상  
대여소별로 자전거가 **부족하거나 과도하게 집중되는 수요 불균형**이 발생할 수 있습니다.

이 프로젝트에서는 따릉이 이용 데이터를 기반으로 대여소별 대여량과 반납량을 비교하고,

- 언제 불균형이 발생하는지
- 어떤 대여소 유형에서 불균형이 나타나는지
- 어떤 대여소의 재배치 우선순위가 높은지

를 데이터로 분석했습니다.

최종적으로 분석 결과를 **Streamlit 대시보드**로 구현하여 사용자가 대여소 유형을 선택하고 주요 분석 결과를 확인할 수 있도록 구성했습니다.

---

## 2. 프로젝트 목표

### 문제 정의

단순히 따릉이 이용량이 많은 대여소를 찾는 것이 아니라,

> **대여와 반납의 차이가 큰 대여소를 찾아 자전거 재배치가 우선적으로 필요한 지점을 파악할 수 있는가?**

를 핵심 분석 질문으로 설정했습니다.

### 분석 목표

1. 대여·반납 데이터를 이용해 대여소별 수요 불균형을 측정
2. 시간대별 수요 불균형 패턴 분석
3. 대여소 주변 특성에 따른 유형 분류
4. 출퇴근 시간대의 불균형 분석
5. 재배치 우선순위가 높은 대여소 도출
6. 분석 결과를 Streamlit 대시보드로 시각화

---

## 3. 데이터

프로젝트에서는 서울 공공자전거 이용 및 대여소 데이터를 활용했습니다.

### 원천 데이터

`data/raw/`에는 다음과 같은 원천 데이터가 저장되어 있습니다.

| 데이터 | 설명 |
|---|---|
| `SeoulBikeStationMaster.csv` | 서울 공공자전거 대여소 정보 |
| `SeoulBikeStationUseInfo_2307to2312.csv` | 2023년 7~12월 대여소 이용 정보 |
| `SeoulBikeStationUseInfo_2401to2406.csv` | 2024년 1~6월 대여소 이용 정보 |
| `SeoulBikeStationUseInfo_2407to2412.csv` | 2024년 7~12월 대여소 이용 정보 |
| `SeoulBikeStationUseInfo_2501to2506.csv` | 2025년 1~6월 대여소 이용 정보 |
| `SeoulBikeStationUseInfo_2507to2512.csv` | 2025년 7~12월 대여소 이용 정보 |
| `SeoulBikeStationUseInfo_2601to2606.csv` | 2026년 1~6월 대여소 이용 정보 |
| `seoul_municipalities_geo_simple.json` | 서울시 행정구역 공간 데이터 |

원천 데이터는 `data/raw/`에 별도로 관리하고, 분석에 사용하는 가공 데이터는 `data/processed/`에 분리하여 관리했습니다.

---

## 4. 데이터 처리 과정

전체 데이터 처리 과정은 다음과 같습니다.

```text
서울 공공자전거 데이터
        ↓
    데이터 수집
        ↓
   Raw 데이터 저장
        ↓
      전처리
        ↓
 대여·반납 데이터 결합
        ↓
  불균형 지표 생성
        ↓
 대여소 유형 분류
        ↓
      분석
        ↓
  재배치 우선순위 산출
        ↓
 Streamlit 대시보드
