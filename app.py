import streamlit as st
import pandas as pd
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
    koreanize_matplotlib = None

plt.rcParams["axes.unicode_minus"] = False


# ============================================================
# 3. 파일 경로 및 인코딩
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

CSV_ENCODING = "cp949"


# ============================================================
# 4. 분석 기간
# ============================================================

DAILY_START = pd.Timestamp("2025-01-01")
DAILY_END = pd.Timestamp("2025-12-31")

MONTHLY_START = pd.Timestamp("2025-01-01")
MONTHLY_END = pd.Timestamp("2025-12-31")


# ============================================================
# 5. 시간대 컬럼
# ============================================================

HOUR_COLS = [
    "04시", "05시", "06시", "07시",
    "08시", "09시", "10시", "11시",
    "12시", "13시", "14시", "15시",
    "16시", "17시", "18시", "19시",
    "20시", "21시", "22시", "23시",
    "00시", "01시", "02시", "03시"
]

COMMUTE_COLS = [
    "07시",
    "08시",
    "09시",
    "17시",
    "18시",
    "19시"
]


# ============================================================
# 6. CSV 헤더 / 인코딩 확인
# ============================================================

@st.cache_data(
    show_spinner=False
)
def get_csv_encoding(file_path, file_mtime):

    try:

        pd.read_csv(
            file_path,
            encoding="cp949",
            nrows=0
        )

        return "cp949"

    except UnicodeDecodeError:

        pd.read_csv(
            file_path,
            encoding="euc-kr",
            nrows=0
        )

        return "euc-kr"


@st.cache_data(
    show_spinner=False
)
def read_csv_header(file_path, file_mtime):

    encoding = get_csv_encoding(
        file_path,
        file_mtime
    )

    header = pd.read_csv(
        file_path,
        encoding=encoding,
        nrows=0
    )

    return header, encoding


# ============================================================
# 7. 일별 데이터 로딩
# ============================================================

def _load_daily_data(
    daily_file,
    daily_mtime
):

    if not daily_file.exists():

        raise FileNotFoundError(
            f"일별 CSV 파일을 찾을 수 없습니다.\n"
            f"{daily_file}"
        )

    header, encoding = read_csv_header(
        str(daily_file),
        daily_mtime
    )

    available_columns = set(
        header.columns
    )

    # --------------------------------------------------------
    # 날짜 컬럼 확인
    # --------------------------------------------------------

    if "업무일자" in available_columns:

        date_col = "업무일자"

    elif "수송일자" in available_columns:

        date_col = "수송일자"

    else:

        raise ValueError(
            "일별 데이터에서 "
            "'업무일자' 또는 '수송일자' "
            "컬럼을 찾을 수 없습니다."
        )

    # --------------------------------------------------------
    # 필요한 컬럼만 선택
    # --------------------------------------------------------

    required_columns = [
        date_col,
        "역명",
        "호선",
        "승하차구분"
    ] + HOUR_COLS

    usecols = [
        col
        for col in required_columns
        if col in available_columns
    ]

    # --------------------------------------------------------
    # 필수 컬럼 확인
    # --------------------------------------------------------

    required_basic = [
        date_col,
        "역명",
        "호선",
        "승하차구분"
    ]

    missing_basic = [
        col
        for col in required_basic
        if col not in available_columns
    ]

    if missing_basic:

        raise ValueError(
            "일별 CSV에 다음 필수 컬럼이 없습니다:\n"
            + ", ".join(missing_basic)
        )

    # --------------------------------------------------------
    # 시간대 컬럼 확인
    # --------------------------------------------------------

    missing_hours = [
        col
        for col in HOUR_COLS
        if col not in available_columns
    ]

    if missing_hours:

        raise ValueError(
            "다음 시간대 컬럼이 CSV에 없습니다:\n"
            + ", ".join(missing_hours)
        )

    # --------------------------------------------------------
    # 필요한 컬럼만 CSV에서 읽기
    # --------------------------------------------------------

    daily = pd.read_csv(
        daily_file,
        encoding=encoding,
        usecols=usecols,
        low_memory=False
    )

    # --------------------------------------------------------
    # 날짜 변환
    # --------------------------------------------------------

    daily[date_col] = pd.to_datetime(
        daily[date_col],
        errors="coerce"
    )

    # --------------------------------------------------------
    # 2025년 필터
    # --------------------------------------------------------

    daily = daily.loc[
        (
            daily[date_col] >= DAILY_START
        )
        &
        (
            daily[date_col] <= DAILY_END
        )
    ].copy()

    # --------------------------------------------------------
    # 문자열 컬럼 category
    # --------------------------------------------------------

    for col in [
        "역명",
        "호선",
        "승하차구분"
    ]:

        if col in daily.columns:

            daily[col] = (
                daily[col]
                .astype("category")
            )

    # --------------------------------------------------------
    # 시간대 숫자형 변환
    # --------------------------------------------------------

    for col in HOUR_COLS:

        daily[col] = (
            pd.to_numeric(
                daily[col],
                errors="coerce"
            )
            .fillna(0)
            .astype("float32")
        )

    return daily, date_col


