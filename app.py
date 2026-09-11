import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 페이지 기본 설정
st.set_page_config(page_title="Wharton Investment Dashboard", page_icon="📈", layout="wide")

# 타이틀 및 헤더 디자인
st.title("📈 Wharton High School Investment Competition Dashboard")
st.markdown("---")

# 시드바: 분석할 종목 선택
st.sidebar.header("🔍 분석 설정")
tickers_input = st.sidebar.text_input("분석할 종목 코드를 입력하세요 (공백으로 구분)", "AAPL TSLA TLT SPY")
start_date = st.sidebar.date_input("시작일", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료일", pd.to_datetime("today"))

ticker_list = [t.strip().upper() for t in tickers_input.split() if t.strip()]

if ticker_list:
    # 데이터 불러오기
    with st.spinner('주가 데이터를 가져오는 중입니다...'):
        data = yf.download(ticker_list, start=start_date, end=end_date)['Close']
        if isinstance(data, pd.Series):
            data = data.to_frame()

    # 1. 핵심 지표 카드 (Metric Cards)
    st.subheader("📌 주요 종목 최신 동향")
    cols = st.columns(len(ticker_list))
    for idx, ticker in enumerate(ticker_list):
        if ticker in data.columns:
            recent_price = data[ticker].dropna().iloc[-1]
            prev_price = data[ticker].dropna().iloc[-2]
            change = ((recent_price - prev_price) / prev_price) * 100
            cols[idx].metric(label=ticker, value=f"${recent_price:.2f}", delta=f"{change:.2f}%")

    st.markdown("---")

    # 2. 누적 수익률 비교 차트 (Normalized Growth)
    st.subheader("📊 종목별 누적 수익률 비교 (%)")
    st.caption("시작 시점(100%)을 기준으로 한 상대적 성과 비교입니다.")
    normalized_data = (data / data.iloc[0]) * 100
    st.line_chart(normalized_data)

    st.markdown("---")

    # 3. 리스크 & 변동성 분석 표 (Wharton 심사위원 핵심 평가 항목)
    st.subheader("🛡️ 리스크 및 변동성 분석 (Sharpe Ratio)")
    
    # 일일 수익률 계산
    daily_returns = data.pct_change().dropna()
    
    # 지표 계산 (연율화 기준)
    annual_return = daily_returns.mean() * 252 * 100
    annual_volatility = daily_returns.std() * np.sqrt(252) * 100
    risk_free_rate = 4.0 # 무위험 수익률 가정 (미국 국채 4%)
    sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility
    
    metrics_df = pd.DataFrame({
        "연간 예상 수익률 (%)": annual_return.map("{:.2f}%".format),
        "연간 변동성 (위험도 %)": annual_volatility.map("{:.2f}%".format),
        "샤프 지수 (Sharpe Ratio)": sharpe_ratio.map("{:.2f}".format)
    })
    
    st.dataframe(metrics_df.T, use_container_width=True)

    # 데이터 다운로드 버튼
    st.sidebar.markdown("---")
    csv_data = data.to_csv().encode('utf-8')
    st.sidebar.download_button("📥 주가 데이터 CSV 다운로드", data=csv_data, file_name="wharton_stock_data.csv", mime="text/csv")
else:
    st.warning("분석할 주식 코드를 입력해 주세요.")
