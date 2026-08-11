import pandas as pd
import streamlit as st
import seaborn as sns
import matplotlib.pyplot as plt
import koreanize_matplotlib


# ============================================================
# 1. 페이지 설정
# ============================================================

st.set_page_config(
    page_title="서울 지하철 이용 패턴 분석",
    page_icon="🚇",
    layout="wide"
)


# ============================================================
# 2. 제목
# ============================================================

st.title("🚇 서울 지하철 이용 패턴 분석")
st.markdown(
    """
    서울교통공사 공공데이터를 활용하여
    **역별·시간대별·호선별·월별 지하철 이용 패턴**을 분석합니다.
    
    - **일별통행통계:** 1~5월 자료 활용
    - **월별 승하차인원:** 데이터 제공 전체 기간 활용
    """
)


# ============================================================
# 3. 데이터 불러오기
# ============================================================

@st.cache_data
def load_data():

    daily = pd.read_csv(
        "서울교통공사_일별통행통계_20251231.csv",
        encoding="cp949"
    )

    monthly = pd.read_csv(
        "서울교통공사_월별 승하차인원_20251231.csv",
        encoding="cp949"
    )

    return daily, monthly


daily, monthly = load_data()


# ============================================================
# 4. 시간대 컬럼
# ============================================================

hour_cols = [
    "04시", "05시", "06시", "07시",
    "08시", "09시", "10시", "11시",
    "12시", "13시", "14시", "15시",
    "16시", "17시", "18시", "19시",
    "20시", "21시", "22시", "23시",
    "00시", "01시", "02시", "03시"
]


# ============================================================
# 5. 데이터 전처리
# ============================================================

@st.cache_data
def preprocess_data(daily, monthly):

    daily = daily.copy()
    monthly = monthly.copy()

    # 시간대별 데이터 숫자형 변환
    for col in hour_cols:
        daily[col] = pd.to_numeric(
            daily[col],
            errors="coerce"
        ).fillna(0)

    # 월별 승하차인원 숫자형 변환
    monthly["승하차인원수"] = pd.to_numeric(
        monthly["승하차인원수"],
        errors="coerce"
    ).fillna(0)

    # 날짜 변환
    daily["수송일자"] = pd.to_datetime(
        daily["수송일자"],
        errors="coerce"
    )

    monthly["수송연월"] = pd.to_datetime(
        monthly["수송연월"],
        errors="coerce"
    )

    # 하루 이용량
    daily["일일이용량"] = daily[hour_cols].sum(axis=1)

    return daily, monthly


daily, monthly = preprocess_data(
    daily,
    monthly
)


# ============================================================
# 6. 기본 분석 데이터 생성
# ============================================================

# ------------------------------------------------------------
# 역별 이용량
# ------------------------------------------------------------