# ============================================================
# 8. 월별 데이터 로딩
# ============================================================

def _load_monthly_data(
    monthly_file,
    monthly_mtime
):

    if not monthly_file.exists():

        raise FileNotFoundError(
            f"월별 CSV 파일을 찾을 수 없습니다.\n"
            f"{monthly_file}"
        )

    header, encoding = read_csv_header(
        str(monthly_file),
        monthly_mtime
    )

    available_columns = set(
        header.columns
    )

    if "수송연월" not in available_columns:

        raise ValueError(
            "월별 데이터에서 "
            "'수송연월' 컬럼을 찾을 수 없습니다."
        )

    if "승하차인원수" not in available_columns:

        raise ValueError(
            "월별 데이터에서 "
            "'승하차인원수' 컬럼을 찾을 수 없습니다."
        )

    # --------------------------------------------------------
    # 필요한 컬럼만 읽기
    # --------------------------------------------------------

    monthly = pd.read_csv(
        monthly_file,
        encoding=encoding,
        usecols=[
            "수송연월",
            "승하차인원수"
        ],
        low_memory=False
    )

    # --------------------------------------------------------
    # 날짜 처리
    # --------------------------------------------------------

    raw_date = (
        monthly["수송연월"]
        .astype(str)
        .str.strip()
    )

    monthly_date = pd.to_datetime(
        raw_date,
        errors="coerce"
    )

    # --------------------------------------------------------
    # YYYYMM 형태 처리
    # --------------------------------------------------------

    yyyymm_mask = (
        raw_date.str.len().eq(6)
        &
        raw_date.str.match(
            r"^\d{6}$"
        )
    )

    if yyyymm_mask.any():

        monthly_date.loc[
            yyyymm_mask
        ] = pd.to_datetime(
            raw_date.loc[yyyymm_mask],
            format="%Y%m",
            errors="coerce"
        )

    monthly["수송연월"] = monthly_date

    # --------------------------------------------------------
    # 분석기간 필터링
    # --------------------------------------------------------

    monthly = monthly.loc[
        (
            monthly["수송연월"]
            >= MONTHLY_START
        )
        &
        (
            monthly["수송연월"]
            <= MONTHLY_END
        )
    ].copy()

    # --------------------------------------------------------
    # 숫자형 변환
    # --------------------------------------------------------

    monthly["승하차인원수"] = (
        pd.to_numeric(
            monthly["승하차인원수"],
            errors="coerce"
        )
        .fillna(0)
        .astype("float32")
    )

    return monthly


# ============================================================
# 9. 전체 데이터 로딩 + 분석 계산
#
# 핵심 최적화
# ------------------------------------------------------------
# Streamlit은 위젯을 클릭할 때마다 스크립트를 다시 실행한다.
#
# 기존 코드:
#
# CSV 읽기
# ↓
# groupby
# ↓
# sum
# ↓
# sort
# ↓
# 화면 출력
#
# 이 모든 작업을 매번 반복.
#
# 현재 코드:
#
# 파일 수정시간 확인
# ↓
# 캐시된 결과 사용
#
# 파일이 실제로 변경된 경우에만 다시 계산.
# ============================================================

