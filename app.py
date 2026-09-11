import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 페이지 설정
st.set_page_config(
    page_title="Wharton Pro Investment Dashboard", 
    page_icon="📈", 
    layout="wide"
)

# 2. 헤더 디자인
st.title("📈 Wharton Investment Competition & Stock Analysis Dashboard")
st.caption("Wharton Global High School Investment Competition - Comprehensive Portfolio Strategy Tool")
st.markdown("---")

# 3. 사이드바 - 카테고리/섹터별 세분화 데이터베이스
TICKER_CATEGORIES = {
    "🇺🇸 테크 & 빅테크": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "TSM"],
    "📊 지수 및 대표 ETF": ["SPY", "QQQ", "DIA", "IWM", "SOXX"],
    "🏦 금융 & 소비재": ["JPM", "BAC", "V", "WMT", "COST", "NKE", "SBUX", "DIS", "NFLX"],
    "🛡️ 안전자산 & 배당": ["TLT", "IEF", "AGG", "GLD", "SLV", "SCHD"],
    "🌐 전체 목록에서 조합": ["AAPL", "NVDA", "TSLA", "SPY", "TLT", "GLD", "MSFT", "GOOGL", "AMZN", "QQQ", "SCHD"]
}

st.sidebar.header("🗂️ 자산 카테고리 선택")

# 채팅방 선택처럼 카테고리 선택 메뉴 제공
selected_category = st.sidebar.radio(
    "분석할 시장 테마를 선택하세요",
    options=list(TICKER_CATEGORIES.keys())
)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 종목 선택 (클릭으로 켜기/끄기)")

# 해당 카테고리의 종목 목록을 사이드바에 쭉 표시
available_tickers = TICKER_CATEGORIES[selected_category]
selected_tickers = []

# 각 종목별 체크박스 생성
for ticker in available_tickers:
    # 기본으로 몇 개 종목은 선택 상태로 지정
    is_default = ticker in ["AAPL", "NVDA", "TSLA", "SPY", "TLT", "GLD"]
    if st.sidebar.checkbox(ticker, value=is_default, key=f"chk_{ticker}"):
        selected_tickers.append(ticker)

