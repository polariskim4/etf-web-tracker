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

# 3. 데이터 로드 및 분석 함수
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    results = []
    my_bar = st.progress(0, text=f"{period_years}년 데이터 분석 중...")
    
    for i, ticker_symbol in enumerate(TICKERS):
        try:
            t_obj = yf.Ticker(ticker_symbol)
            df = t_obj.history(period=f"{period_years}y")
            
            # 데이터가 충분하지 않으면 스킵
            if df.empty or len(df) < 10: continue

            # 메타데이터 추출
            info = t_obj.info
            name = info.get('longName', '').upper()
            is_inv = "YES" if any(w in name for w in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
            
            if any(w in name for w in ["3X", "TRIPLE"]): lev = "3x"
            elif any(w in name for w in ["2X", "DOUBLE", "ULTRA"]): lev = "2x"
            else: lev = "1x"
            
            aum_val = info.get('totalAssets', 0)
            aum = f"${aum_val/1e9:.2f}B" if aum_val >= 1e9 else (f"${aum_val/1e6:.1f}M" if aum_val >= 1e6 else "N/A")

            # 지표 계산
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
            
            results.append({
                "신호": sig, "ETF": ticker_symbol, "레버리지": lev, "인버스": is_inv,
                "현재가": f"${cp:.2f}", "고가/저가": f"${high:.1f}/${low:.1f}",
                "MDD": f"{mdd:.1f}%", "회복률": f"{rec:.1f}%", "기간변화": f"{chg:+.1f}%",
                "점수": score, "자산규모(AUM)": aum
            })
        except: continue
        my_bar.progress((i + 1) / len(TICKERS))
    
    my_bar.empty()
    # 결과가 없을 경우 빈 데이터프레임 구조 반환하여 KeyError 방지
    if not results:
        return pd.DataFrame(columns=["신호", "ETF", "레버리지", "인버스", "현재가", "고가/저가", "MDD", "회복률", "기간변화", "점수", "자산규모(AUM)"])
    return pd.DataFrame(results).sort_values("점수", ascending=False)

# 4. UI 구성
st.title("🏦 ETF 전문 분석 대시보드")
ny_tz = pytz.timezone('America/New_York')
st.caption(f"Last Update (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')}")

tab1, tab2, tab3 = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_dashboard(years):
    df = fetch_etf_data(years)
    
    if df.empty:
        st.warning(f"{years}년 기간에 대한 데이터를 불러오지 못했습니다. 종목의 상장 기간을 확인해 주세요.")
        return

    # 필터
    c1, c2, c3 = st.columns(3)
    with c1: s_sig = st.multiselect("신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"s{years}")
    with c2: s_lev = st.multiselect("레버리지", ["3x", "2x", "1x"], default=["3x", "2x", "1x"], key=f"l{years}")
    with c3: s_inv = st.radio("인버스 포함", ["전체", "YES", "NO"], horizontal=True, key=f"i{years}")

    # 필터 적용
    final_df = df[df['신호'].isin(s_sig) & df['레버리지'].isin(s_lev)]
    if s_inv != "전체": final_df = final_df[final_df['인버스'] == s_inv]

    # 컬럼 순서 재배치 (요청 사항 반영)
    final_df = final_df[["신호", "ETF", "레버리지", "인버스", "현재가", "고가/저가", "MDD", "회복률", "기간변화", "점수", "자산규모(AUM)"]]

    st.dataframe(final_df, use_container_width=True, hide_index=True)

with tab1: display_dashboard(1)
with tab2: display_dashboard(2)
with tab3: display_dashboard(3)
