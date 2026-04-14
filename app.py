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

# 3. ETF 데이터 분석 함수 (속도 최적화 버전)
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    # 주가 데이터 일괄 다운로드 (네트워크 요청 1회로 단축)
    data = yf.download(TICKERS, period=f"{period_years}y", interval="1d", progress=False)
    if data.empty: return pd.DataFrame()

    results = []
    
    for t in TICKERS:
        try:
            # MultiIndex 처리 및 데이터 추출
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
            
            if score >= 50: sig = "🔥 적극매수"
            elif 30 <= score < 50: sig = "🟢 매수"
            else: sig = "🟡 진입"

            results.append({
                "신호": sig, 
                "ETF": t, 
                "현재가": cp, 
                "고가/저가": f"${high_val:.2f} / ${low_val:.2f}",
                "MDD": mdd, 
                "회복률": rec, 
                "기간변화": chg, 
                "점수": score
            })
        except: continue
    return pd.DataFrame(results)

# 4. 메인 UI
st.title("🏦 통합 ETF 분석 리포트")
ny_time = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S')
st.caption(f"Last Update (NY): {ny_time}")

tabs = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_content(years):
    data = fetch_etf_data(years)
    if data.empty:
        st.warning("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        return

    # 신호 필터 (레버리지/인버스 필터는 메타데이터 삭제로 인해 제거됨)
    f_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], 
                           default=["🔥 적극매수", "🟢 매수", "🟡 진입"], key=f"sig_{years}")

    filtered = data[data['신호'].isin(f_sig)]

    st.dataframe(
        filtered.sort_values("점수", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "현재가": st.column_config.NumberColumn("현재가", format="$%.2f"),
            "고가/저가": st.column_config.TextColumn("기간 내 고가 / 저가"),
            "MDD": st.column_config.NumberColumn("MDD", format="%.1f%%"),
            "회복률": st.column_config.NumberColumn("회복률", format="%.1f%%"),
            "기간변화": st.column_config.NumberColumn("기간변화", format="%.1f%%"),
            "점수": st.column_config.NumberColumn("점수", format="%.1f"),
        }
    )

for i, tab in enumerate(tabs):
    with tab: display_content(i+1)
