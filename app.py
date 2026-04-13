import streamlit as st
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

# 1. 페이지 설정 (넓은 화면 사용)
st.set_page_config(page_title="ETF MDD DashBoard", page_icon="📊", layout="wide")

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

# 3. 데이터 로드 (안정성 강화)
@st.cache_data(ttl=3600)
def fetch_etf_data():
    results = []
    my_bar = st.progress(0, text="실시간 시장 데이터 동기화 중...")
    
    for i, ticker in enumerate(TICKERS):
        try:
            df = yf.download(ticker, period="3y", interval="1d", progress=False)
            if df.empty or len(df) < 20: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            cp = float(df['Close'].iloc[-1])
            prev_cp = float(df['Close'].iloc[-2])
            day_change = ((cp - prev_cp) / prev_cp) * 100

            h_1y = float(df['High'].iloc[-252:].max()) if len(df) >= 252 else float(df['High'].max())
            l_1y = float(df['Low'].iloc[-252:].min()) if len(df) >= 252 else float(df['Low'].min())
            
            mdd = ((cp - h_1y) / h_1y) * 100
            gain = ((cp - l_1y) / l_1y) * 100
            
            # 신호 로직
            if mdd <= -60.0 or gain <= 15.0:
                status, color, score = "🔥 적극매수", "red", 3
            elif mdd <= -30.0 or gain <= 40.0:
                status, color, score = "🟢 매수", "green", 2
            else:
                status, color, score = "🟡 진입", "orange", 1
            
            results.append({
                "ETF": ticker, "Price": cp, "Change": day_change,
                "Status": status, "MDD": mdd, "Gain": gain, 
                "High": h_1y, "Low": l_1y, "Score": score
            })
        except: continue
        my_bar.progress((i + 1) / len(TICKERS))
    
    my_bar.empty()
    return pd.DataFrame(results)

# 4. UI 레이아웃
st.title("📊 레버리지 ETF 실시간 MDD 대시보드")
ny_tz = pytz.timezone('America/New_York')
st.caption(f"최종 업데이트 (NY): {datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M:%S')}")

data = fetch_etf_data()

if not data.empty:
    # 요약 메트릭
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("전체 종목", f"{len(data)}개")
    col2.metric("적극매수", f"{len(data[data['Score']==3)])}개", delta_color="inverse")
    col3.metric("매수 가능", f"{len(data[data['Score']==2])}개")
    col4.metric("관망/진입", f"{len(data[data['Score']==1])}개")

    st.divider()

    # 필터 및 정렬
    filter_col, sort_col = st.columns([2, 1])
    with filter_col:
        selected_status = st.multiselect("상태별 필터", ["🔥 적극매수", "🟢 매수", "🟡 진입"], default=["🔥 적극매수", "🟢 매수"])
    with sort_col:
        sort_by = st.selectbox("정렬 기준", ["MDD 낮은순", "수익률 높은순", "이름순"])

    # 데이터 필터링 및 정렬 적용
    filtered_df = data[data['Status'].isin(selected_status)]
    if sort_by == "MDD 낮은순":
        filtered_df = filtered_df.sort_values("MDD")
    elif sort_by == "수익률 높은순":
        filtered_df = filtered_df.sort_values("Change", ascending=False)

    # 5. 카드형 UI 출력 (가독성 핵심)
    rows = [filtered_df.iloc[i:i+4] for i in range(0, len(filtered_df), 4)]
    
    for row in rows:
        cols = st.columns(4)
        for i, (idx, item) in enumerate(row.iterrows()):
            with cols[i]:
                # 카드 스타일 적용
                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 15px; border-radius: 10px; background-color: #f9f9f9; margin-bottom: 10px;">
                    <h3 style="margin:0; color: #333;">{item['ETF']}</h3>
                    <p style="font-size: 20px; font-weight: bold; margin: 5px 0;">${item['Price']:.2f} <span style="font-size:14px; color:{'red' if item['Change']>=0 else 'blue'};">({item['Change']:+.2f}%)</span></p>
                    <hr style="margin: 10px 0;">
                    <p style="margin: 2px 0;"><b>상태:</b> {item['Status']}</p>
                    <p style="margin: 2px 0; color: red;"><b>MDD:</b> {item['MDD']:.1f}%</p>
                    <p style="margin: 2px 0; color: green;"><b>저점대비:</b> +{item['Gain']:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

else:
    st.warning("데이터를 불러오는 중입니다. 잠시만 기다려주세요.")
