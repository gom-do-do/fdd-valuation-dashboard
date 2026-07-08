import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="M&A FDD & Valuation Prototype",
    page_icon=":briefcase:",
    layout="wide",
)

REQUIRED_COLUMNS = [
    "Year",
    "Revenue",
    "COGS",
    "SG&A",
    "One_off_Loss",
    "Owner_Expense",
    "Accounting_Adj",
    "AR",
    "Inventory",
    "AP",
    "Net_Debt",
]

ADJUSTMENT_COLUMNS = ["One_off_Loss", "Owner_Expense", "Accounting_Adj"]


@st.cache_data
def create_mock_financials() -> pd.DataFrame:
    """Create three-year mock IS/BS summary data using the upload schema."""
    return pd.DataFrame(
        [
            {
                "Year": "FY2023",
                "Revenue": 82_000,
                "COGS": 48_500,
                "SG&A": 19_200,
                "One_off_Loss": 1_800,
                "Owner_Expense": 700,
                "Accounting_Adj": -400,
                "AR": 11_200,
                "Inventory": 8_300,
                "AP": 7_600,
                "Net_Debt": 15_500,
            },
            {
                "Year": "FY2024",
                "Revenue": 92_500,
                "COGS": 53_200,
                "SG&A": 21_100,
                "One_off_Loss": 1_700,
                "Owner_Expense": 1_000,
                "Accounting_Adj": 600,
                "AR": 13_500,
                "Inventory": 9_700,
                "AP": 8_900,
                "Net_Debt": 13_200,
            },
            {
                "Year": "FY2025",
                "Revenue": 105_000,
                "COGS": 59_800,
                "SG&A": 23_600,
                "One_off_Loss": -900,
                "Owner_Expense": 1_400,
                "Accounting_Adj": 1_200,
                "AR": 19_000,
                "Inventory": 13_500,
                "AP": 10_200,
                "Net_Debt": 10_200,
            },
        ]
    )


def format_krw(value: float) -> str:
    return f"{value:,.0f} 백만원"


def format_multiple(value: float) -> str:
    return f"{value:.1f}x"


def year_sort_key(value: object) -> int:
    digits = "".join(char for char in str(value) if char.isdigit())
    return int(digits) if digits else 0


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    file_name = uploaded_file.name.lower()
    if file_name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    try:
        return pd.read_excel(uploaded_file)
    except ImportError as exc:
        raise ImportError(
            "엑셀 업로드를 사용하려면 openpyxl 설치가 필요합니다. "
            "현재 환경에서는 CSV 업로드를 사용하거나 `pip install openpyxl`을 실행해 주세요."
        ) from exc


def validate_uploaded_data(df: pd.DataFrame) -> list[str]:
    errors = []
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        errors.append(f"필수 컬럼 누락: {', '.join(missing_cols)}")

    if len(df) < 3:
        errors.append("3개년 이상 데이터가 필요합니다.")

    return errors


def prepare_financials(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df[REQUIRED_COLUMNS].copy()
    prepared["Year"] = prepared["Year"].astype(str)

    numeric_cols = [col for col in REQUIRED_COLUMNS if col != "Year"]
    for col in numeric_cols:
        prepared[col] = pd.to_numeric(prepared[col], errors="coerce")

    prepared = prepared.dropna(subset=numeric_cols)
    prepared = prepared.sort_values("Year", key=lambda col: col.map(year_sort_key))

    prepared["Gross Profit"] = prepared["Revenue"] - prepared["COGS"]
    prepared["Reported EBITDA"] = (
        prepared["Revenue"] - prepared["COGS"] - prepared["SG&A"]
    )
    prepared["QoE Adjustment"] = prepared[ADJUSTMENT_COLUMNS].sum(axis=1)
    prepared["Normalized EBITDA"] = (
        prepared["Reported EBITDA"] + prepared["QoE Adjustment"]
    )
    prepared["EBITDA Margin"] = prepared["Reported EBITDA"] / prepared["Revenue"]
    prepared["Normalized EBITDA Margin"] = (
        prepared["Normalized EBITDA"] / prepared["Revenue"]
    )
    prepared["Net Working Capital"] = (
        prepared["AR"] + prepared["Inventory"] - prepared["AP"]
    )
    prepared["DSO"] = prepared["AR"] / prepared["Revenue"] * 365
    prepared["DIO"] = prepared["Inventory"] / prepared["COGS"] * 365
    prepared["DPO"] = prepared["AP"] / prepared["COGS"] * 365
    prepared["Cash Conversion Cycle"] = prepared["DSO"] + prepared["DIO"] - prepared["DPO"]
    prepared["DSO YoY"] = prepared["DSO"].pct_change()
    prepared["DIO YoY"] = prepared["DIO"].pct_change()
    return prepared.reset_index(drop=True)


def create_qoe_waterfall(row: pd.Series) -> go.Figure:
    labels = [
        "Reported EBITDA",
        "비경상적 손익",
        "대주주 관련 비용",
        "회계정책 조정",
        "Normalized EBITDA",
    ]
    values = [
        row["Reported EBITDA"],
        row["One_off_Loss"],
        row["Owner_Expense"],
        row["Accounting_Adj"],
        row["Normalized EBITDA"],
    ]

    fig = go.Figure(
        go.Waterfall(
            name="QoE Bridge",
            orientation="v",
            measure=["absolute", "relative", "relative", "relative", "total"],
            x=labels,
            y=values,
            connector={"line": {"color": "#64748b"}},
            increasing={"marker": {"color": "#2563eb"}},
            decreasing={"marker": {"color": "#dc2626"}},
            totals={"marker": {"color": "#111827"}},
            text=[format_krw(value) for value in values],
            textposition="outside",
        )
    )
    fig.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=30, b=20),
        yaxis_title="백만원",
        showlegend=False,
    )
    return fig