@st.cache_data(
    show_spinner="🚇 데이터를 분석하는 중..."
)
def load_and_prepare_all_data(
    daily_file,
    daily_mtime,
    monthly_file,
    monthly_mtime
):

    # --------------------------------------------------------
    # CSV 로딩
    # --------------------------------------------------------

    daily, daily_date_col = _load_daily_data(
        Path(daily_file),
        daily_mtime
    )

    monthly = _load_monthly_data(
        Path(monthly_file),
        monthly_mtime
    )

    # --------------------------------------------------------
    # 데이터 존재 여부
    # --------------------------------------------------------

    if daily.empty:

        raise ValueError(
            "2025년 1월~12월에 해당하는 "
            "일별 데이터가 없습니다."
        )

    if monthly.empty:

        raise ValueError(
            "2025년 월별 데이터가 없습니다."
        )

    # ========================================================
    # 10. 일일 이용량 계산
    # ========================================================

    daily["일일이용량"] = (
        daily[HOUR_COLS]
        .sum(axis=1)
        .astype("float32")
    )

    # ========================================================
    # 11. 역별·시간대별 이용량
    # ========================================================

    station_hourly = (
        daily
        .groupby(
            "역명",
            observed=True
        )[HOUR_COLS]
        .sum()
        .astype("float32")
    )

    # ========================================================
    # 12. 역별 총 이용량
    # ========================================================

    station_total = (
        station_hourly
        .sum(axis=1)
        .sort_values(
            ascending=False
        )
    )

    # ========================================================
    # 13. 시간대별 이용량
    # ========================================================

    hourly_usage = (
        daily[HOUR_COLS]
        .sum()
        .astype("float32")
    )

    # ========================================================
    # 14. 호선별 이용량
    # ========================================================

    line_usage = (
        daily
        .groupby(
            [
                "호선",
                "승하차구분"
            ],
            observed=True
        )["일일이용량"]
        .sum()
        .unstack(
            fill_value=0
        )
    )

    line_total = (
        line_usage
        .sum(axis=1)
        .sort_values(
            ascending=False
        )
    )

    # ========================================================
    # 15. 출퇴근 이용량
    # ========================================================

    commute_usage = (
        daily
        .groupby(
            "역명",
            observed=True
        )[COMMUTE_COLS]
        .sum()
        .sum(axis=1)
        .sort_values(
            ascending=False
        )
    )

    # ========================================================
    # 16. 월별 이용량
    # ========================================================

    monthly_usage = (
        monthly
        .groupby(
            "수송연월"
        )["승하차인원수"]
        .sum()
        .sort_index()
    )

    return (
        daily,
        daily_date_col,
        monthly,
        station_hourly,
        station_total,
        hourly_usage,
        line_usage,
        line_total,
        commute_usage,
        monthly_usage
    )


# ============================================================
# 10. 데이터 로딩 실행
# ============================================================

try:

    if not DAILY_FILE.exists():

        st.error(
            "❌ 일별 CSV 파일을 찾을 수 없습니다."
        )

        st.code(
            str(DAILY_FILE)
        )

        st.stop()

    if not MONTHLY_FILE.exists():

        st.error(
            "❌ 월별 CSV 파일을 찾을 수 없습니다."
        )

        st.code(
            str(MONTHLY_FILE)
        )

        st.stop()

    # --------------------------------------------------------
    # 파일 수정시간
    #
    # 파일이 변경됐을 때만 cache가 무효화됨
    # --------------------------------------------------------

    daily_mtime = DAILY_FILE.stat().st_mtime_ns
    monthly_mtime = MONTHLY_FILE.stat().st_mtime_ns

    (
        daily,
        daily_date_col,
        monthly,
        station_hourly,
        station_total,
        hourly_usage,
        line_usage,
        line_total,
        commute_usage,
        monthly_usage
    ) = load_and_prepare_all_data(
        str(DAILY_FILE),
        daily_mtime,
        str(MONTHLY_FILE),
        monthly_mtime
    )

except Exception as e:

    st.error(
        "❌ 데이터 로딩 중 오류가 발생했습니다."
    )

    st.exception(e)

    st.stop()


# ============================================================
# 11. 사이드바
# ============================================================

st.sidebar.title(
    "🚇 서울 지하철 분석"
)

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

st.sidebar.markdown("---")

st.sidebar.write(
    "### 📅 분석 기간"
)

st.sidebar.write(
    f"일별통계: "
    f"{DAILY_START:%Y-%m-%d} ~ "
    f"{DAILY_END:%Y-%m-%d}"
)

