import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정 (반드시 코드 최상단에 위치해야 함)
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

# 3. 메타데이터 가져오기 (종목설명 및 AUM 단위 변환)
@st.cache_data(ttl=86400)
def get_etf_metadata():
    meta = {}
    for t in TICKERS:
        meta[t] = {"lev": "1x", "inv": "NO", "aum": 0, "desc": "-"}
        try:
            info = yf.Ticker(t).info
            name = info.get('longName', '')
            name_up = name.upper()
            
            # 레버리지/인버스 판단
            inv = "YES" if any(w in name_up for w in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
            if any(w in name_up for w in ["3X", "TRIPLE"]): lev = "3x"
            elif any(w in name_up for w in ["2X", "DOUBLE", "ULTRA"]): lev = "2x"
            else: lev = "1x"
            
            # AUM을 Million($MM) 단위로 변환
            raw_assets = info.get('totalAssets') or info.get('navPrice', 0)
            aum_mm = round(raw_assets / 1_000_000, 1) if raw_assets else 0
            
            meta[t] = {"lev": lev, "inv": inv, "aum": aum_mm, "desc": name}
        except:
            pass
    return meta

# 4. ETF 데이터 분석 함수
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    meta_dict = get_etf_metadata()
    results = []
    
    for t in TICKERS:
        try:
            df = yf.download(t, period=f"{period_years}y", interval="1d", progress=False)
            if df.empty or len(df) < 2: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            cp = float(df['Close'].iloc[-1])
            start_p = float(df['Close'].iloc[0])
            high = float(df['High'].max())
            low = float(df['Low'].min())
            
            chg = round(((cp - start_p) / start_p) * 100, 2)
            mdd = round(((cp - high) / high) * 100, 2)
            rec = round(((cp - low) / low) * 100, 2)
            score = round(abs(mdd) - rec, 1)
            
            if score >= 50: sig = "🔥 적극매수"
            elif 30 <= score < 50: sig = "🟢 매수"
            else: sig = "🟡 진입"

            m = meta_dict.get(t, {"lev": "1x", "inv": "NO", "aum": 0, "desc": "-"})

            results.append({
                "신호": sig, "ETF": t, "종목설명": m["desc"], "레버리지": m["lev"], "인버스": m["inv"],
                "현재가": cp, "MDD": mdd, "회복률": rec, "기간변화": chg, "점수": score, "자산규모($MM)": m["aum"]
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
        st.warning("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.")
        return

    # 필터
    c1, c2, c3 = st.columns(3)
    with c1: f_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"sig_{years}")
    with c2: f_lev = st.multiselect("레버리지", ["3x", "2x", "1x"], default=["3x", "2x", "1x"], key=f"lev_{years}")
    with c3: f_inv = st.radio("인버스 포함", ["전체", "YES", "NO"], index=0, horizontal=True, key=f"inv_{years}")

    filtered = data[data['신호'].isin(f_sig) & data['레버리지'].isin(f_lev)]
    if f_inv != "전체": filtered = filtered[filtered['인버스'] == f_inv]

    st.dataframe(
        filtered.sort_values("점수", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "현재가": st.column_config.NumberColumn("현재가", format="$%.2f"),
            "MDD": st.column_config.NumberColumn("MDD", format="%.1f%%"),
            "회복률": st.column_config.NumberColumn("회복률", format="%.1f%%"),
            "기간변화": st.column_config.NumberColumn("기간변화", format="%.1f%%"),
            "자산규모($MM)": st.column_config.NumberColumn("AUM ($MM)", format="$%.1f MM"),
            "종목설명": st.column_config.TextColumn("종목설명", width="large")
        }
    )

for i, tab in enumerate(tabs):
    with tab: display_content(i+1)