def build_wc_alerts(df: pd.DataFrame) -> list[str]:
    alerts = []
    for _, row in df.iloc[1:].iterrows():
        spike_items = []
        if pd.notna(row["DSO YoY"]) and row["DSO YoY"] >= 0.15:
            spike_items.append("매출채권")
        if pd.notna(row["DIO YoY"]) and row["DIO YoY"] >= 0.15:
            spike_items.append("재고자산")
        if spike_items:
            alerts.append(
                f"🚨 경고: {row['Year']}년도 {'/'.join(spike_items)} 회전기일 급증 "
                "(부실자산 및 가공매출 위험성 정밀 실사 필요)"
            )
    return alerts


def create_template_file() -> bytes:
    return create_mock_financials().to_csv(index=False, encoding="utf-8-sig").encode(
        "utf-8-sig"
    )


st.title("M&A FDD & Valuation Automation Prototype")
st.caption(
    "재무실사 QoE, 운전자본 분석, EV/EBITDA Valuation을 한 화면에서 검토하는 Deals 포트폴리오용 프로토타입"
)

with st.sidebar:
    st.header("데이터 업로드")
    st.caption("업로드 파일이 없으면 기본 Mock Data로 대시보드가 작동합니다.")
    uploaded_file = st.file_uploader(
        "3개년 재무 데이터 업로드",
        type=["xlsx", "csv"],
        help="엑셀(.xlsx) 또는 CSV 파일을 업로드하세요.",
    )
    st.download_button(
        "업로드 템플릿 다운로드",
        data=create_template_file(),
        file_name="fdd_valuation_upload_template.csv",
        mime="text/csv",
    )
    with st.expander("필수 컬럼 안내", expanded=True):
        st.code(", ".join(REQUIRED_COLUMNS), language="text")

data_source = "Mock Data"
raw_financials = create_mock_financials()

if uploaded_file is not None:
    try:
        uploaded_df = read_uploaded_file(uploaded_file)
        validation_errors = validate_uploaded_data(uploaded_df)
        if validation_errors:
            st.error("업로드 파일 검증 실패: " + " / ".join(validation_errors))
            st.warning("검증 실패로 기본 Mock Data를 표시합니다.")
        else:
            raw_financials = uploaded_df
            data_source = uploaded_file.name
            st.success(f"업로드 파일을 반영했습니다: {uploaded_file.name}")
    except Exception as exc:
        st.error(f"업로드 파일을 읽는 중 오류가 발생했습니다: {exc}")
        st.warning("오류 발생으로 기본 Mock Data를 표시합니다.")

financials = prepare_financials(raw_financials)

if len(financials) < 2:
    st.error("계산 가능한 데이터가 부족합니다. 숫자 컬럼 값을 확인해 주세요.")
    st.stop()

latest = financials.iloc[-1]
prior = financials.iloc[-2]

wc_alerts = build_wc_alerts(financials)
for alert in wc_alerts:
    st.error(alert)

st.caption(f"현재 데이터 소스: {data_source}")

