import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD Tracker", page_icon="🏦", layout="wide")

# 2. 티커 목록 (중복 제거 및 정렬)
TICKERS = [
    "TQQQ", "SOXL", "QLD", "SSO", "SPXL", "TSLL", "UPRO", "NVDL", "TMF",
    "TECL", "SQQQ", "FAS", "AGQ", "SH", "BULZ", "USD", "TNA", "NUGT",
    "KORU", "UGL", "SCO", "SOXS", "PSQ", "MUU", "UDOW", "DSPY", "YINN",
    "GGLL", "ROM", "UYG", "SNXX", "UCO", "MSFU", "LABU", "AMDL", "JNUG",
    "SDS", "NVDU", "NAIL", "SPXU", "CONL", "DPST", "NVDX", "PLTU", "FNGO",
    "DDM", "PTIR", "SPXS", "BOIL", "GUSH", "BITU", "DFEN", "METU", "LITX",
    "MSTU", "ERX", "TSMX", "QID", "SPDN", "BMNU", "UVXY", "URTY", "AMZU",
    "TZA", "TBT", "TSPY", "CWEB", "TSLT", "ASTX", "UWM", "ORCX", "SBIT",
    "KOLD", "ETHT", "MSTX", "SDOW", "MULL", "FBL", "TSLQ", "SPUU", "SVXY",
    "RWM", "TMV", "BITI", "AVGX", "RKLX", "DOG", "NFXL", "SJB", "EDC",
    "AAPU", "FAZ", "IONX", "AVL", "BRZU", "MVV", "CURE", "ZSL", "GLL",
    "TSLR", "FNGD", "DIG", "YANG", "APPX", "MSTZ", "MQQQ", "BABX", "NEBX",
    "CHAU", "DRIP", "CWVX", "SRTY", "FNGG", "TBF", "OKLL", "SMCX", "ETHD",
    "NVD", "LABD", "TECS", "INTW", "DUST", "WEBL", "MSFL", "HIMZ", "BIB",
    "ROBN", "SARK", "RXL", "QQQU", "UBT", "TSLS", "MIDU", "MVLL", "TSDD",
    "DXD", "TWM", "NBIL", "INDL", "EURL", "FNGU", "DUSL", "UTSL", "MEXX", 
    "TPOR", "PILL", "DRN", "UYXY"
]
TICKERS = sorted(list(set(TICKERS)))

# 3. 레버리지/인버스 구분 함수 (API 호출 없이 티커명 기반 판단)
def get_etf_type(ticker):
    # 인버스 그룹
    inverses = ["SQQQ", "SOXS", "SH", "PSQ", "SDS", "SPXU", "SPXS", "QID", "SPDN", "TZA", "KOLD", "BITI", "DOG", "FAZ", "FNGD", "YANG", "DRIP", "SRTY", "NVD", "LABD", "TECS", "DUST", "SARK", "TSLS", "TSDD", "DXD", "TWM", "SDOW", "TMV", "ZSL"]
    # 3배 레버리지 그룹
    triple = ["TQQQ", "SOXL", "SPXL", "UPRO", "TSLL", "NVDL", "TMF", "TECL", "FAS", "BULZ", "TNA", "NUGT", "KORU", "YINN", "MSFU", "LABU", "JNUG", "NAIL", "CONL", "DPST", "NVDX", "FNGO", "GUSH", "BITU", "DFEN", "MSTU", "ERX", "URTY", "AMZU", "CWEB", "ASTX", "MSTX", "FBL", "MEXX", "TPOR", "DRN", "WEBL", "MIDU", "FNGU", "DUSL", "UTSL"]
    # 2배 레버리지 그룹
    double = ["QLD", "SSO", "AGQ", "USD", "UGL", "ROM", "UYG", "UCO", "AMDL", "NVDU", "PLTU", "DDM", "PTIR", "BITU", "TSMX", "TSLT", "UWM", "SBIT", "MULL", "EDC", "AAPU", "AVL", "BRZU", "MVV", "CURE", "GLL", "DIG", "CHAU", "BIB", "RXL", "EURL"]
    
    # 구분 로직
    is_inv = ticker in inverses
    prefix = "-" if is_inv else ""
    
    if ticker in triple: return f"{prefix}3x"
    if ticker in double: return f"{prefix}2x"
    if is_inv: return "-1x"
    return "1x"

# 4. 데이터 분석 함수
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    data = yf.download(TICKERS, period=f"{period_years}y", interval="1d", progress=False)
    if data.empty: return pd.DataFrame()

    results = []
    for t in TICKERS:
        try:
            close_series = data['Close'][t].dropna()
            high_series = data['High'][t].dropna()
            low_series = data['Low'][t].dropna()
            
            if len(close_series) < 2: continue

            cp = float(close_series.iloc[-1])
            start_p = float(close_series.iloc[0])
            high_val = float(high_series.max())
            low_val = float(low_series.min())
            
            chg = round(((cp - start_p) / start_p) * 100, 2)
            mdd = round(((cp - high_val) / high_val) * 100, 2)
            rec = round(((cp - low_val) / low_val) * 100, 2)
            score = round(abs(mdd) - rec, 1)
            
            # 신호 판단
            if score >= 50: sig = "🔥 적극매수"
            elif 30 <= score < 50: sig = "🟢 매수"
            else: sig = "🟡 진입"

            results.append({
                "신호": sig, 
                "ETF": t, 
                "구분": get_etf_type(t), # 신규 추가
                "현재가": cp, 
                "고가/저가": f"${high_val:.2f} / ${low_val:.2f}",
                "MDD": mdd, 
                "회복률": rec, 
                "기간변화": chg, 
                "점수": score
            })
        except: continue
    return pd.DataFrame(results)

# 5. 메인 UI
st.title("🏦 통합 ETF 분석 리포트")
ny_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"Last Update (NY): {ny_time}")

tabs = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_content(years):
    data = fetch_etf_data(years)
    if data.empty:
        st.warning("데이터를 불러오지 못했습니다.")
        return

    # 필터 UI
    c1, c2 = st.columns(2)
    with c1:
        f_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], 
                               default=["🔥 적극매수", "🟢 매수", "🟡 진입"], key=f"sig_{years}")
    with c2:
        f_type = st.multiselect("레버리지 구분", ["3x", "2x", "1x", "-1x", "-2x", "-3x"], 
                                default=["3x", "2x", "1x", "-1x", "-2x", "-3x"], key=f"type_{years}")

    filtered = data[data['신호'].isin(f_sig) & data['구분'].isin(f_type)]

    st.dataframe(
        filtered.sort_values("점수", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "현재가": st.column_config.NumberColumn("현재가", format="$%.2f"),
            "MDD": st.column_config.NumberColumn("MDD", format="%.1f%%"),
            "회복률": st.column_config.NumberColumn("회복률", format="%.1f%%"),
            "기간변화": st.column_config.NumberColumn("기간변화", format="%.1f%%"),
        }
    )

for i, tab in enumerate(tabs):
    with tab: display_content(i+1)