station_total = (
    daily
    .groupby("역명")["일일이용량"]
    .sum()
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 시간대별 이용량
# ------------------------------------------------------------

hourly_usage = daily[hour_cols].sum()


# ------------------------------------------------------------
# 호선별 승차·하차 이용량
# ------------------------------------------------------------

line_usage = (
    daily
    .groupby(["호선", "승하차구분"])["일일이용량"]
    .sum()
    .unstack()
)


# 호선별 총 이용량
line_total = (
    line_usage
    .sum(axis=1)
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 역별·시간대별 이용량
# ------------------------------------------------------------

station_hourly = (
    daily
    .groupby("역명")[hour_cols]
    .sum()
)


# ------------------------------------------------------------
# 월별 이용량
# ------------------------------------------------------------

monthly_usage = (
    monthly
    .groupby("수송연월")["승하차인원수"]
    .sum()
    .sort_index()
)


# ============================================================
# 7. 사이드바
# ============================================================

st.sidebar.title("📌 분석 메뉴")

menu = st.sidebar.radio(
    "분석 항목을 선택하세요.",
    [
        "🏠 전체 요약",
        "🚉 역별 이용량",
        "🕐 시간대별 이용량",
        "🚇 호선별 이용량",
        "🔥 역별·시간대별 패턴",
        "📅 월별 이용량"
    ]
)


# ============================================================
# 8. 전체 요약
# ============================================================

if menu == "🏠 전체 요약":

    st.header("📊 서울 지하철 이용 현황")

    st.info(
        "※ 역별·시간대별·호선별 분석은 일별통행통계의 "
        "제공 기간인 1~5월 자료를 사용합니다. "
        "월별 분석은 월별 승하차인원 데이터의 전체 제공 기간을 사용합니다."
    )

    # --------------------------------------------------------
    # 주요 지표
    # --------------------------------------------------------

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "이용량이 가장 많은 역",
        station_total.idxmax()
    )

    col2.metric(
        "가장 많은 시간대",
        hourly_usage.idxmax()
    )

    col3.metric(
        "이용량이 가장 많은 호선",
        line_total.idxmax()
    )

    col4.metric(
        "이용량이 가장 많은 월",
        monthly_usage.idxmax().strftime("%Y-%m")
    )


    st.divider()


    # --------------------------------------------------------
    # 분석 질문
    # --------------------------------------------------------

    st.subheader("🔎 분석 질문")

    st.markdown(
        """
        1. **이용량이 많은 역은 어디인가?**
        2. **이용객이 집중되는 시간대는 언제인가?**
        3. **호선별 이용량에는 어떤 차이가 있는가?**
        4. **역별·시간대별 이용 패턴은 어떻게 다른가?**
        5. **월별 이용량은 어떻게 변화하는가?**
        """
    )


    # --------------------------------------------------------
    # TOP 10 역
    # --------------------------------------------------------

    st.subheader("🚉 이용량이 많은 역 TOP 10")

    top10 = station_total.head(10)

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(
        x=top10.values,
        y=top10.index,
        color="steelblue",
        ax=ax
    )

    ax.set_xlabel("이용객 수 (명)")
    ax.set_ylabel("역명")
    ax.set_title("이용량이 많은 역 TOP 10")

    st.pyplot(fig)


# ============================================================
# 9. 역별 이용량
# ============================================================

elif menu == "🚉 역별 이용량":

    st.header("🚉 역별 이용량 분석")

    st.caption(
        "일별통행통계 1~5월 기준"
    )


    # --------------------------------------------------------
    # TOP 10
    # --------------------------------------------------------

    top10 = station_total.head(10)

    fig, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(
        x=top10.values,
        y=top10.index,
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        "서울 지하철 이용량이 많은 역 TOP 10"
    )

    ax.set_xlabel("이용객 수 (명)")
    ax.set_ylabel("역명")

    st.pyplot(fig)


    # --------------------------------------------------------
    # 역 선택
    # --------------------------------------------------------

    st.subheader("🔎 역 선택")

    selected_station = st.selectbox(
        "확인할 역을 선택하세요.",
        station_total.index
    )


    selected_usage = station_hourly.loc[
        selected_station
    ]


    col1, col2 = st.columns(2)

    col1.metric(
        "선택한 역",
        selected_station
    )

    col2.metric(
        "총 이용량",
        f"{station_total[selected_station]:,.0f}명"
    )


    # --------------------------------------------------------
    # 선택 역 시간대 그래프
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(10, 5))

    sns.lineplot(
        x=selected_usage.index,
        y=selected_usage.values,
        marker="o",
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        f"{selected_station} 시간대별 이용량"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수 (명)")
    ax.tick_params(axis="x", rotation=45)

    st.pyplot(fig)


# ============================================================
# 10. 시간대별 이용량
# ============================================================

elif menu == "🕐 시간대별 이용량":

    st.header("🕐 시간대별 이용량 분석")

    st.caption(
        "일별통행통계 1~5월 기준"
    )


    # --------------------------------------------------------
    # 가장 많은 시간대
    # --------------------------------------------------------

    max_hour = hourly_usage.idxmax()
    max_value = hourly_usage.max()


    col1, col2 = st.columns(2)

    col1.metric(
        "이용객이 가장 많은 시간대",
        max_hour
    )

    col2.metric(
        "해당 시간대 이용량",
        f"{max_value:,.0f}명"
    )


    # --------------------------------------------------------
    # 시간대 그래프
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(14, 6))

    sns.lineplot(
        x=hourly_usage.index,
        y=hourly_usage.values,
        marker="o",
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        "서울 지하철 시간대별 이용량 (1~5월)"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수 (명)")
    ax.grid(alpha=0.3)

    st.pyplot(fig)


    # --------------------------------------------------------
    # 시간대별 데이터
    # --------------------------------------------------------

    st.subheader("시간대별 이용량")

    hourly_df = pd.DataFrame({
        "시간대": hourly_usage.index,
        "이용객 수": hourly_usage.values
    })

    st.dataframe(
        hourly_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 11. 호선별 이용량
# ============================================================

elif menu == "🚇 호선별 이용량":

    st.header("🚇 호선별 이용량 분석")

    st.caption(
        "일별통행통계 1~5월 기준"
    )


    # --------------------------------------------------------
    # 가장 많은 호선 / 가장 적은 호선
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    col1.metric(
        "이용량이 가장 많은 호선",
        line_total.idxmax()
    )

    col2.metric(
        "이용량이 가장 적은 호선",
        line_total.idxmin()
    )


    # --------------------------------------------------------
    # 호선별 총 이용량
    # --------------------------------------------------------

    st.subheader("호선별 총 이용량")

    fig, ax = plt.subplots(figsize=(12, 6))

    line_total.sort_values(ascending=False).plot(
        kind="bar",
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        "서울 지하철 호선별 총 이용량"
    )

    ax.set_xlabel("호선")
    ax.set_ylabel("승하차 인원 (명)")
    ax.tick_params(axis="x", rotation=0)

    st.pyplot(fig)


    # --------------------------------------------------------
    # 승차 / 하차 비교
    # --------------------------------------------------------

    st.subheader("호선별 승차·하차 이용량")

    fig, ax = plt.subplots(figsize=(12, 6))

    line_usage.plot(
        kind="bar",
        ax=ax,
        color=["steelblue", "orange"]
    )

    ax.set_title(
        "서울 지하철 호선별 승차·하차 이용량"
    )

    ax.set_xlabel("호선")
    ax.set_ylabel("승하차 인원 (명)")
    ax.tick_params(axis="x", rotation=0)

    ax.legend(title="구분")

    st.pyplot(fig)


    st.subheader("호선별 이용량 데이터")

    st.dataframe(
        line_total.rename("총 이용량"),
        use_container_width=True
    )


# ============================================================
# 12. 역별·시간대별 패턴
# ============================================================

elif menu == "🔥 역별·시간대별 패턴":

    st.header("🔥 역별·시간대별 이용 패턴")

    st.caption(
        "일별통행통계 1~5월 기준"
    )


    # --------------------------------------------------------
    # 역 선택
    # --------------------------------------------------------

    selected_station = st.selectbox(
        "분석할 역을 선택하세요.",
        station_total.index
    )


    selected_station_data = station_hourly.loc[
        selected_station
    ]


    # --------------------------------------------------------
    # 선택 역의 가장 많은 시간대
    # --------------------------------------------------------

    station_max_hour = selected_station_data.idxmax()
    station_max_value = selected_station_data.max()


    col1, col2 = st.columns(2)

    col1.metric(
        "선택한 역",
        selected_station
    )

    col2.metric(
        "가장 이용량이 많은 시간대",
        station_max_hour
    )


    # --------------------------------------------------------
    # 선택 역 시간대 그래프
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(14, 6))

    sns.lineplot(
        x=selected_station_data.index,
        y=selected_station_data.values,
        marker="o",
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        f"{selected_station} 시간대별 이용 패턴"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수 (명)")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3)

    st.pyplot(fig)


    st.divider()


    # --------------------------------------------------------
    # 상위 20개 역 히트맵
    # --------------------------------------------------------

    st.subheader(
        "🔥 주요 역별·시간대별 이용 패턴"
    )

    top20_stations = station_total.head(20).index

    heatmap_data = station_hourly.loc[
        top20_stations,
        hour_cols
    ]


    # 역별 시간대 이용 비중
    heatmap_ratio = heatmap_data.div(
        heatmap_data.sum(axis=1),
        axis=0
    )


    fig, ax = plt.subplots(
        figsize=(16, 10)
    )

    sns.heatmap(
        heatmap_ratio,
        cmap="YlOrRd",
        linewidths=0.3,
        ax=ax,
        cbar_kws={
            "label": "시간대별 이용 비중"
        }
    )

    ax.set_title(
        "서울 지하철 주요 역별·시간대별 이용 패턴"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("역명")

    ax.tick_params(
        axis="x",
        rotation=45
    )

    st.pyplot(fig)


    st.info(
        "히트맵은 역별 전체 이용량이 아니라 "
        "각 역에서 시간대별 이용량이 차지하는 비중을 나타냅니다. "
        "따라서 역마다 이용객이 어느 시간대에 집중되는지 비교할 수 있습니다."
    )


# ============================================================
# 13. 월별 이용량
# ============================================================

elif menu == "📅 월별 이용량":

    st.header("📅 월별 이용량 분석")

    st.caption(
        "월별 승하차인원 데이터의 전체 제공 기간 기준"
    )


    # --------------------------------------------------------
    # 최대 / 최소 월
    # --------------------------------------------------------

    max_month = monthly_usage.idxmax()
    min_month = monthly_usage.idxmin()


    col1, col2 = st.columns(2)

    col1.metric(
        "이용량이 가장 많은 월",
        max_month.strftime("%Y-%m")
    )

    col2.metric(
        "이용량이 가장 적은 월",
        min_month.strftime("%Y-%m")
    )


    # --------------------------------------------------------
    # 월별 그래프
    # --------------------------------------------------------

    fig, ax = plt.subplots(figsize=(12, 6))

    sns.lineplot(
        x=monthly_usage.index,
        y=monthly_usage.values,
        marker="o",
        color="steelblue",
        ax=ax
    )

    ax.set_title(
        "서울 지하철 월별 이용량"
    )

    ax.set_xlabel("월")
    ax.set_ylabel("승하차 인원 (명)")
    ax.grid(alpha=0.3)

    st.pyplot(fig)


    # --------------------------------------------------------
    # 월별 데이터
    # --------------------------------------------------------

    st.subheader("월별 이용량 데이터")

    monthly_df = pd.DataFrame({
        "월": monthly_usage.index.strftime("%Y-%m"),
        "승하차 인원": monthly_usage.values
    })

    st.dataframe(
        monthly_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 14. 하단 정보
# ============================================================

st.sidebar.divider()

st.sidebar.info(
    """
    **데이터 출처**

    서울교통공사 공공데이터

    • 서울교통공사 일별통행통계
    • 서울교통공사 월별 승하차인원

    ※ 일별통행통계는 1~5월 자료를 활용합니다.
    """
)
