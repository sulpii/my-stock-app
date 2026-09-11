import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(
    page_title="Wharton Investment Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# 2. 메인 타이틀
st.title("📈 Wharton Investment Competition Analysis Dashboard")
st.caption("Wharton Global High School Investment Competition - Portfolio Strategy Tool")
st.markdown("---")

# 3. 사이드바 입력창
st.sidebar.header("⚙️ 분석 설정")
default_tickers = "AAPL TSLA SPY TLT GLD"
tickers_input = st.sidebar.text_input("분석할 종목 코드를 입력하세요 (공백으로 구분)", default_tickers)
start_date = st.sidebar.date_input("시작일", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료일", pd.to_datetime("today"))

ticker_list = [t.strip().upper() for t in tickers_input.split() if t.strip()]

if ticker_list:
    # 데이터 다운로드
    with st.spinner('금융 데이터를 가져오는 중입니다...'):
        try:
            raw_data = yf.download(ticker_list, start=start_date, end=end_date)
            if 'Close' in raw_data:
                data = raw_data['Close']
            else:
                data = raw_data
            
            if isinstance(data, pd.Series):
                data = data.to_frame()
                
            data = data.dropna(how='all', axis=1)
        except Exception as e:
            st.error("데이터 수집 중 오류가 발생했습니다.")
            data = pd.DataFrame()

    valid_tickers = [t for t in ticker_list if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()

        # 4. 상단 카드 (최신 동향) - 가독성을 높이기 위해 4개씩 줄바꿈 렌더링
        st.subheader("📌 주요 자산 최신 가격 현황")
        grid_cols = st.columns(4)
        for idx, ticker in enumerate(valid_tickers):
            col_target = grid_cols[idx % 4]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                col_target.metric(label=ticker, value=f"${curr_p:.2f}", delta=f"{chg:.2f}%")

        st.markdown("---")

        # 5. 탭 구성 (가독성 향상)
        tab1, tab2, tab3 = st.tabs(["📊 상대 수익률 비교", "⚖️ 포트폴리오 비중 시뮬레이션", "🛡️ 리스크 & Sharpe Ratio"])

        # TAB 1: 누적 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점(100 기준) 상대 성과 비교")
            st.caption("모든 자산의 시작가를 100으로 기준화하여 종목 간 상대적인 성장률을 보여줍니다.")
            norm_data = (valid_data / valid_data.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 비중 시뮬레이터 (슬라이더)
        with tab2:
            st.markdown("### 🎯 내 포트폴리오 자산 배분 (Asset Allocation)")
            st.write("각 종목의 비중(%)을 설정하세요.")

            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, int(100 / len(valid_tickers)), step=5)
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("최소 하나 이상의 종목 비중을 0% 이상으로 설정해 주세요.")
            else:
                # 비중 정규화 (합이 100%가 되도록 조정)
                norm_weights = np.array(weights) / total_weight
                st.info(f"💡 현재 설정된 총 비중 합계: **{total_weight}%** (자동 100% 표준화 반영)")

                # 포트폴리오 일일 수익률 계산
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                
                # 포트폴리오 누적 수익률
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                st.markdown("#### 🚀 조합된 포트폴리오 성과 추이")
                st.line_chart(port_cum_ret, use_container_width=True)

                # 포트폴리오 요약 수치
                tot_return = ((port_cum_ret.iloc[-1] - 100))
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                rf = 4.0
                ann_ret = port_daily_ret.mean() * 252 * 100
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0

                res_col1, res_col2, res_col3 = st.columns(3)
                res_col1.metric("포트폴리오 총 수익률", f"{tot_return:.2f}%")
                res_col2.metric("포트폴리오 연간 변동성", f"{ann_vol:.2f}%")
                res_col3.metric("포트폴리오 샤프 지수 (Sharpe)", f"{sharpe:.2f}")

        # TAB 3: 개별 리스크 분석
        with tab3:
            st.markdown("### 🛡️ 종목별 위험 대비 수익률 상세 (Sharpe Ratio)")
            
            daily_returns = valid_data.pct_change().dropna()
            ann_ret = daily_returns.mean() * 252 * 100
            ann_vol = daily_returns.std() * np.sqrt(252) * 100
            rf = 4.0
            sharpe = (ann_ret - rf) / ann_vol

            summary_df = pd.DataFrame({
                "연간 예상 수익률 (%)": ann_ret.map("{:.2f}%".format),
                "연간 변동성 (위험도 %)": ann_vol.map("{:.2f}%".format),
                "샤프 지수 (Sharpe Ratio)": sharpe.map("{:.2f}".format)
            })

            st.dataframe(summary_df.T, use_container_width=True)

        # 다운로드 버튼
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 주가 데이터 CSV 다운로드", 
            data=csv_data, 
            file_name="wharton_portfolio_data.csv", 
            mime="text/csv"
        )
    else:
        st.error("입력하신 종목의 데이터를 찾을 수 없습니다. 올바른 주식 티커를 입력해 주세요.")
else:
    st.warning("분석할 주식 코드를 입력해 주세요.")