st.sidebar.write(
    f"월별통계: "
    f"{MONTHLY_START:%Y-%m} ~ "
    f"{MONTHLY_END:%Y-%m}"
)

st.sidebar.markdown("---")

st.sidebar.caption(
    f"일별 데이터: {len(daily):,}행"
)

st.sidebar.caption(
    f"월별 데이터: {len(monthly):,}행"
)

st.sidebar.caption(
    "서울교통공사 데이터 기반"
)

st.sidebar.caption(
    "🚇 Seoul Subway Analysis Dashboard"
)


# ============================================================
# 12. 종합 대시보드
# ============================================================

if menu == "종합 대시보드":

    st.title(
        "🚇 서울 지하철 이용 패턴 분석"
    )

    st.caption(
        "서울교통공사 일별통행통계 및 "
        "월별 승하차인원 데이터"
    )

    st.markdown("---")

    # ========================================================
    # KPI
    # ========================================================

    col1, col2, col3, col4 = st.columns(4)

    # --------------------------------------------------------
    # 1위 역
    # --------------------------------------------------------

    top_station = (
        station_total.idxmax()
    )

    top_station_value = (
        station_total.max()
    )

    col1.metric(
        "🚉 이용량 1위 역",
        str(top_station),
        f"{top_station_value:,.0f}명"
    )

    # --------------------------------------------------------
    # 최고 시간대
    # --------------------------------------------------------

    max_hour = (
        hourly_usage.idxmax()
    )

    max_hour_value = (
        hourly_usage.max()
    )

    col2.metric(
        "🕐 최다 이용 시간",
        str(max_hour),
        f"{max_hour_value:,.0f}명"
    )

    # --------------------------------------------------------
    # 1위 호선
    # --------------------------------------------------------

    top_line = (
        line_total.idxmax()
    )

    top_line_value = (
        line_total.max()
    )

    col3.metric(
        "🚇 이용량 1위 호선",
        str(top_line),
        f"{top_line_value:,.0f}명"
    )

    # --------------------------------------------------------
    # 최고 월
    # --------------------------------------------------------

    max_month = (
        monthly_usage.idxmax()
    )

    max_month_value = (
        monthly_usage.max()
    )

    col4.metric(
        "📅 이용량 최다 월",
        max_month.strftime("%Y-%m"),
        f"{max_month_value:,.0f}명"
    )

    # ========================================================
    # TOP 10 + 시간대
    # ========================================================

    st.markdown("---")

    col1, col2 = st.columns(
        [1, 1],
        gap="large"
    )

    # ========================================================
    # 왼쪽 : TOP 10 역
    # ========================================================

    with col1:

        st.subheader(
            "🚉 이용량 TOP 10 역"
        )

        top10 = (
            station_total
            .head(10)
            .sort_values(
                ascending=True
            )
        )

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        bars = ax.barh(
            top10.index.astype(str),
            top10.values,
            color="#4C78A8",
            height=0.65
        )

        chart_max = top10.max()

        for bar, value in zip(
            bars,
            top10.values
        ):

            ax.text(
                value + chart_max * 0.01,
                bar.get_y()
                + bar.get_height() / 2,
                f"{value:,.0f}",
                va="center",
                fontsize=9
            )

        ax.set_xlabel(
            "이용객 수"
        )

        ax.set_ylabel(
            "역명"
        )

        ax.set_title(
            "이용량 TOP 10",
            fontsize=13,
            fontweight="bold"
        )

        ax.grid(
            axis="x",
            alpha=0.25
        )

        ax.spines[
            "top"
        ].set_visible(False)

        ax.spines[
            "right"
        ].set_visible(False)

        ax.set_xlim(
            0,
            chart_max * 1.15
        )

        plt.tight_layout()

        st.pyplot(
            fig,
            clear_figure=True,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # TOP 10 표
        # ----------------------------------------------------

        st.write(
            "#### TOP 10 상세"
        )

        display_top10 = (
            station_total
            .head(10)
            .reset_index()
        )

        display_top10.columns = [
            "역명",
            "이용량"
        ]

        display_top10[
            "이용량"
        ] = (
            display_top10[
                "이용량"
            ]
            .map(
                lambda x:
                f"{x:,.0f}"
            )
        )

        st.dataframe(
            display_top10,
            use_container_width=True,
            hide_index=True,
            height=260
        )

    # ========================================================
    # 오른쪽 : 시간대별 이용량
    # ========================================================

    with col2:

        st.subheader(
            "🕐 시간대별 이용량"
        )

        fig, ax = plt.subplots(
            figsize=(8, 6)
        )

        x = range(
            len(hourly_usage)
        )

        ax.plot(
            x,
            hourly_usage.values,
            marker="o",
            markersize=5,
            linewidth=2.5,
            color="#F58518"
        )

        ax.fill_between(
            x,
            hourly_usage.values,
            alpha=0.12,
            color="#F58518"
        )

        max_index = (
            hourly_usage.values.argmax()
        )

        max_value = (
            hourly_usage.iloc[
                max_index
            ]
        )

        ax.scatter(
            max_index,
            max_value,
            color="#D62728",
            s=80,
            zorder=5
        )

        ax.annotate(
            (
                f"{hourly_usage.index[max_index]}\n"
                f"{max_value:,.0f}명"
            ),
            xy=(
                max_index,
                max_value
            ),
            xytext=(
                0,
                20
            ),
            textcoords="offset points",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color="#D62728"
        )

        ax.set_xticks(
            x
        )

        ax.set_xticklabels(
            hourly_usage.index,
            rotation=45
        )

        ax.set_xlabel(
            "시간대"
        )

        ax.set_ylabel(
            "이용객 수"
        )

        ax.set_title(
            "시간대별 이용량",
            fontsize=13,
            fontweight="bold"
        )

        ax.grid(
            axis="y",
            alpha=0.25
        )

        ax.spines[
            "top"
        ].set_visible(False)

        ax.spines[
            "right"
        ].set_visible(False)

        plt.tight_layout()

        st.pyplot(
            fig,
            clear_figure=True,
            use_container_width=True
        )

        plt.close(fig)

        # ----------------------------------------------------
        # 시간대 TOP 5
        # ----------------------------------------------------

        st.write(
            "#### 이용량이 많은 시간대"
        )

        top_hours = (
            hourly_usage
            .sort_values(
                ascending=False
            )
            .head(5)
            .reset_index()
        )

        top_hours.columns = [
            "시간대",
            "이용량"
        ]

        top_hours[
            "이용량"
        ] = (
            top_hours[
                "이용량"
            ]
            .map(
                lambda x:
                f"{x:,.0f}"
            )
        )

        st.dataframe(
            top_hours,
            use_container_width=True,
            hide_index=True,
            height=220
        )

    # ========================================================
    # 주요 분석 요약
    # ========================================================

    st.markdown("---")

    st.subheader(
        "📊 주요 분석 요약"
    )

    summary_col1, summary_col2, summary_col3 = (
        st.columns(3)
    )

    # --------------------------------------------------------
    # TOP 역
    # --------------------------------------------------------

    with summary_col1:

        st.markdown(
            f"""
**🚉 가장 많이 이용한 역**

### {top_station}

총 **{top_station_value:,.0f}명**
"""
        )

    # --------------------------------------------------------
    # 최고 시간
    # --------------------------------------------------------

    with summary_col2:

        st.markdown(
            f"""
**🕐 가장 붐비는 시간대**

### {max_hour}

총 **{max_hour_value:,.0f}명**
"""
        )

    # --------------------------------------------------------
    # 최고 월
    # --------------------------------------------------------

    with summary_col3:

        st.markdown(
            f"""
**📅 가장 많이 이용한 월**

### {max_month.strftime("%Y-%m")}

총 **{max_month_value:,.0f}명**
"""
        )

    # ========================================================
    # 분석 기간
    # ========================================================

    st.markdown("---")

    st.caption(
        f"📅 분석기간 | "
        f"일별 {DAILY_START:%Y-%m-%d} ~ "
        f"{DAILY_END:%Y-%m-%d} | "
        f"월별 {MONTHLY_START:%Y-%m} ~ "
        f"{MONTHLY_END:%Y-%m}"
    )


# ============================================================
# 13. 역별 이용량
# ============================================================

elif menu == "역별 이용량":

    st.title(
        "🚉 역별 이용량 분석"
    )

    top_n = st.slider(
        "표시할 역 개수",
        5,
        30,
        10
    )

    top_stations = (
        station_total
        .head(top_n)
        .sort_values(
            ascending=True
        )
    )

    fig, ax = plt.subplots(
        figsize=(12, 8)
    )

    bars = ax.barh(
        top_stations.index.astype(str),
        top_stations.values,
        color="#4C78A8"
    )

    chart_max = top_stations.max()

    for bar, value in zip(
        bars,
        top_stations.values
    ):

        ax.text(
            value + chart_max * 0.01,
            bar.get_y()
            + bar.get_height() / 2,
            f"{value:,.0f}",
            va="center",
            fontsize=9
        )

    ax.set_xlabel(
        "이용객 수"
    )

    ax.set_ylabel(
        "역명"
    )

    ax.set_title(
        f"서울 지하철 이용량 TOP {top_n}"
    )

    ax.grid(
        axis="x",
        alpha=0.25
    )

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False
    )

    ax.set_xlim(
        0,
        chart_max * 1.15
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)

    st.subheader(
        "상세 데이터"
    )

    result = (
        station_total
        .head(top_n)
        .reset_index()
    )

    result.columns = [
        "역명",
        "이용량"
    ]

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 14. 시간대별 이용량
# ============================================================