st.sidebar.markdown("---")
start_date = st.sidebar.date_input("시작일", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료일", pd.to_datetime("today"))

ticker_list = list(set(selected_tickers))

if ticker_list:
    with st.spinner('금융 데이터 및 주가를 불러오는 중입니다...'):
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

        # 4. 상단 카드 (선택한 종목 최신 시세)
        st.subheader("📌 선택 종목 최신 시세 및 변동률")
        grid_cols = st.columns(min(len(valid_tickers), 5))
        for idx, ticker in enumerate(valid_tickers):
            col_target = grid_cols[idx % 5]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                col_target.metric(label=ticker, value=f"${curr_p:.2f}", delta=f"{chg:.2f}%")

        st.markdown("---")

        # 5. 5개 메인 분석 탭 구성
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 상대 수익률 비교", 
            "🎯 포트폴리오 시뮬레이터", 
            "🔍 개별 종목 기술적 분석 (SMA/RSI)", 
            "🛡️ 리스크 및 상관관계 (MDD)", 
            "📝 대회 제출용 보고서 생성"
        ])

        # TAB 1: 상대 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점(100 기준) 상대 수익률 비교")
            st.caption("왼쪽 사이드바에서 선택한 종목들의 시작가를 100으로 설정하여 성과를 비교합니다.")
            norm_data = (valid_data / valid_data.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 비중 시뮬레이터
        with tab2:
            st.markdown("### 🎯 내 포트폴리오 비중(%) 설정 및 백테스트")
            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, int(100 / len(valid_tickers)), step=5, key=f"w_{ticker}")
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("최소 하나 이상의 종목 비중을 설정해 주세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                st.info(f"💡 설정된 총 비중: **{total_weight}%** (자동 100% 표준화 적용)")

                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                st.markdown("#### 🚀 조합된 포트폴리오 성과 추이")
                st.line_chart(port_cum_ret, use_container_width=True)

                # 메트릭 계산
                tot_return = (port_cum_ret.iloc[-1] - 100)
                ann_ret = port_daily_ret.mean() * 252 * 100
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                
                # MDD 계산
                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max
                mdd = drawdown.min() * 100

                r1, r2, r3, r4 = st.columns(4)
                r1.metric("총 수익률", f"{tot_return:.2f}%")
                r2.metric("연간 변동성 (위험도)", f"{ann_vol:.2f}%")
                r3.metric("샤프 지수 (Sharpe)", f"{sharpe:.2f}")
                r4.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

        # TAB 3: 개별 종목 기술적 분석
        with tab3:
            st.markdown("### 🔍 개별 종목 심층 분석 (이동평균선 & RSI)")
            selected_ticker = st.selectbox("분석할 종목을 선택하세요", valid_tickers)
            
            stock_series = valid_data[selected_ticker]
            
            # 이동평균선 계산
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 이동평균선 (SMA 50)": sma_50,
                "200일 이동평균선 (SMA 200)": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 이동평균선 차트")
            st.line_chart(chart_df, use_container_width=True)

            # RSI 계산 (14일 기준)
            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} RSI (상대강도지수): **{latest_rsi:.1f}**")
            if latest_rsi >= 70:
                st.warning("⚠️ **과매수 구간 (RSI ≥ 70):** 주가가 단기적으로 과도하게 상승했을 가능성이 있습니다.")
            elif latest_rsi <= 30:
                st.success("💡 **과매도 구간 (RSI ≤ 30):** 주가가 단기적으로 과도하게 하락하여 반등 가능성이 있습니다.")
            else:
                st.info("ℹ️ **중립 구간 (30 < RSI < 70):** 안정적인 주가 흐름을 유지 중입니다.")

        # TAB 4: 리스크 & 상관관계 분석
        with tab4:
            st.markdown("### 🛡️ 자산 간 상관관계 및 리스크 표")
            st.caption("상관계수가 낮은 자산들을 조합해야 포트폴리오 위험이 효과적으로 분산됩니다.")
            
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
            st.markdown("#### 🔗 자산 간 상관관계 행렬 (Correlation Matrix)")
            st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)

            st.markdown("#### 📋 종목별 리스크 지표")
            ind_ann_ret = daily_returns.mean() * 252 * 100
            ind_ann_vol = daily_returns.std() * np.sqrt(252) * 100
            rf = 4.0
            ind_sharpe = (ind_ann_ret - rf) / ind_ann_vol
            
            ind_mdd = {}
            for t in valid_tickers:
                t_cum = (1 + daily_returns[t]).cumprod()
                t_max = t_cum.cummax()
                ind_mdd[t] = ((t_cum - t_max) / t_max).min() * 100

            summary_df = pd.DataFrame({
                "연간 예상 수익률 (%)": ind_ann_ret.map("{:.2f}%".format),
                "연간 변동성 (%)": ind_ann_vol.map("{:.2f}%".format),
                "샤프 지수 (Sharpe)": ind_sharpe.map("{:.2f}".format),
                "최대 낙폭 (MDD %)": pd.Series(ind_mdd).map("{:.2f}%".format)
            })

            st.dataframe(summary_df.T, use_container_width=True)

        # TAB 5: 와튼 대회 보고서 자동 생성
        with tab5:
            st.markdown("### 📝 Wharton Competition Executive Summary Generator")
            st.caption("탭 2에서 설정한 자산 비중과 백테스트 결과를 바탕으로 제출용 보고서 요약문을 자동 생성합니다.")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("보고서 언어 선택", ["한국어", "English"])
                
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                if lang == "한국어":
                    report_text = f"""
### 📄 와튼 대회 포트폴리오 전략 요약서

**1. 자산 배분 구조 (Asset Allocation)**
본 포트폴리오는 위험 분산과 안정적 수익 달성을 위해 다음과 같이 자산을 배분하였습니다:
- **구성 종목 및 비중:** {weight_summary}

**2. 백테스팅 성과 및 위험 분석 (Performance & Risk)**
- **포트폴리오 총 수익률:** {tot_return:.2f}%
- **연간 변동성(위험도):** {ann_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {sharpe:.2f} (무위험 수익률 4% 기준)
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 투자 핵심 논리 (Investment Thesis)**
본 포트폴리오는 {valid_tickers[0]} 등의 성장 자산을 통해 수익성을 확보하는 동시에, 자산 간 상관관계를 고려하여 최대 낙폭({mdd:.2f}%)을 효과적으로 통제하도록 설계되었습니다. 특히 샤프 지수 {sharpe:.2f}를 기록하며 위험 대비 우수한 수익 효율성을 입증하였습니다.
                    """
                else:
                    report_text = f"""
### 📄 Wharton Investment Strategy Executive Summary

**1. Asset Allocation Breakdown**
To optimize risk-adjusted returns, the portfolio is allocated as follows:
- **Target Allocation:** {weight_summary}

**2. Historical Performance & Risk Metrics**
- **Total Portfolio Return:** {tot_return:.2f}%
- **Annualized Volatility:** {ann_vol:.2f}%
- **Sharpe Ratio:** {sharpe:.2f} (Assumed Risk-Free Rate: 4.0%)
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Investment Thesis**
This strategy strikes a balance between capital growth and risk mitigation. By combining growth assets with defensive instruments, the portfolio successfully controlled maximum drawdown to {mdd:.2f}% while maintaining a robust Sharpe ratio of {sharpe:.2f}.
                    """
                
                st.markdown(report_text)
                st.text_area("텍스트 복사용 상자", report_text, height=200)
            else:
                st.warning("탭 2(포트폴리오 시뮬레이터)에서 종목 비중을 설정해 주세요.")

        # 다운로드 버튼
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 주가 데이터 CSV 다운로드", 
            data=csv_data, 
            file_name="wharton_pro_data.csv", 
            mime="text/csv"
        )
    else:
        st.error("선택한 종목 중 불러올 수 있는 주가 데이터가 없습니다. 종목을 하나 이상 선택해 주세요.")
else:
    st.warning("왼쪽 사이드바에서 분석할 종목 체크박스를 하나 이상 선택해 주세요.")
