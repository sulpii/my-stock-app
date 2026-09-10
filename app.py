import streamlit as st
import yfinance as yf

# 앱 제목
st.title("📈 와튼 대회용 나만의 주식 분석 앱")

# 주식 종목 입력창
ticker = st.text_input("분석할 주식 코드를 입력하세요 (예: AAPL, TSLA, TLT)", "AAPL")

if st.button("주식 데이터 가져오기"):
    data = yf.Ticker(ticker)
    info = data.info
    
    # 주요 지표 카드 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="현재 가격", value=f"${info.get('currentPrice', 'N/A')}")
    with col2:
        st.metric(label="PER (저평가 지표)", value=f"{info.get('trailingPE', 'N/A')}")
    
    # 주가 그래프 그리기
    st.subheader("최근 1년 주가 추이")
    hist = data.history(period="1y")
    st.line_chart(hist['Close'])