elif menu == "시간대별 이용량":

    st.title(
        "🕐 시간대별 이용량 분석"
    )

    max_hour = (
        hourly_usage.idxmax()
    )

    max_value = (
        hourly_usage.max()
    )

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

    x = range(
        len(hourly_usage)
    )

    ax.plot(
        x,
        hourly_usage.values,
        marker="o",
        linewidth=2,
        color="#4C78A8"
    )

    ax.fill_between(
        x,
        hourly_usage.values,
        alpha=0.15,
        color="#4C78A8"
    )

    ax.set_xticks(
        x
    )

    ax.set_xticklabels(
        hourly_usage.index,
        rotation=45
    )

    ax.set_xlabel(
        "시간대"
    )

    ax.set_ylabel(
        "이용객 수"
    )

    ax.set_title(
        "서울 지하철 시간대별 이용량"
    )

    ax.grid(
        alpha=0.3
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)

    st.subheader(
        "시간대별 데이터"
    )

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
# 15. 호선별 이용량
# ============================================================

elif menu == "호선별 이용량":

    st.title(
        "🚇 호선별 이용량 분석"
    )

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
            "#4C78A8",
            "#F58518"
        ]
    )

    ax.set_xlabel(
        "호선"
    )

    ax.set_ylabel(
        "이용량 (억 명)"
    )

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

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

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

    st.subheader(
        "호선별 총 이용량"
    )

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
# 16. 역별·시간대별 패턴
# ============================================================

