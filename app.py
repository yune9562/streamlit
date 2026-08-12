import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================
# 1. Streamlit 기본 설정
# ============================================================

st.set_page_config(
    page_title="서울 지하철 이용 패턴 분석",
    page_icon="🚇",
    layout="wide"
)

# ============================================================
# 2. 한글 폰트
# ============================================================

try:
    import koreanize_matplotlib
except ImportError:
    pass

plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 3. 파일 경로
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DAILY_FILE = (
    BASE_DIR /
    "서울교통공사_일별통행통계_20251231.csv"
)

MONTHLY_FILE = (
    
    BASE_DIR /
    "서울교통공사_월별 승하차인원_20251231.csv"
)


# ============================================================
# 4. CSV 불러오기
# ============================================================

@st.cache_data
def load_data():

    # 파일 존재 여부 확인
    if not DAILY_FILE.exists():
        st.error(
            "❌ 일별통행통계 CSV 파일을 찾을 수 없습니다."
        )
        st.code(str(DAILY_FILE))
        st.stop()

    if not MONTHLY_FILE.exists():
        st.error(
            "❌ 월별 승하차인원 CSV 파일을 찾을 수 없습니다."
        )
        st.code(str(MONTHLY_FILE))
        st.stop()

    # 일별 데이터
    try:
        daily = pd.read_csv(
            DAILY_FILE,
            encoding="cp949"
        )
    except UnicodeDecodeError:
        daily = pd.read_csv(
            DAILY_FILE,
            encoding="euc-kr"
        )

    # 월별 데이터
    try:
        monthly = pd.read_csv(
            MONTHLY_FILE,
            encoding="cp949"
        )
    except UnicodeDecodeError:
        monthly = pd.read_csv(
            MONTHLY_FILE,
            encoding="euc-kr"
        )

    return daily, monthly


daily, monthly = load_data()


# ============================================================
# 5. 시간대 컬럼
# ============================================================

hour_cols = [
    "04시", "05시", "06시", "07시",
    "08시", "09시", "10시", "11시",
    "12시", "13시", "14시", "15시",
    "16시", "17시", "18시", "19시",
    "20시", "21시", "22시", "23시",
    "00시", "01시", "02시", "03시"
]

commute_cols = [
    "07시",
    "08시",
    "09시",
    "17시",
    "18시",
    "19시"
]


# ============================================================
# 6. 컬럼 확인
# ============================================================

missing_hour_cols = [
    col for col in hour_cols
    if col not in daily.columns
]

if missing_hour_cols:

    st.error(
        "일별 데이터에서 다음 시간대 컬럼을 찾을 수 없습니다."
    )

    st.write(missing_hour_cols)

    st.write("현재 CSV의 컬럼:")
    st.write(daily.columns.tolist())

    st.stop()


# ============================================================
# 7. 날짜 컬럼 처리
# ============================================================

# 실제 데이터에 따라 업무일자 또는 수송일자 사용

if "업무일자" in daily.columns:

    daily_date_col = "업무일자"

elif "수송일자" in daily.columns:

    daily_date_col = "수송일자"

else:

    st.error(
        "일별 데이터에서 날짜 컬럼을 찾을 수 없습니다."
    )

    st.write(daily.columns.tolist())

    st.stop()


daily[daily_date_col] = pd.to_datetime(
    daily[daily_date_col],
    errors="coerce"
)


# ============================================================
# 8. 월별 날짜 처리
# ============================================================

if "수송연월" in monthly.columns:

    monthly_date_col = "수송연월"

else:

    st.error(
        "월별 데이터에서 '수송연월' 컬럼을 찾을 수 없습니다."
    )

    st.write(monthly.columns.tolist())

    st.stop()


monthly[monthly_date_col] = pd.to_datetime(
    monthly[monthly_date_col],
    errors="coerce"
)


# ============================================================
# 9. 숫자형 변환
# ============================================================

for col in hour_cols:

    daily[col] = pd.to_numeric(
        daily[col],
        errors="coerce"
    ).fillna(0)


monthly["승하차인원수"] = pd.to_numeric(
    monthly["승하차인원수"],
    errors="coerce"
).fillna(0)


# ============================================================
# 10. 일일 이용량
# ============================================================

daily["일일이용량"] = (
    daily[hour_cols].sum(axis=1)
)


