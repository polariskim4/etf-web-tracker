import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD Tracker", page_icon="📈", layout="wide")

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

# 3. 데이터 로드 함수 (기간 인자 추가)
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    results = []
    days = period_years * 252
    my_bar = st.progress(0, text=f"{period_years}년 데이터 분석 중...")
    
    for i, ticker in enumerate(TICKERS):
        try:
            # 기간에 따른 데이터 호출 (1y, 2y, 3y)
            yf_period = f"{period_years}y"
            df = yf.download(ticker, period=yf_period, interval="1d", progress=False)
            
            if df.empty or len(df) < 10: continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            cp = float(df['Close'].iloc[-1]) # 현재가
            start_price = float(df['Close'].iloc[0]) # 기준일(년초) 가격
            
            high = float(df['High'].max())
            low = float(df['Low'].min())
            
            # 1. 기간 변화율 (기준년초 대비)
            change_rate = ((cp - start_price) / start_price) * 100
            
            # 2. 최대 낙폭 (MDD)
            mdd = ((cp - high) / high) * 100
            
            # 3. 저점 대비 상승률 (회복률)
            recovery = ((cp - low) / low) * 100
            
            # 4. 스코어 계산: |MDD| * 100 - 회복률 * 100
            # 사용자 요청 공식: Score = |MDD %| - Recovery %
            # (수치 가독성을 위해 백분율 값 그대로 계산)
            score = abs(mdd) - recovery
            
            # 5. 신호 판별
            if score >= 50:
                signal = "🔥 적극매수"
            elif 30 <= score < 50:
                signal = "🟢 매수"
            else:
                signal = "🟡 진입"
            
            results.append({
                "신호": signal,
                "ETF": ticker,
                "현재가": f"${cp:.2f}",
                "기간 변화율": f"{change_rate:+.1f}%",
                "MDD": f"{mdd:.1f}%",
                "저점 대비 상승률": f"{recovery:+.1f}%",
                "고가 / 저가": f"${high:.1f} / ${low:.1f}",
                "스코어": round(score, 1)
            })
        except: continue
        my_bar.progress((i + 1) / len(TICKERS))
    
    my_bar.empty()
    return pd.DataFrame(results).sort_values("스코어", ascending=False)

# 4. UI 구성
st.title("📊 ETF 매수 신호 분석 대시보드")
ny_tz = pytz.timezone('America/New_York')
st.caption(f"Update (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')}")

# 상단 기간 선택 탭
tab1, tab2, tab3 = st.tabs(["📅 1년 분석", "📅 2년 분석", "📅 3년 분석"])

def display_data(years):
    data = fetch_etf_data(years)
    if not data.empty:
        # 필터링 섹션
        signals = st.multiselect(f"{years}년 기준 신호 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"filter_{years}")
        filtered_df = data[data['신호'].isin(signals)]
        
        # 테이블 출력
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "스코어": st.column_config.NumberColumn(format="%.1f"),
                "현재가": st.column_config.TextColumn(help="실시간에 가까운 최신 종가"),
                "MDD": st.column_config.TextColumn(help="전고점 대비 하락률"),
            }
        )
        st.info(f"💡 **스코어 기준:** MDD가 크고 회복률이 낮을수록 높은 점수 (|MDD| - 회복률)")
    else:
        st.warning("데이터를 불러올 수 없습니다.")

with tab1:
    display_data(1)
with tab2:
    display_data(2)
with tab3:
    display_data(3)
