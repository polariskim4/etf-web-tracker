import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD 전문 분석", page_icon="🏦", layout="wide")

# 2. 티커 목록 (130여 개)
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

# 3. 메타데이터(이름, AUM) 전용 수집 함수 (24시간 캐시 유지 - API 차단 방지)
@st.cache_data(ttl=86400)
def get_etf_metadata():
    meta = {}
    my_bar = st.progress(0, text="초기 1회 메타데이터(레버리지/AUM) 연동 중... (잠시만 기다려주세요)")
    for i, t in enumerate(TICKERS):
        # 기본값 설정
        meta[t] = {"lev": "알수없음", "inv": "알수없음", "aum": "N/A"}
        try:
            info = yf.Ticker(t).info
            name = info.get('longName', '')
            if name:
                name = name.upper()
                inv = "YES" if any(w in name for w in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
                
                if any(w in name for w in ["3X", "TRIPLE"]): lev = "3x"
                elif any(w in name for w in ["2X", "DOUBLE", "ULTRA"]): lev = "2x"
                else: lev = "1x"
                
                aum_val = info.get('totalAssets', 0)
                if aum_val and aum_val > 0:
                    aum = f"${aum_val/1e9:.2f}B" if aum_val >= 1e9 else f"${aum_val/1e6:.1f}M"
                
                meta[t] = {"lev": lev, "inv": inv, "aum": aum}
        except:
            pass # 차단되더라도 기본값 유지
        my_bar.progress((i + 1) / len(TICKERS))
    my_bar.empty()
    return meta

# 4. 가격 데이터 수집 및 분석 함수 (1시간 캐시)
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    meta_dict = get_etf_metadata() # 미리 캐시된 메타데이터 불러오기 (API 호출 안 함)
    results = []
    
    my_bar = st.progress(0, text=f"{period_years}년 가격 및 MDD 데이터 계산 중...")
    
    for i, ticker_symbol in enumerate(TICKERS):
        try:
            df = yf.download(ticker_symbol, period=f"{period_years}y", interval="1d", progress=False)
            if df.empty or len(df) < 10: 
                continue
                
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # 가격 지표 계산
            cp = float(df['Close'].iloc[-1])
            start_p = float(df['Close'].iloc[0])
            high = float(df['High'].max())
            low = float(df['Low'].min())
            
            chg = ((cp - start_p) / start_p) * 100
            mdd = ((cp - high) / high) * 100
            rec = ((cp - low) / low) * 100
            score = round(abs(mdd) - rec, 1)
            
            if score >= 50: sig = "🔥 적극매수"
            elif 30 <= score < 50: sig = "🟢 매수"
            else: sig = "🟡 진입"

            # 메타데이터 병합
            t_meta = meta_dict.get(ticker_symbol, {"lev": "알수없음", "inv": "알수없음", "aum": "N/A"})

            results.append({
                "신호": sig, "ETF": ticker_symbol, "레버리지": t_meta["lev"], "인버스": t_meta["inv"],
                "현재가": f"${cp:.2f}", "고가/저가": f"${high:.1f}/${low:.1f}",
                "MDD": f"{mdd:.1f}%", "회복률": f"{rec:.1f}%", "기간변화": f"{chg:+.1f}%",
                "점수": score, "자산규모(AUM)": t_meta["aum"]
            })
        except: 
            continue
        my_bar.progress((i + 1) / len(TICKERS))
    
    my_bar.empty()
    
    if not results:
        return pd.DataFrame(columns=["신호", "ETF", "레버리지", "인버스", "현재가", "고가/저가", "MDD", "회복률", "기간변화", "점수", "자산규모(AUM)"])
        
    return pd.DataFrame(results).sort_values("점수", ascending=False)

# 5. UI 구성
st.title("🏦 ETF 전문 분석 대시보드")
ny_tz = pytz.timezone('America/New_York')
st.caption(f"Last Update (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')}")

tab1, tab2, tab3 = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_dashboard(years):
    df = fetch_etf_data(years)
    
    if df.empty:
        st.warning("데이터가 없습니다. API 지연 또는 필터 설정을 확인해주세요.")
        return

    # 필터
    c1, c2, c3 = st.columns(3)
    with c1: s_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"s{years}")
    with c2: s_lev = st.multiselect("레버리지", ["3x", "2x", "1x", "알수없음"], default=["3x", "2x", "1x", "알수없음"], key=f"l{years}")
    with c3: s_inv = st.radio("인버스 포함", ["전체", "YES", "NO"], horizontal=True, key=f"i{years}")

    # 필터 적용
    final_df = df[df['신호'].isin(s_sig) & df['레버리지'].isin(s_lev)]
    if s_inv != "전체": 
        final_df = final_df[final_df['인버스'] == s_inv]

    # 컬럼 순서 재배치
    final_df = final_df[["신호", "ETF", "레버리지", "인버스", "현재가", "고가/저가", "MDD", "회복률", "기간변화", "점수", "자산규모(AUM)"]]

    st.dataframe(final_df, use_container_width=True, hide_index=True)

with tab1: display_dashboard(1)
with tab2: display_dashboard(2)
with tab3: display_dashboard(3)