elif menu == "역별·시간대별 패턴":

    st.title(
        "📈 역별·시간대별 이용 패턴"
    )

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

        if station in station_hourly.index:

            ax.plot(
                HOUR_COLS,
                station_hourly.loc[
                    station
                ].values,
                marker="o",
                label=str(station)
            )

    ax.set_title(
        "주요 역의 시간대별 이용 패턴"
    )

    ax.set_xlabel(
        "시간대"
    )

    ax.set_ylabel(
        "이용객 수"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(
        alpha=0.3
    )

    ax.legend()

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)

    st.markdown("---")

    selected_station = st.selectbox(
        "상세 확인할 역",
        station_total.head(50).index
    )

    station_data = (
        station_hourly
        .loc[selected_station]
    )

    fig, ax = plt.subplots(
        figsize=(14, 5)
    )

    ax.plot(
        HOUR_COLS,
        station_data.values,
        marker="o",
        color="#4C78A8"
    )

    ax.set_title(
        f"{selected_station} 시간대별 이용량"
    )

    ax.set_xlabel(
        "시간대"
    )

    ax.set_ylabel(
        "이용객 수"
    )

    ax.tick_params(
        axis="x",
        rotation=45
    )

    ax.grid(
        alpha=0.3
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)


# ============================================================
# 17. 출퇴근 이용량
# ============================================================

