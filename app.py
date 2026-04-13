import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD & Metadata Tracker", page_icon="🏦", layout="wide")

# 2. 티커 목록 (정렬 및 중복 제거)
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

# 3. 데이터 로드 및 메타데이터 분석 함수
@st.cache_data(ttl=3600)
def fetch_etf_data(period_years):
    results = []
    my_bar = st.progress(0, text="시장 데이터 및 ETF 정보 수집 중...")
    
    for i, ticker_symbol in enumerate(TICKERS):
        try:
            ticker = yf.Ticker(ticker_symbol)
            yf_period = f"{period_years}y"
            df = ticker.history(period=yf_period)
            
            if df.empty: continue

            # --- 메타데이터 추출 (AUM, 배수, Inverse) ---
            info = ticker.info
            name = info.get('longName', '').upper()
            
            # 1. Inverse 여부 판단
            is_inverse = "YES" if any(word in name for word in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
            
            # 2. 레버리지 배수 판단 (이름 기반 자동 감지)
            if any(word in name for word in ["3X", "TRIPLE"]): leverage = "3x"
            elif any(word in name for word in ["2X", "DOUBLE", "ULTRA"]): leverage = "2x"
            else: leverage = "1x"
            
            # 3. AUM (운용자산) 정보
            aum_raw = info.get('totalAssets', 0)
            if aum_raw >= 1e9: aum = f"${aum_raw/1e9:.2f}B"
            elif aum_raw >= 1e6: aum = f"${aum_raw/1e6:.1f}M"
            else: aum = "N/A"

            # --- 가격 지표 계산 ---
            cp = float(df['Close'].iloc[-1])
            start_p = float(df['Close'].iloc[0])
            high = float(df['High'].max())
            low = float(df['Low'].min())
            
            change_rate = ((cp - start_p) / start_p) * 100
            mdd = ((cp - high) / high) * 100
            recovery = ((cp - low) / low) * 100
            
            # 스코어 공식 적용
            score = abs(mdd) - recovery
            
            if score >= 50: signal = "🔥 적극매수"
            elif 30 <= score < 50: signal = "🟢 매수"
            else: signal = "🟡 진입"
            
            results.append({
                "신호": signal,
                "ETF": ticker_symbol,
                "배수": leverage,
                "Inverse": is_inverse,
                "AUM": aum,
                "현재가": f"${cp:.2f}",
                "MDD": f"{mdd:.1f}%",
                "회복률": f"{recovery:.1f}%",
                "스코어": round(score, 1),
                "기간변화": f"{change_rate:+.1f}%",
                "고가/저가": f"${high:.1f}/${low:.1f}"
            })
        except: continue
        my_bar.progress((i + 1) / len(TICKERS))
    
    my_bar.empty()
    return pd.DataFrame(results).sort_values("스코어", ascending=False)

# 4. UI 구성
st.title("🏦 ETF 전문 분석 대시보드")
ny_tz = pytz.timezone('America/New_York')
st.caption(f"최종 업데이트 (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')}")

tab1, tab2, tab3 = st.tabs(["📅 1년", "📅 2년", "📅 3년"])

def display_dashboard(years):
    data = fetch_etf_data(years)
    if not data.empty:
        # 필터 레이아웃
        f1, f2, f3 = st.columns(3)
        with f1:
            sel_signals = st.multiselect(f"{years}y 신호", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"], key=f"s_{years}")
        with f2:
            sel_lev = st.multiselect(f"{years}y 배수", ["3x", "2x", "1x"], default=["3x", "2x"], key=f"l_{years}")
        with f3:
            sel_inv = st.radio(f"{years}y Inverse 포함", ["전체", "YES", "NO"], index=0, horizontal=True, key=f"i_{years}")

        # 필터 적용
        df_final = data[data['신호'].isin(sel_signals) & data['배수'].isin(sel_lev)]
        if sel_inv != "전체":
            df_final = df_final[df_final['Inverse'] == sel_inv]

        # 데이터프레임 출력
        st.dataframe(
            df_final,
            use_container_width=True,
            hide_index=True,
            column_config={
                "AUM": st.column_config.TextColumn("자산규모(AUM)", help="운용 자산 총액 (B: 10억달러, M: 100만달러)"),
                "배수": st.column_config.TextColumn("레버리지", width="small"),
                "Inverse": st.column_config.TextColumn("인버스", width="small"),
                "스코어": st.column_config.NumberColumn("점수", format="%.1f")
            }
        )
    else:
        st.error("데이터를 불러오지 못했습니다.")

with tab1: display_dashboard(1)
with tab2: display_dashboard(2)
with tab3: display_dashboard(3)
