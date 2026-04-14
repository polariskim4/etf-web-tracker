import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD 전문 분석", page_icon="🏦", layout="wide")

# 2. 티커 목록
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

@st.cache_data(ttl=86400)
def get_etf_metadata():
    meta = {}
    for t in TICKERS:
        meta[t] = {"lev": "알수없음", "inv": "알수없음", "aum": 0} # AUM 기본값을 0으로 설정
        try:
            info = yf.Ticker(t).info
            name = info.get('longName', '').upper()
            if name:
                inv = "YES" if any(w in name for w in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
                if any(w in name for w in ["3X", "TRIPLE"]): lev = "3x"
                elif any(w in name for w in ["2X", "DOUBLE", "ULTRA"]): lev = "2x"
                else: lev = "1x"
                aum = info.get('totalAssets', 0)
                meta[t] = {"lev": lev, "inv": inv, "aum": aum}
        except:
            pass
    return meta

@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    meta_dict = get_etf_metadata()
    results = []
    
    for ticker_symbol in TICKERS:
        try:
            df = yf.download(ticker_symbol, period=f"{period_years}y", interval="1d", progress=False)
            if df.empty or len(df) < 5: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            cp = float(df['Close'].iloc[-1])
            start_p = float(df['Close'].iloc[0])
            high = float(df['High'].max())
            low = float(df['Low'].min())
            
            # 문자열이 아닌 '숫자' 그대로 저장 (정렬을 위해)
            chg = round(((cp - start_p) / start_p) * 100, 2)
            mdd = round(((cp - high) / high) * 100, 2)
            rec = round(((cp - low) / low) * 100, 2)
            score = round(abs(mdd) - rec, 1)
            
            if score >= 50: sig = "🔥 적극매수"
            elif 30 <= score < 50: sig = "🟢 매수"
            else: sig = "🟡 진입"

            t_meta = meta_dict.get(ticker_symbol, {"lev": "알수없음", "inv": "알수없음", "aum": 0})

            results.append({
                "신호": sig, "ETF": ticker_symbol, "레버리지": t_meta["lev"], "인버스": t_meta["inv"],
                "현재가": cp, "고가": high, "저가": low,
                "MDD": mdd, "회복률": rec, "기간변화": chg,
                "점수": score, "자산규모(AUM)": t_meta["aum"]
            })
        except: continue
    
    return pd.DataFrame(results)

# 5. UI 구성
st.title("🏦 ETF 전문 분석 대시보드")

tab1, tab2, tab3 = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_dashboard(years):
    df = fetch_etf_data(years)
    if df.empty:
        st.warning("데이터를 불러오지 못했습니다.")
        return

    # 필터 UI
    c1, c2, c3 = st.columns(3)
    with c1: s_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"s{years}")
    with c2: s_lev = st.multiselect("레버리지", ["3x", "2x", "1x", "알수없음"], default=["3x", "2x", "1x", "알수없음"], key=f"l{years}")
    with c3: s_inv = st.radio("인버스 포함", ["전체", "YES", "NO"], horizontal=True, key=f"i{years}")

    final_df = df[df['신호'].isin(s_sig) & df['레버리지'].isin(s_lev)].copy()
    if s_inv != "전체": final_df = final_df[final_df['인버스'] == s_inv]

    # 소팅 및 컬럼 설정
    st.dataframe(
        final_df.sort_values("점수", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "현재가": st.column_config.NumberColumn("현재가", format="$%.2f"),
            "고가": st.column_config.NumberColumn("고가", format="$%.1f"),
            "저가": st.column_config.NumberColumn("저가", format="$%.1f"),
            "MDD": st.column_config.NumberColumn("MDD", format="%.1f%%"),
            "회복률": st.column_config.NumberColumn("회복률", format="%.1f%%"),
            "기간변화": st.column_config.NumberColumn("기간변화", format="%.1f%%"),
            "점수": st.column_config.NumberColumn("점수", format="%.1f"),
            "자산규모(AUM)": st.column_config.NumberColumn("자산규모(AUM)", format="$%.2e"), # 지수표기법 또는 단순 숫자
        }
    )

with tab1: display_dashboard(1)
with tab2: display_dashboard(2)
with tab3: display_dashboard(3)