elif menu == "출퇴근 이용량":

    st.title(
        "💼 출퇴근 시간대 이용량"
    )

    st.info(
        "출근: 07시 ~ 09시 / "
        "퇴근: 17시 ~ 19시"
    )

    top10 = (
        commute_usage
        .head(10)
        .sort_values(
            ascending=True
        )
    )

    fig, ax = plt.subplots(
        figsize=(12, 7)
    )

    bars = ax.barh(
        top10.index.astype(str),
        top10.values,
        color="#4C78A8"
    )

    chart_max = top10.max()

    for bar, value in zip(
        bars,
        top10.values
    ):

        ax.text(
            value + chart_max * 0.01,
            bar.get_y()
            + bar.get_height() / 2,
            f"{value:,.0f}",
            va="center",
            fontsize=9
        )

    ax.set_xlabel(
        "출퇴근 시간대 이용객 수"
    )

    ax.set_ylabel(
        "역명"
    )

    ax.set_title(
        "출퇴근 시간대 이용량 TOP 10"
    )

    ax.grid(
        axis="x",
        alpha=0.3
    )

    ax.spines[
        "top"
    ].set_visible(False)

    ax.spines[
        "right"
    ].set_visible(False)

    ax.set_xlim(
        0,
        chart_max * 1.15
    )

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)

    result = (
        commute_usage
        .head(10)
        .reset_index()
    )

    result.columns = [
        "역명",
        "출퇴근 이용량"
    ]

    st.dataframe(
        result,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 18. 월별 이용량
# ============================================================

elif menu == "월별 이용량":

    st.title(
        "📅 월별 이용량 변화"
    )

    max_month = (
        monthly_usage.idxmax()
    )

    min_month = (
        monthly_usage.idxmin()
    )

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
        linewidth=2.5,
        color="#4C78A8"
    )

    ax.fill_between(
        monthly_usage.index,
        monthly_usage.values,
        alpha=0.12,
        color="#4C78A8"
    )

    ax.set_title(
        "서울 지하철 월별 이용량"
    )

    ax.set_xlabel(
        "월"
    )

    ax.set_ylabel(
        "승하차 인원"
    )

    ax.grid(
        alpha=0.3
    )

    fig.autofmt_xdate()

    plt.tight_layout()

    st.pyplot(
        fig,
        clear_figure=True,
        use_container_width=True
    )

    plt.close(fig)

    st.subheader(
        "월별 상세 데이터"
    )

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
# 19. 데이터 확인
# ============================================================

elif menu == "데이터 확인":

    st.title(
        "📋 데이터 확인"
    )

    tab1, tab2 = st.tabs([
        "일별통행통계",
        "월별 승하차인원"
    ])

    # ========================================================
    # 일별 데이터
    # ========================================================

    with tab1:

        col1, col2 = st.columns(2)

        col1.metric(
            "행 수",
            f"{daily.shape[0]:,}"
        )

        col2.metric(
            "열 수",
            f"{daily.shape[1]:,}"
        )

        st.write(
            "### 컬럼"
        )

        st.write(
            daily.columns.tolist()
        )

        st.write(
            "### 데이터 미리보기"
        )

        st.dataframe(
            daily.head(100),
            use_container_width=True,
            height=400
        )

        st.write(
            "### 결측치"
        )

        missing = (
            daily
            .isnull()
            .sum()
            .sort_values(
                ascending=False
            )
        )

        missing = missing[
            missing > 0
        ]

        if missing.empty:

            st.success(
                "결측치가 없습니다."
            )

        else:

            st.dataframe(
                missing.to_frame(
                    "결측치 수"
                ),
                use_container_width=True
            )

    # ========================================================
    # 월별 데이터
    # ========================================================

    with tab2:

        col1, col2 = st.columns(2)

        col1.metric(
            "행 수",
            f"{monthly.shape[0]:,}"
        )

        col2.metric(
            "열 수",
            f"{monthly.shape[1]:,}"
        )

        st.write(
            "### 컬럼"
        )

        st.write(
            monthly.columns.tolist()
        )

        st.write(
            "### 데이터 미리보기"
        )

        st.dataframe(
            monthly.head(100),
            use_container_width=True,
            height=400
        )

        st.write(
            "### 결측치"
        )

        missing = (
            monthly
            .isnull()
            .sum()
            .sort_values(
                ascending=False
            )
        )

        missing = missing[
            missing > 0
        ]

        if missing.empty:

            st.success(
                "결측치가 없습니다."
            )

        else:

            st.dataframe(
                missing.to_frame(
                    "결측치 수"
                ),
                use_container_width=True
            )
            