import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# 1. 페이지 레이아웃 및 테마 설정
st.set_page_config(
    page_title="Wharton Investment Competition & Terminal", 
    page_icon="🏛️", 
    layout="wide"
)

# Custom CSS for Professional UI Design
st.markdown("""
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0px; }
    .sub-header { font-size: 1rem; color: #6B7280; margin-bottom: 25px; }
    .stMetric { background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 2. 헤더 섹션
st.markdown('<p class="main-header">🏛️ Wharton Investment Competition Portfolio Analytics Terminal</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">글로벌 11대 산업 섹터 및 주요 ETF 통합 백테스팅 & 리스크 분석 시스템</p>', unsafe_allow_html=True)

# 3. 글로벌 11대 GICS 섹터 및 자산군 완벽 데이터베이스
SECTOR_DATABASE = {
    "🖥️ Information Technology (IT & 반도체)": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "ORCL", "CSCO", "CRM", "INTC", "TSM", "ASML"],
    "🌐 Communication Services (통신 & 미디어)": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ", "T", "CMCSA"],
    "🛍️ Consumer Discretionary (임의소비재 & 전기차)": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX", "BKNG", "LOW"],
    "🛒 Consumer Staples (필수소비재)": ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL"],
    "🏥 Health Care (헬스케어 & 제약)": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE", "TMO", "AMGN"],
    "🏦 Financials (금융 & 투자은행)": ["BRK-B", "JPM", "V", "MA", "BAC", "GS", "MS", "WFC", "C"],
    "⚙️ Industrials (산업재 & 방산)": ["CAT", "GE", "BA", "HON", "LMT", "RTX", "UPS", "DE"],
    "⚡ Energy (에너지 & 석유)": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "VLO"],
    "⛏️ Materials (소재 & 원자재)": ["LIN", "APD", "NEM", "FCX", "ECL", "SHW"],
    "💡 Utilities (유틸리티 & 전력)": ["NEE", "DUK", "SO", "AEP", "SRE"],
    "🏢 Real Estate (부동산 & 리츠)": ["PLD", "AMT", "EQIX", "SPG", "O", "CCI"],
    "📊 Index & Asset Class ETFs (지수 및 원자재)": ["SPY", "QQQ", "DIA", "IWM", "SOXX", "TLT", "IEF", "GLD", "SLV", "SCHD"]
}

# 4. 프로페셔널 사이드바 설계
st.sidebar.markdown("### 🗂️ 자산군 및 산업 섹터 선택")

# 섹터 선택
selected_sector = st.sidebar.selectbox(
    "산업 섹터(GICS Sector)를 선택하세요",
    options=list(SECTOR_DATABASE.keys()),
    index=0
)

# 선택된 섹터의 종목 목록 추출 및 멀티 셀렉트 박스 구축
sector_tickers = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("### 📌 포트폴리오 구성 종목 선택")
selected_tickers = st.sidebar.multiselect(
    "종목을 검색하거나 선택/제거하세요 (직접 입력 가능)",
    options=list(set(sector_tickers + ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "TSLA", "SPY", "TLT", "GLD"])),
    default=sector_tickers[:4] # 초기 기본값 4개 선택
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 백테스트 기간 설정")
start_date = st.sidebar.date_input("시작일", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("종료일", pd.to_datetime("today"))

# 실행 검증
ticker_list = list(set(selected_tickers))

if ticker_list:
    with st.spinner('금융 데이터 단말기 연결 중... 주가 데이터를 수집합니다.'):
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

        # 5. 상단 라이브 틱스 카드 UI
        st.markdown("##### 📌 선택된 종목 시세 요약")
        metric_cols = st.columns(min(len(valid_tickers), 5))
        for idx, ticker in enumerate(valid_tickers):
            col_target = metric_cols[idx % 5]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                col_target.metric(label=ticker, value=f"${curr_p:.2f}", delta=f"{chg:.2f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # 6. 메인 분석 탭 (프로페셔널 구획)
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 상대 수익률 비교 분석", 
            "🎯 포트폴리오 비중 백테스터", 
            "🔍 기술적 지표 (SMA / RSI)", 
            "🛡️ 리스크 & 상관계수 분석", 
            "📄 와튼 대회 제출용 Report Generator"
        ])

        # TAB 1: 상대 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점 기준(100) 성과 트렌드 비교")
            st.caption("선택한 종목들의 시작가를 100으로 정규화하여 기간 내 상대적 우위를 분석합니다.")
            norm_data = (valid_data / valid_data.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 백테스터
        with tab2:
            st.markdown("### 🎯 포트폴리오 자산 배분 비중(%) 설정")
            st.caption("각 자산의 투자 비중을 조정하여 최적의 Risk-Adjusted Return을 탐색합니다.")
            
            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, int(100 / len(valid_tickers)), step=5, key=f"w_{ticker}")
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("⚠️ 최소 1개 이상의 종목 비중을 설정하세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                st.info(f"💡 현재 설정된 총 비중: **{total_weight}%** (계산 시 자동으로 100% 표준화 적용)")

                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                st.markdown("#### 🚀 합성 포트폴리오 누적 성과 추이")
                st.line_chart(port_cum_ret, use_container_width=True)

                # 성과 지표 산출
                tot_return = (port_cum_ret.iloc[-1] - 100)
                ann_ret = port_daily_ret.mean() * 252 * 100
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                
                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max
                mdd = drawdown.min() * 100

                st.markdown("#### 📊 핵심 포트폴리오 리스크 & 성과 지표")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("총 누적 수익률", f"{tot_return:.2f}%")
                m2.metric("연간 변동성 (위험도)", f"{ann_vol:.2f}%")
                m3.metric("샤프 지수 (Sharpe Ratio)", f"{sharpe:.2f}")
                m4.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

        # TAB 3: 기술적 분석
        with tab3:
            st.markdown("### 🔍 종목별 기술적 지표 심층 분석")
            selected_ticker = st.selectbox("분석할 개별 종목을 선택하세요", valid_tickers)
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 이동평균 (SMA 50)": sma_50,
                "200일 이동평균 (SMA 200)": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 가격 추이 및 이동평균선")
            st.line_chart(chart_df, use_container_width=True)

            # RSI 계산
            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} RSI (14일 상대강도지수): **{latest_rsi:.1f}**")
            if latest_rsi >= 70:
                st.warning("⚠️ **과매수 (Overbought) 상태:** 기술적 단기 조정 가능성이 존재합니다.")
            elif latest_rsi <= 30:
                st.success("💡 **과매도 (Oversold) 상태:** 기술적 단기 반등 가능성이 존재합니다.")
            else:
                st.info("ℹ️ **중립 (Neutral) 상태:** 안정적인 추세를 유지 중입니다.")

        # TAB 4: 리스크 & 상관관계 분석
        with tab4:
            st.markdown("### 🛡️ 자산간 상관관계 및 상세 위험 지표")
            st.caption("상관계수가 낮거나 음의 값을 갖는 자산을 조합하는 것이 포트폴리오 위험 분산의 핵심입니다.")
            
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
            st.markdown("#### 🔗 상관관계 행렬 (Correlation Matrix)")
            st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)

            st.markdown("#### 📋 개별 자산 리스크 통계")
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
            st.markdown("### 📄 Wharton Investment Strategy Executive Summary")
            st.caption("탭 2에서 구축한 포트폴리오 데이터를 기반으로 와튼 투자 대회 제출용 요약문이 자동 작성됩니다.")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("보고서 언어 선택", ["한국어 (Korean)", "English (영어)"])
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                if "한국어" in lang:
                    report_text = f"""
### 📄 [보고서] 와튼 투자 대회 포트폴리오 전략 요약서

**1. 자산 배분 전략 (Asset Allocation)**
본 전략은 위험 대비 수익률(Risk-Adjusted Return) 최적화를 목표로 구성되었습니다:
- **선택 섹터:** {selected_sector}
- **목표 자산 비중:** {weight_summary}

**2. 백테스팅 성과 및 리스크 분석 (Quantitative Metrics)**
- **포트폴리오 총 누적 수익률:** {tot_return:.2f}%
- **연간 변동성 (위험도):** {ann_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {sharpe:.2f} (무위험 수익률 4.0% 적용)
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 투자 논리 및 핵심 결론 (Investment Thesis)**
본 포트폴리오는 상관관계 분석을 바탕으로 설계되어 market downturn 상황에서도 최대 낙폭을 {mdd:.2f}%로 제한했습니다. 동시에 샤프 지수 {sharpe:.2f}를 달성하여 우수한 자본 보전 및 성장 역량을 입증합니다.
                    """
                else:
                    report_text = f"""
### 📄 Wharton Investment Strategy Executive Summary

**1. Strategic Asset Allocation**
Designed to maximize risk-adjusted returns through diversified multi-asset exposure:
- **Selected Industry Sector:** {selected_sector}
- **Target Portfolio Weight:** {weight_summary}

**2. Historical Performance & Quantitative Metrics**
- **Total Portfolio Return:** {tot_return:.2f}%
- **Annualized Volatility:** {ann_vol:.2f}%
- **Sharpe Ratio:** {sharpe:.2f} (Assumed Risk-Free Rate: 4.0%)
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Investment Thesis**
By deploying low-correlation assets within the {selected_sector} ecosystem, the portfolio controls Maximum Drawdown to {mdd:.2f}% while maintaining a robust Sharpe Ratio of {sharpe:.2f}.
                    """
                
                st.markdown(report_text)
                st.text_area("텍스트 복사용 메임 상자", report_text, height=220)
            else:
                st.warning("⚠️ 탭 2(포트폴리오 백테스터)에서 종목 비중을 먼저 설정해 주세요.")

        # 사이드바 데이터 다운로드 기능
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 분석 데이터 CSV 다운로드", 
            data=csv_data, 
            file_name="wharton_portfolio_data.csv", 
            mime="text/csv"
        )
    else:
        st.error("데이터를 가져올 수 있는 종목이 선택되지 않았습니다. 사이드바에서 종목을 추가해 보세요.")
else:
    st.warning("👈 왼쪽 사이드바에서 분석할 종목을 선택하거나 직접 입력해 주세요.")
