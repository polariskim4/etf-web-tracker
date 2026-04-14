import streamlit as st
import yfinance as yf
import pandas as pd

# ... (페이지 설정 및 TICKERS 리스트는 기존과 동일) ...

@st.cache_data(ttl=86400)
def get_etf_metadata():
    meta = {}
    for t in TICKERS:
        # 기본값 설정
        meta[t] = {"lev": "알수없음", "inv": "알수없음", "aum": 0, "desc": "-"}
        try:
            info = yf.Ticker(t).info
            name = info.get('longName', '')
            
            # 1. 인버스/레버리지 판단 logic
            name_upper = name.upper()
            inv = "YES" if any(w in name_upper for w in ["INVERSE", "SHORT", "BEAR", "REVERSE"]) else "NO"
            if any(w in name_upper for w in ["3X", "TRIPLE"]): lev = "3x"
            elif any(w in name_upper for w in ["2X", "DOUBLE", "ULTRA"]): lev = "2x"
            else: lev = "1x"
            
            # 2. AUM 단위를 Million으로 미리 변환 (숫자로 저장해야 소팅이 잘 됨)
            raw_aum = info.get('totalAssets', 0)
            aum_mm = round(raw_aum / 1_000_000, 1) if raw_aum else 0
            
            meta[t] = {
                "lev": lev, 
                "inv": inv, 
                "aum": aum_mm, 
                "desc": name  # 종목 설명(Full Name) 저장
            }
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
            if df.empty: continue
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

            t_meta = meta_dict.get(ticker_symbol)

            # 결과 리스트 생성 (순서 주의: ETF -> 종목설명 -> 레버리지)
            results.append({
                "신호": sig,
                "ETF": ticker_symbol,
                "종목설명": t_meta["desc"],  # 새 칼럼 추가
                "레버리지": t_meta["lev"],
                "인버스": t_meta["inv"],
                "현재가": cp,
                "MDD": mdd,
                "회복률": rec,
                "기간변화": chg,
                "점수": score,
                "자산규모($MM)": t_meta["aum"]  # 변환된 AUM
            })
        except: continue
    
    return pd.DataFrame(results)

def display_dashboard(years):
    df = fetch_etf_data(years)
    if df.empty:
        st.warning(f"{years}년 기간에 대한 데이터를 불러오지 못했습니다.")
        return

    # ... (필터 UI 부분은 기존과 동일) ...

    # 정렬 및 화면 표시
    st.dataframe(
        final_df.sort_values("점수", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "현재가": st.column_config.NumberColumn("현재가", format="$%.2f"),
            "MDD": st.column_config.NumberColumn("MDD", format="%.1f%%"),
            "회복률": st.column_config.NumberColumn("회복률", format="%.1f%%"),
            "기간변화": st.column_config.NumberColumn("기간변화", format="%.1f%%"),
            "자산규모($MM)": st.column_config.NumberColumn("자산규모($MM)", format="$%.1f MM"), # 소수점 한자리 표시
            "종목설명": st.column_config.TextColumn("종목설명", width="large") # 텍스트가 기므로 폭을 넓게 설정
        }
    )

# ... (탭 구성 및 호출 부분은 기존과 동일) ...
