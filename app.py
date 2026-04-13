import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="ETF MDD 실시간 대시보드", page_icon="📈", layout="wide")

# 2. 요청하신 티커 목록 (중복 제거 및 정리)
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
TICKERS = list(dict.fromkeys(TICKERS)) # 중복 제거

# 3. 데이터 로드 함수
@st.cache_data(ttl=3600)
def fetch_etf_data():
    results = []
    total = len(TICKERS)
    my_bar = st.progress(0, text="데이터 수집 시작...")
    
    for i, ticker in enumerate(TICKERS):
        try:
            # 데이터 수집 (최근 5~10년치 데이터 확보)
            df = yf.download(ticker, period="10y", interval="1d", progress=False)
            
            if df is None or df.empty or len(df) < 5: # 최소한의 데이터 확인
                continue
            
            # 멀티 인덱스 대응
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            cp = float(df['Close'].iloc[-1])
            
            # 고점 계산 (데이터가 모자라면 전체 기간 중 최대값 사용)
            h_1y = float(df['High'].iloc[-252:].max()) if len(df) >= 252 else float(df['High'].max())
            h_2y = float(df['High'].iloc[-504:].max()) if len(df) >= 504 else h_1y
            h_3y = float(df['High'].iloc[-756:].max()) if len(df) >= 756 else h_2y
            
            # 저점 계산
            l_1y = float(df['Low'].iloc[-252:].min()) if len(df) >= 252 else float(df['Low'].min())
            l_2y = float(df['Low'].iloc[-504:].min()) if len(df) >= 504 else l_1y
            l_3y = float(df['Low'].iloc[-756:].min()) if len(df) >= 756 else l_2y
            
            m1 = round(((cp - h_1y) / h_1y) * 100, 1)
            m2 = round(((cp - h_2y) / h_2y) * 100, 1)
            m3 = round(((cp - h_3y) / h_3y) * 100, 1)
            
            g1 = round(((cp - l_1y) / l_1y) * 100, 1)
            g2 = round(((cp - l_2y) / l_2y) * 100, 1)
            g3 = round(((cp - l_3y) / l_3y) * 100, 1)
            
            # 판단 기준
            if m1 <= -60.0 or g1 <= 15.0:
                score, status = 3, "🔥 적극매수"
            elif m1 <= -30.0 or g1 <= 40.0:
                score, status = 2, "🟢 매수"
            else:
                score, status = 1, "🟡 진입"
            
            results.append({
                "ETF": ticker, "Price ($)": round(cp, 2), "Status": status, "Score": score,
                "MDD 1Y": m1, "MDD 2Y": m2, "MDD 3Y": m3,
                "Gain 1Y": g1, "Gain 2Y": g2, "Gain 3Y": g3
            })
        except Exception as e:
            continue
        
        my_bar.progress((i + 1) / total, text=f"{ticker} 분석 중... ({i+1}/{total})")
    
    my_bar.empty()
    
    if results:
        results.sort(key=lambda x: x['Score'], reverse=True)
        return pd.DataFrame(results).drop(columns=['Score'])
    return pd.DataFrame()

# 4. 화면 구성
ny_tz = pytz.timezone('America/New_York')
current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 통합 ETF 리포트 (Web)")
st.subheader(f"뉴욕 시간: {current_ny_time}")

df = fetch_etf_data()

if not df.empty:
    # 필터 기능 추가 (매수 등급별로 모아보기)
    status_list = ["전체"] + list(df['Status'].unique())
    selected_status = st.selectbox("등급 필터링", status_list)
    
    display_df = df if selected_status == "전체" else df[df['Status'] == selected_status]
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.write(f"표시된 종목 수: {len(display_df)} / 총 종목 수: {len(df)}")
else:
    st.error("데이터를 가져오는 데 실패했습니다. GitHub Actions가 정상인지 또는 티커가 올바른지 확인해 주세요.")
