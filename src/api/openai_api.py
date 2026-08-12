import os

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def generate_monthly_imbalance_insight(
    monthly_imbalances: dict[str, pd.DataFrame],
    average_rentals: pd.Series,
    month_labels: list[str],
    selected_periods: list[str],
) -> str:
    """Generate a short operational insight for the monthly imbalance chart."""
    period_summaries = []
    for period in selected_periods:
        data = monthly_imbalances[period].sort_values("stat_mn").reset_index(drop=True)
        highest = data.loc[data["imbalance_abs_sum"].idxmax()]
        lowest = data.loc[data["imbalance_abs_sum"].idxmin()]
        period_summaries.append(
            f"- {period}: 최고 {highest['stat_mn']} ({highest['imbalance_abs_sum']:,.0f}), "
            f"최저 {lowest['stat_mn']} ({lowest['imbalance_abs_sum']:,.0f})"
        )

    rental_by_month = pd.Series(average_rentals.to_list(), index=month_labels)
    highest_rental_month = rental_by_month.idxmax()
    lowest_rental_month = rental_by_month.idxmin()

    prompt = f"""
당신은 서울 공공자전거 따릉이 재배치 운영 분석가입니다.
아래는 '월별 불균형 합계와 전체 대여 건수 추이 비교' 그래프의 요약 데이터입니다.
불균형 합계는 대여소별 대여·반납 차이의 절댓값 합계이며, 값이 클수록 재배치 운영 검토가 필요한 상태입니다.

[선택 기간별 불균형 요약]
{chr(10).join(period_summaries)}

[전체 대여 건수 평균]
- 최고: {highest_rental_month} ({rental_by_month.max():,.0f}건)
- 최저: {lowest_rental_month} ({rental_by_month.min():,.0f}건)

다음 형식으로 한국어 350자 이내로 작성하세요.

**핵심 인사이트**
- 그래프에서 확인되는 불균형과 대여 건수의 계절적 특징 2가지

**운영 제안**
- 재배치 운영에 활용할 수 있는 간단한 제안 1가지

그래프에 없는 원인을 사실처럼 단정하지 마세요.
"""

    response = client.responses.create(
        instructions="제공된 수치만 근거로, 명확하고 간결한 운영 인사이트를 작성하세요.",
        model="gpt-4o-mini",
        input=prompt,
    )
    return response.output_text