with st.container():
    kpi_1, kpi_2, kpi_3, kpi_4 = st.columns(4)
    kpi_1.metric(
        f"{latest['Year']} Revenue",
        format_krw(latest["Revenue"]),
        f"{(latest['Revenue'] / prior['Revenue'] - 1):.1%} YoY",
    )
    kpi_2.metric(
        "Reported EBITDA",
        format_krw(latest["Reported EBITDA"]),
        f"{latest['EBITDA Margin']:.1%} margin",
    )
    kpi_3.metric(
        "Normalized EBITDA",
        format_krw(latest["Normalized EBITDA"]),
        f"{latest['Normalized EBITDA Margin']:.1%} margin",
    )
    kpi_4.metric("Net Debt", format_krw(latest["Net_Debt"]))

st.divider()

tab_qoe, tab_wc, tab_valuation = st.tabs(
    ["1. QoE 분석", "2. 운전자본 및 회전기일", "3. Valuation 시뮬레이션"]
)

with tab_qoe:
    st.subheader("Quality of Earnings 분석")
    st.write(
        "EBITDA 조정 항목을 비경상적 손익, 대주주 관련 비용, 회계정책 조정으로 구분해 Normalized EBITDA를 산출합니다."
    )

    selected_qoe_year = st.selectbox(
        "QoE 분석 기준 연도",
        financials["Year"],
        index=len(financials) - 1,
        key="qoe_year",
    )
    qoe_row = financials.loc[financials["Year"] == selected_qoe_year].iloc[0]

    chart_col, table_col = st.columns([1.35, 1])

    with chart_col:
        st.plotly_chart(create_qoe_waterfall(qoe_row), width="stretch")

    with table_col:
        st.dataframe(
            financials[
                [
                    "Year",
                    "Reported EBITDA",
                    "One_off_Loss",
                    "Owner_Expense",
                    "Accounting_Adj",
                    "QoE Adjustment",
                    "Normalized EBITDA",
                    "Normalized EBITDA Margin",
                ]
            ].rename(
                columns={
                    "One_off_Loss": "비경상적 손익",
                    "Owner_Expense": "대주주 관련 비용",
                    "Accounting_Adj": "회계정책 조정",
                }
            ).style.format(
                {
                    "Reported EBITDA": "{:,.0f}",
                    "비경상적 손익": "{:,.0f}",
                    "대주주 관련 비용": "{:,.0f}",
                    "회계정책 조정": "{:,.0f}",
                    "QoE Adjustment": "{:,.0f}",
                    "Normalized EBITDA": "{:,.0f}",
                    "Normalized EBITDA Margin": "{:.1%}",
                }
            ),
            width="stretch",
            hide_index=True,
        )

    st.info(
        f"{selected_qoe_year} 기준 QoE 조정액은 {format_krw(qoe_row['QoE Adjustment'])}이며, "
        f"Normalized EBITDA는 {format_krw(qoe_row['Normalized EBITDA'])}입니다."
    )

with tab_wc:
    st.subheader("Working Capital & Turnover Days")

    if wc_alerts:
        st.error("운전자본 이상 징후가 감지되었습니다. 상단 경고 배너의 연도와 항목을 확인하세요.")

    wc_metric_1, wc_metric_2, wc_metric_3, wc_metric_4 = st.columns(4)
    wc_metric_1.metric(
        "매출채권 회전기일(DSO)",
        f"{latest['DSO']:.1f} 일",
        f"{latest['DSO YoY']:.1%} YoY",
    )
    wc_metric_2.metric(
        "재고자산 회전기일(DIO)",
        f"{latest['DIO']:.1f} 일",
        f"{latest['DIO YoY']:.1%} YoY",
    )
    wc_metric_3.metric("매입채무 회전기일(DPO)", f"{latest['DPO']:.1f} 일")
    wc_metric_4.metric("Cash Conversion Cycle", f"{latest['Cash Conversion Cycle']:.1f} 일")

    trend_col, detail_col = st.columns([1.25, 1])

    with trend_col:
        st.markdown("#### 순운전자본 트렌드")
        wc_trend = financials.set_index("Year")[["AR", "Inventory", "AP", "Net Working Capital"]]
        st.line_chart(wc_trend, height=360)

    with detail_col:
        st.markdown("#### 회전기일 상세")
        wc_detail = financials[
            [
                "Year",
                "DSO",
                "DSO YoY",
                "DIO",
                "DIO YoY",
                "DPO",
                "Cash Conversion Cycle",
            ]
        ]
        st.dataframe(
            wc_detail.style.format(
                {
                    "DSO": "{:.1f}",
                    "DSO YoY": "{:.1%}",
                    "DIO": "{:.1f}",
                    "DIO YoY": "{:.1%}",
                    "DPO": "{:.1f}",
                    "Cash Conversion Cycle": "{:.1f}",
                },
                na_rep="-",
            ),
            width="stretch",
            hide_index=True,
        )

    st.caption(
        "DSO = AR / Revenue x 365, DIO = Inventory / COGS x 365, DPO = AP / COGS x 365"
    )

