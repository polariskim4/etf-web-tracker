import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 페이지 기본 설정
st.set_page_config(page_title="ETF MDD Tracker", page_icon="🚀", layout="wide")

TICKERS = [
  // 기존 + 추가 종목 통합 (중복 제거)
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
  "DXD", "TWM", "NBIL", "INDL", "EURL",
  // 기존 목록에만 있던 종목
  "FNGU", "DUSL", "UTSL", "MEXX", "TPOR", "PILL", "DRN", "UYXY"
]

# 데이터 캐싱 (로딩 속도 향상 및 yfinance 호출 제한 방지, 1시간 유지)
@st.cache_data(ttl=3600)
def fetch_etf_data():
    results = []
    
    # 로딩 바 표시
    progress_text = "데이터를 불러오는 중입니다..."
    my_bar = st.progress(0, text=progress_text)
    
    total = len(TICKERS)
    for i, ticker in enumerate(TICKERS):
        try:
            df = yf.download(ticker, period="5y", interval="1d", progress=False)
            if df.empty or len(df) < 252: continue
            
            cp = float(df['Close'].iloc[-1])
            
            h_1y = float(df['High'].iloc[-252:].max()) if len(df) >= 252 else cp
            h_2y = float(df['High'].iloc[-504:].max()) if len(df) >= 504 else h_1y
            h_3y = float(df['High'].iloc[-756:].max()) if len(df) >= 756 else h_2y
            
            l_1y = float(df['Low'].iloc[-252:].min()) if len(df) >= 252 else cp
            l_2y = float(df['Low'].iloc[-504:].min()) if len(df) >= 504 else l_1y
            l_3y = float(df['Low'].iloc[-756:].min()) if len(df) >= 756 else l_2y
            
            m1 = round(((cp - h_1y) / h_1y) * 100, 1)
            m2 = round(((cp - h_2y) / h_2y) * 100, 1)
            m3 = round(((cp - h_3y) / h_3y) * 100, 1)
            
            g1 = round(((cp - l_1y) / l_1y) * 100, 1)
            g2 = round(((cp - l_2y) / l_2y) * 100, 1)
            g3 = round(((cp - l_3y) / l_3y) * 100, 1)
            
            if m1 <= -60.0 or g1 <= 15.0:
                score, status = 3, "🔥 적극매수"
            elif m1 <= -30.0 or g1 <= 40.0:
                score, status = 2, "🟢 매수"
            else:
                score, status = 1, "🟡 진입"
            
            results.append({
                "ETF": ticker, "Price ($)": round(cp, 2), "Status": status, "Score": score,
                "MDD 1Y (%)": m1, "MDD 2Y (%)": m2, "MDD 3Y (%)": m3,
                "Gain 1Y (%)": g1, "Gain 2Y (%)": g2, "Gain 3Y (%)": g3
            })
        except:
            pass
        
        # 프로그레스 바 업데이트
        my_bar.progress((i + 1) / total, text=f"{ticker} 분석 중... ({i+1}/{total})")
        
    my_bar.empty() # 완료 후 로딩바 숨김
    
    if results:
        # Score 기준으로 정렬 후 반환
        results.sort(key=lambda x: x['Score'], reverse=True)
        return pd.DataFrame(results).drop(columns=['Score']) # Score 컬럼은 웹에서 숨김
    return pd.DataFrame()

# UI 구성
ny_tz = pytz.timezone('America/New_York')
current_ny_time = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')

st.title("🚀 통합 ETF 리포트")
st.caption(f"뉴욕 시간 기준 업데이트: {current_ny_time}")

# 데이터 불러오기 및 화면 출력
df = fetch_etf_data()

if not df.empty:
    # 데이터프레임을 인터랙티브한 표로 출력
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.error("데이터를 불러오지 못했습니다.")