# ============================================================
# 11. 분석 데이터 생성
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

hourly_usage = (
    daily[hour_cols]
    .sum()
)


# ------------------------------------------------------------
# 호선별 이용량
# ------------------------------------------------------------

line_usage = (
    daily
    .groupby(
        ["호선", "승하차구분"]
    )["일일이용량"]
    .sum()
    .unstack()
)

line_total = (
    line_usage
    .sum(axis=1)
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 역별 시간대별 이용량
# ------------------------------------------------------------

station_hourly = (
    daily
    .groupby("역명")[hour_cols]
    .sum()
)

station_total = (
    station_hourly
    .sum(axis=1)
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 출퇴근 이용량
# ------------------------------------------------------------

commute_usage = (
    daily
    .groupby("역명")[commute_cols]
    .sum()
    .sum(axis=1)
    .sort_values(ascending=False)
)


# ------------------------------------------------------------
# 월별 이용량
# ------------------------------------------------------------

monthly_usage = (
    monthly
    .groupby(monthly_date_col)["승하차인원수"]
    .sum()
    .sort_index()
)


# ============================================================
# 12. 사이드바
# ============================================================

st.sidebar.title("🚇 서울 지하철 분석")

menu = st.sidebar.radio(
    "분석 메뉴",
    [
        "종합 대시보드",
        "역별 이용량",
        "시간대별 이용량",
        "호선별 이용량",
        "역별·시간대별 패턴",
        "출퇴근 이용량",
        "월별 이용량",
        "데이터 확인"
    ]
)




# ============================================================
# 일별통계: 2025년 01월 ~ 05월
# ============================================================

daily_start = pd.Timestamp("2025-01-01")
daily_end = pd.Timestamp("2025-05-31")

daily = daily[
    (daily[daily_date_col] >= daily_start) &
    (daily[daily_date_col] <= daily_end)
].copy()


# ============================================================
# 월별통계: 2025년 01월 ~ 12월
# ============================================================

monthly_start = pd.Timestamp("2025-01-01")
monthly_end = pd.Timestamp("2025-12-31")

monthly = monthly[
    (monthly[monthly_date_col] >= monthly_start) &
    (monthly[monthly_date_col] <= monthly_end)
].copy()


# ============================================================
# 사이드바 분석 기간 표시
# ============================================================

st.sidebar.markdown("---")

st.sidebar.write("### 📅 분석 기간")

st.sidebar.write(
    f"일별통계: {daily_start:%Y-%m-%d} ~ "
    f"{daily_end:%Y-%m-%d}"
)

st.sidebar.write(
    f"월별통계: {monthly_start:%Y-%m} ~ "
    f"{monthly_end:%Y-%m}"
)



# ============================================================
# 13. 종합 대시보드
# ============================================================

if menu == "종합 대시보드":

    st.title("🚇 서울 지하철 이용 패턴 분석")

    st.caption(
        "서울교통공사 일별통행통계 및 월별 승하차인원 데이터"
    )

    # KPI

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "🚉 이용량 1위 역",
        station_total.idxmax()
    )

    col2.metric(
        "🕐 최다 이용 시간",
        hourly_usage.idxmax()
    )

    col3.metric(
        "🚇 이용량 1위 호선",
        str(line_total.idxmax())
    )

    col4.metric(
        "📅 이용량 최다 월",
        monthly_usage.idxmax().strftime("%Y-%m")
    )

    st.markdown("---")

    # --------------------------------------------------------
    # TOP 10 역
    # --------------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        st.subheader("🚉 이용량 TOP 10 역")

        top10 = station_total.head(10)

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        sns.barplot(
            x=top10.values,
            y=top10.index,
            color="steelblue",
            ax=ax
        )

        ax.set_xlabel("이용량")
        ax.set_ylabel("역명")
        ax.set_title("이용량 TOP 10")

        st.pyplot(fig)

        plt.close(fig)

    # --------------------------------------------------------
    # 시간대
    # --------------------------------------------------------

    with col2:

        st.subheader("🕐 시간대별 이용량")

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        ax.plot(
            hourly_usage.index,
            hourly_usage.values,
            marker="o",
            color="steelblue"
        )

        ax.set_xlabel("시간대")
        ax.set_ylabel("이용량")
        ax.tick_params(
            axis="x",
            rotation=45
        )

        ax.grid(alpha=0.3)

        st.pyplot(fig)

        plt.close(fig)


# ============================================================
# 14. 역별 이용량
# ============================================================

elif menu == "역별 이용량":

    st.title("🚉 역별 이용량 분석")

    top_n = st.slider(
        "표시할 역 개수",
        5,
        30,
        10
    )

    top_stations = station_total.head(top_n)

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    sns.barplot(
        x=top_stations.values,
        y=top_stations.index,
        color="steelblue",
        ax=ax
    )

    ax.set_xlabel("이용객 수")
    ax.set_ylabel("역명")

    ax.set_title(
        f"서울 지하철 이용량 TOP {top_n}"
    )

    st.pyplot(fig)

    plt.close(fig)

    st.subheader("상세 데이터")

    result = pd.DataFrame({
        "역명": top_stations.index,
        "이용량": top_stations.values
    })

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 15. 시간대별 이용량
# ============================================================

elif menu == "시간대별 이용량":

    st.title("🕐 시간대별 이용량 분석")

    max_hour = hourly_usage.idxmax()
    max_value = hourly_usage.max()

    col1, col2 = st.columns(2)

    col1.metric(
        "가장 이용객이 많은 시간",
        max_hour
    )

    col2.metric(
        "해당 시간 이용량",
        f"{max_value:,.0f}명"
    )

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    ax.plot(
        hourly_usage.index,
        hourly_usage.values,
        marker="o",
        linewidth=2,
        color="steelblue"
    )

    ax.fill_between(
        range(len(hourly_usage)),
        hourly_usage.values,
        alpha=0.15,
        color="steelblue"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수")

    ax.set_title(
        "서울 지하철 시간대별 이용량"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(alpha=0.3)

    st.pyplot(fig)

    plt.close(fig)

    st.subheader("시간대별 데이터")

    hour_result = pd.DataFrame({
        "시간대": hourly_usage.index,
        "이용량": hourly_usage.values
    })

    st.dataframe(
        hour_result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 16. 호선별 이용량
# ============================================================

elif menu == "호선별 이용량":

    st.title("🚇 호선별 이용량 분석")

    line_usage_display = (
        line_usage / 100_000_000
    )

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    line_usage_display.plot(
        kind="bar",
        ax=ax,
        color=[
            "steelblue",
            "orange"
        ]
    )

    ax.set_xlabel("호선")
    ax.set_ylabel("이용량 (억 명)")

    ax.set_title(
        "서울 지하철 호선별 승차·하차 이용량"
    )

    ax.tick_params(
        axis="x",
        rotation=0
    )

    ax.grid(
        axis="y",
        alpha=0.3
    )

    st.pyplot(fig)

    plt.close(fig)

    col1, col2 = st.columns(2)

    col1.metric(
        "이용량이 가장 많은 호선",
        str(line_total.idxmax())
    )

    col2.metric(
        "이용량이 가장 적은 호선",
        str(line_total.idxmin())
    )

    st.subheader("호선별 총 이용량")

    line_result = (
        line_total
        .reset_index()
    )

    line_result.columns = [
        "호선",
        "총 이용량"
    ]

    st.dataframe(
        line_result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 17. 역별·시간대별 패턴
# ============================================================

elif menu == "역별·시간대별 패턴":

    st.title("📈 역별·시간대별 이용 패턴")

    top_n = st.slider(
        "비교할 역 개수",
        3,
        10,
        5
    )

    top_stations = (
        station_total
        .head(top_n)
        .index
    )

    fig, ax = plt.subplots(
        figsize=(14, 7)
    )

    for station in top_stations:

        ax.plot(
            hour_cols,
            station_hourly.loc[station],
            marker="o",
            label=station
        )

    ax.set_title(
        "주요 역의 시간대별 이용 패턴"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수")

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(alpha=0.3)
    ax.legend()

    st.pyplot(fig)

    plt.close(fig)

    st.markdown("---")

    selected_station = st.selectbox(
        "상세 확인할 역",
        station_total.head(50).index
    )

    station_data = (
        station_hourly.loc[selected_station]
    )

    fig, ax = plt.subplots(
        figsize=(14, 5)
    )

    ax.plot(
        station_data.index,
        station_data.values,
        marker="o",
        color="steelblue"
    )

    ax.set_title(
        f"{selected_station} 시간대별 이용량"
    )

    ax.set_xlabel("시간대")
    ax.set_ylabel("이용객 수")

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(alpha=0.3)

    st.pyplot(fig)

    plt.close(fig)


# ============================================================
# 18. 출퇴근 이용량
# ============================================================

elif menu == "출퇴근 이용량":

    st.title("💼 출퇴근 시간대 이용량")

    st.info(
        "출근: 07시 ~ 09시 / "
        "퇴근: 17시 ~ 19시"
    )

    top10 = commute_usage.head(10)

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    sns.barplot(
        x=top10.values,
        y=top10.index,
        color="steelblue",
        ax=ax
    )

    ax.set_xlabel(
        "출퇴근 시간대 이용객 수"
    )

    ax.set_ylabel("역명")

    ax.set_title(
        "출퇴근 시간대 이용량 TOP 10"
    )

    st.pyplot(fig)

    plt.close(fig)

    result = pd.DataFrame({
        "역명": top10.index,
        "출퇴근 이용량": top10.values
    })

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 19. 월별 이용량
# ============================================================

elif menu == "월별 이용량":

    st.title("📅 월별 이용량 변화")

    max_month = monthly_usage.idxmax()
    min_month = monthly_usage.idxmin()

    col1, col2 = st.columns(2)

    col1.metric(
        "이용량이 가장 많은 달",
        max_month.strftime("%Y-%m"),
        f"{monthly_usage.max():,.0f}명"
    )

    col2.metric(
        "이용량이 가장 적은 달",
        min_month.strftime("%Y-%m"),
        f"{monthly_usage.min():,.0f}명"
    )

    fig, ax = plt.subplots(
        figsize=(14, 6)
    )

    ax.plot(
        monthly_usage.index,
        monthly_usage.values,
        marker="o",
        linewidth=2,
        color="steelblue"
    )

    ax.set_title(
        "서울 지하철 월별 이용량"
    )

    ax.set_xlabel("월")
    ax.set_ylabel("승하차 인원")

    ax.grid(alpha=0.3)

    st.pyplot(fig)

    plt.close(fig)

    st.subheader("월별 상세 데이터")

    monthly_result = (
        monthly_usage
        .reset_index()
    )

    monthly_result.columns = [
        "월",
        "승하차 인원"
    ]

    monthly_result["월"] = (
        monthly_result["월"]
        .dt.strftime("%Y-%m")
    )

    st.dataframe(
        monthly_result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 20. 데이터 확인
# ============================================================

elif menu == "데이터 확인":

    st.title("📋 데이터 확인")

    tab1, tab2 = st.tabs([
        "일별통행통계",
        "월별 승하차인원"
    ])

    # --------------------------------------------------------
    # 일별 데이터
    # --------------------------------------------------------

    with tab1:

        st.write(
            f"행 수: {daily.shape[0]:,}"
        )

        st.write(
            f"열 수: {daily.shape[1]:,}"
        )

        st.write("### 컬럼")

        st.write(
            daily.columns.tolist()
        )

        st.write("### 데이터 미리보기")

        st.dataframe(
            daily.head(100),
            use_container_width=True
        )

        st.write("### 결측치")

        missing = (
            daily.isnull()
            .sum()
            .sort_values(ascending=False)
        )

        st.dataframe(
            missing[missing > 0]
            .to_frame("결측치 수"),
            use_container_width=True
        )

    # --------------------------------------------------------
    # 월별 데이터
    # --------------------------------------------------------

    with tab2:

        st.write(
            f"행 수: {monthly.shape[0]:,}"
        )

        st.write(
            f"열 수: {monthly.shape[1]:,}"
        )

        st.write("### 컬럼")

        st.write(
            monthly.columns.tolist()
        )

        st.write("### 데이터 미리보기")

        st.dataframe(
            monthly.head(100),
            use_container_width=True
        )

        st.write("### 결측치")

        missing = (
            monthly.isnull()
            .sum()
            .sort_values(ascending=False)
        )

        st.dataframe(
            missing[missing > 0]
            .to_frame("결측치 수"),
            use_container_width=True
        )


# ============================================================
# 21. 하단
# ============================================================

st.sidebar.markdown("---")

st.sidebar.caption(
    "서울교통공사 데이터 기반"
)

st.sidebar.caption(
    "🚇 Seoul Subway Analysis Dashboard"
)