with tab_valuation:
    st.subheader("EV/EBITDA Multiple Valuation")

    control_col, output_col = st.columns([0.85, 1.15])

    with control_col:
        selected_year = st.selectbox("Valuation 기준 연도", financials["Year"], index=len(financials) - 1)
        selected_row = financials.loc[financials["Year"] == selected_year].iloc[0]
        multiple = st.slider(
            "유사기업 EV/EBITDA Multiple",
            min_value=5.0,
            max_value=15.0,
            value=9.0,
            step=0.5,
            format="%.1fx",
        )
        st.markdown(
            "**Equity Value 산식**  \n"
            "Enterprise Value = Normalized EBITDA x EV/EBITDA Multiple  \n"
            "Equity Value = Enterprise Value - Net Debt"
        )

    enterprise_value = selected_row["Normalized EBITDA"] * multiple
    equity_value = enterprise_value - selected_row["Net_Debt"]
    valuation_bridge = pd.DataFrame(
        {
            "Valuation Input": [
                "Normalized EBITDA",
                "Selected Multiple",
                "Enterprise Value",
                "Less: Net Debt",
                "Implied Equity Value",
            ],
            "Formula": [
                "Reported EBITDA + QoE Adjustments",
                "유사기업 EV/EBITDA Multiple",
                "Normalized EBITDA x Multiple",
                "업로드 파일의 Net_Debt",
                "Enterprise Value - Net Debt",
            ],
            "Value": [
                format_krw(selected_row["Normalized EBITDA"]),
                format_multiple(multiple),
                format_krw(enterprise_value),
                format_krw(selected_row["Net_Debt"]),
                format_krw(equity_value),
            ],
        }
    )

    with output_col:
        val_1, val_2 = st.columns(2)
        val_1.metric("Enterprise Value", format_krw(enterprise_value))
        val_2.metric("Equity Value", format_krw(equity_value))

        bridge_1, bridge_2, bridge_3 = st.columns(3)
        bridge_1.metric("Normalized EBITDA", format_krw(selected_row["Normalized EBITDA"]))
        bridge_2.metric("Applied Multiple", format_multiple(multiple))
        bridge_3.metric("Less: Net Debt", format_krw(selected_row["Net_Debt"]))

        sensitivity = pd.DataFrame({"Multiple": [x / 2 for x in range(10, 31)]})
        sensitivity["Enterprise Value"] = (
            sensitivity["Multiple"] * selected_row["Normalized EBITDA"]
        )
        sensitivity["Equity Value"] = sensitivity["Enterprise Value"] - selected_row["Net_Debt"]
        sensitivity = sensitivity.set_index("Multiple")

        st.markdown("#### Multiple Sensitivity")
        st.line_chart(sensitivity[["Enterprise Value", "Equity Value"]], height=320)

    st.markdown(f"#### Equity Value Bridge ({format_multiple(multiple)} 적용)")
    st.caption(
        f"현재 슬라이더 기준: {format_krw(selected_row['Normalized EBITDA'])} x "
        f"{format_multiple(multiple)} - {format_krw(selected_row['Net_Debt'])} = "
        f"{format_krw(equity_value)}"
    )
    st.table(valuation_bridge)

with st.expander("현재 분석 데이터 보기"):
    st.dataframe(
        financials.style.format(
            {
                "Revenue": "{:,.0f}",
                "COGS": "{:,.0f}",
                "SG&A": "{:,.0f}",
                "One_off_Loss": "{:,.0f}",
                "Owner_Expense": "{:,.0f}",
                "Accounting_Adj": "{:,.0f}",
                "Gross Profit": "{:,.0f}",
                "Reported EBITDA": "{:,.0f}",
                "QoE Adjustment": "{:,.0f}",
                "Normalized EBITDA": "{:,.0f}",
                "EBITDA Margin": "{:.1%}",
                "Normalized EBITDA Margin": "{:.1%}",
                "AR": "{:,.0f}",
                "Inventory": "{:,.0f}",
                "AP": "{:,.0f}",
                "Net_Debt": "{:,.0f}",
                "Net Working Capital": "{:,.0f}",
                "DSO": "{:.1f}",
                "DIO": "{:.1f}",
                "DPO": "{:.1f}",
                "Cash Conversion Cycle": "{:.1f}",
                "DSO YoY": "{:.1%}",
                "DIO YoY": "{:.1%}",
            },
            na_rep="-",
        ),
        width="stretch",
        hide_index=True,
    )
