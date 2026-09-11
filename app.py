import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 프로페셔널 테마 설정
st.set_page_config(
    page_title="Wharton Portfolio Analytics Terminal Pro", 
    page_icon="🏛️", 
    layout="wide"
)

# Custom CSS for Professional Terminal Styling
st.markdown("""
    <style>
    .main-header { font-size: 2.1rem; font-weight: 700; color: #0F172A; margin-bottom: 0px; }
    .sub-header { font-size: 0.95rem; color: #475569; margin-bottom: 20px; }
    
    /* 사이드바 체크박스 영역 스크롤 고정 */
    .checkbox-container {
        max-height: 240px;
        overflow-y: auto;
        border: 1px solid #E2E8F0;
        padding: 10px;
        border-radius: 8px;
        background-color: #F8FAFC;
        margin-bottom: 15px;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 헤더
st.markdown('<p class="main-header">🏛️ Wharton Investment Competition Terminal Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">글로벌 11대 GICS 산업 섹터 & 벤치마크(S&P 500) 알파/낙폭 심층 분석 단말기</p>', unsafe_allow_html=True)

# 3. 사전 정의된 완벽 종목 데이터베이스
SECTOR_DATABASE = {
    "🇺🇸 IT & 반도체": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM", "ASML", "INTC"],
    "🌐 통신 & 미디어": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ"],
    "🛍️ 임의소비재 & 전기차": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
    "🛒 필수소비재": ["PG", "KO", "PEP", "WMT", "COST"],
    "🏥 헬스케어 & 제약": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE"],
    "🏦 금융 & 투자": ["BRK-B", "JPM", "V", "MA", "BAC", "GS"],
    "⚙️ 산업재 & 방산": ["CAT", "GE", "BA", "HON", "LMT", "RTX"],
    "⚡ 에너지 & 원자재": ["XOM", "CVX", "LIN", "GLD", "SLV", "USO"],
    "📊 주요 대표 ETF": ["SPY", "QQQ", "DIA", "IWM", "TLT", "SCHD"]
}

# 4. 사이드바 - 100% 클릭 전용 & 컴팩트 레이아웃
st.sidebar.markdown("### 🗂️ 1. 시장 섹터 선택")
selected_sector = st.sidebar.selectbox(
    "분석할 카테고리를 선택하세요",
    options=list(SECTOR_DATABASE.keys()),
    index=0
)

default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 2. 종목 선택 (클릭 ON/OFF)")
st.sidebar.caption("터치/클릭으로 포트폴리오를 구성하세요.")

# 스크롤 박스로 감싸진 선택창
selected_tickers = []
with st.sidebar.container():
    st.markdown('<div class="checkbox-container">', unsafe_allow_html=True)
    for ticker in default_pool:
        is_default = ticker in default_pool[:4]
        if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_{selected_sector}_{ticker}"):
            selected_tickers.append(ticker)
    st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 백테스트 기간 (Quick Select)")

# 퀵 기간 선택 버튼
today = datetime.today()
col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)

if 'start_d' not in st.session_state:
    st.session_state.start_d = datetime(2023, 1, 1)

if col_q1.button("YTD"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.sidebar.date_input("시작일", st.session_state.start_d)
end_date = st.sidebar.date_input("종료일", today)

# SPY(S&P 500) 지수 자동 포함
analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('금융 데이터 수집 중...'):
        try:
            raw_data = yf.download(analysis_tickers, start=start_date, end=end_date)
            data = raw_data['Close'] if 'Close' in raw_data else raw_data
            if isinstance(data, pd.Series):
                data = data.to_frame()
            data = data.dropna(how='all', axis=1)
        except Exception:
            st.error("데이터 수집 중 오류가 발생했습니다.")
            data = pd.DataFrame()

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # 상단 시세 라이브 카드
        st.markdown("##### 📌 선택 종목 실시간 시세 현황")
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

        # 5. 메인 분석 탭
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 상대 수익률 & SPY 비교", 
            "🎯 포트폴리오 백테스터 & Risk", 
            "🔍 종목 기술적 분석 (SMA/RSI)", 
            "🛡️ 리스크 & 상관관계 행렬", 
            "📄 와튼 대회 제출용 보고서 생성"
        ])

        # TAB 1: 상대 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점(100) 기준 성과 비교")
            st.caption("시장 지수(SPY) 대비 내가 선택한 주식들의 상대적 상승률 흐름입니다.")
            
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['S&P 500 (SPY)'] = spy_data
                
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 백테스터 & Drawdown
        with tab2:
            st.markdown("### 🎯 포트폴리오 비중 설정 및 리스크 분석")
            
            # 1/N 자동 리밸런싱 버튼
            if st.button("⚖️ 모든 종목 비중 동일하게 맞추기 (1/N Auto-Rebalance)"):
                equal_w = int(100 / len(valid_tickers))
                for t in valid_tickers:
                    st.session_state[f"w_{t}"] = equal_w

            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    default_val = st.session_state.get(f"w_{ticker}", int(100 / len(valid_tickers)))
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, default_val, step=5, key=f"w_{ticker}")
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("⚠️ 최소 1개 이상의 종목 비중을 설정해 주세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                chart_df = pd.DataFrame({
                    "내 포트폴리오": port_cum_ret,
                    "벤치마크 (S&P 500)": spy_cum_ret
                }).dropna()

                st.markdown("#### 🚀 포트폴리오 VS S&P 500 누적 성과 추이")
                st.line_chart(chart_df, color=["#1E3A8A", "#9CA3AF"], use_container_width=True)

                # MDD 낙폭 그래프 계산
                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max * 100
                
                spy_cum_roll_max = spy_cum_ret.cummax()
                spy_drawdown = (spy_cum_ret - spy_cum_roll_max) / spy_cum_roll_max * 100

                dd_df = pd.DataFrame({
                    "포트폴리오 낙폭 (%)": drawdown,
                    "S&P 500 낙폭 (%)": spy_drawdown
                }).dropna()

                st.markdown("#### 📉 고점 대비 낙폭 추이 (Drawdown Risk)")
                st.caption("그래프가 0% 아래로 크게 내려갈수록 변동성 위험이 큰 구간입니다.")
                st.area_chart(dd_df, color=["#EF4444", "#CBD5E1"], use_container_width=True)

                # 주요 통계 계산
                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                mdd = drawdown.min()

                st.markdown("#### 📊 핵심 성과 및 알파(Alpha) 지표")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("총 수익률", f"{tot_return:.2f}%")
                m2.metric("초과 수익 (Alpha)", f"{alpha:+.2f}%", delta=f"{alpha:.2f}%p")
                m3.metric("연간 변동성", f"{ann_vol:.2f}%")
                m4.metric("샤프 지수 (Sharpe)", f"{sharpe:.2f}")
                m5.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

        # TAB 3: 기술적 분석
        with tab3:
            st.markdown("### 🔍 개별 종목 기술적 지표 분석")
            selected_ticker = st.selectbox("분석할 종목을 선택하세요", valid_tickers)
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 이동평균": sma_50,
                "200일 이동평균": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 가격 & 이동평균선")
            st.line_chart(chart_df, use_container_width=True)

            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} RSI (14일): **{latest_rsi:.1f}**")
            if latest_rsi >= 70:
                st.warning("⚠️ 과매수 상태 (RSI ≥ 70)")
            elif latest_rsi <= 30:
                st.success("💡 과매도 상태 (RSI ≤ 30)")
            else:
                st.info("ℹ️ 중립 상태 (30 < RSI < 70)")

        # TAB 4: 리스크 & 상관관계 분석
        with tab4:
            st.markdown("### 🛡️ 자산 간 상관관계 및 리스크 표")
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
            st.markdown("#### 🔗 자산 상관관계 행렬 (Correlation Matrix)")
            st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)

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
                "수익률 (%)": ind_ann_ret.map("{:.2f}%".format),
                "변동성 (%)": ind_ann_vol.map("{:.2f}%".format),
                "샤프 지수": ind_sharpe.map("{:.2f}".format),
                "최대 낙폭 (%)": pd.Series(ind_mdd).map("{:.2f}%".format)
            })

            st.dataframe(summary_df.T, use_container_width=True)

        # TAB 5: 와튼 대회 보고서 자동 생성
        with tab5:
            st.markdown("### 📄 Wharton Investment Executive Summary Generator")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("언어 선택", ["한국어", "English"])
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                if lang == "한국어":
                    report_text = f"""
### 📄 와튼 투자 대회 포트폴리오 요약 보고서

**1. 자산 배분 전략 (Asset Allocation)**
- **선택 카테고리:** {selected_sector}
- **자산 비중:** {weight_summary}

**2. 성과 및 리스크 측정 (Performance & Risk)**
- **포트폴리오 총 수익률:** {tot_return:.2f}%
- **시장 초과 수익률 (Alpha vs SPY):** {alpha:+.2f}%
- **연간 변동성 (Volatility):** {ann_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {sharpe:.2f}
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 투자 결론 (Thesis)**
본 포트폴리오는 S&P 500 지수 대비 {alpha:+.2f}%의 Alpha를 달성하며 시장 대비 뛰어난 성과를 기록했습니다. 샤프 지수 {sharpe:.2f}와 MDD {mdd:.2f}%를 통해 리스크 관리 우수성을 입증합니다.
                    """
                else:
                    report_text = f"""
### 📄 Wharton Investment Strategy Executive Summary

**1. Portfolio Construction**
- **Sector Focus:** {selected_sector}
- **Asset Allocation:** {weight_summary}

**2. Benchmark & Risk Performance**
- **Total Return:** {tot_return:.2f}%
- **Alpha (vs. S&P 500):** {alpha:+.2f}%
- **Annualized Volatility:** {ann_vol:.2f}%
- **Sharpe Ratio:** {sharpe:.2f}
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Key Takeaway**
The strategy generated an Alpha of {alpha:+.2f}% relative to the S&P 500, showing strong outperformance with robust downside risk control (MDD {mdd:.2f}%).
                    """
                
                st.markdown(report_text)
                st.text_area("보고서 텍스트 복사", report_text, height=220)
            else:
                st.warning("탭 2에서 종목 비중을 먼저 설정해 주세요.")

        # CSV 다운로드
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 분석 데이터 다운로드", 
            data=csv_data, 
            file_name="wharton_terminal_data.csv", 
            mime="text/csv"
        )
    else:
        st.error("선택한 종목의 주가를 불러올 수 없습니다.")
else:
    st.warning("👈 사이드바에서 분석할 종목을 선택해 주세요.")
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 프로페셔널 테마 설정
st.set_page_config(
    page_title="Wharton Portfolio Analytics Terminal Pro", 
    page_icon="🏛️", 
    layout="wide"
)

# Custom CSS for Professional Terminal Styling
st.markdown("""
    <style>
    .main-header { font-size: 2.1rem; font-weight: 700; color: #0F172A; margin-bottom: 0px; }
    .sub-header { font-size: 0.95rem; color: #475569; margin-bottom: 20px; }
    
    /* 사이드바 체크박스 영역 스크롤 고정 */
    .checkbox-container {
        max-height: 240px;
        overflow-y: auto;
        border: 1px solid #E2E8F0;
        padding: 10px;
        border-radius: 8px;
        background-color: #F8FAFC;
        margin-bottom: 15px;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 헤더
st.markdown('<p class="main-header">🏛️ Wharton Investment Competition Terminal Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">글로벌 11대 GICS 산업 섹터 & 벤치마크(S&P 500) 알파/낙폭 심층 분석 단말기</p>', unsafe_allow_html=True)

# 3. 사전 정의된 완벽 종목 데이터베이스
SECTOR_DATABASE = {
    "🇺🇸 IT & 반도체": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM", "ASML", "INTC"],
    "🌐 통신 & 미디어": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ"],
    "🛍️ 임의소비재 & 전기차": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
    "🛒 필수소비재": ["PG", "KO", "PEP", "WMT", "COST"],
    "🏥 헬스케어 & 제약": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE"],
    "🏦 금융 & 투자": ["BRK-B", "JPM", "V", "MA", "BAC", "GS"],
    "⚙️ 산업재 & 방산": ["CAT", "GE", "BA", "HON", "LMT", "RTX"],
    "⚡ 에너지 & 원자재": ["XOM", "CVX", "LIN", "GLD", "SLV", "USO"],
    "📊 주요 대표 ETF": ["SPY", "QQQ", "DIA", "IWM", "TLT", "SCHD"]
}

# 4. 사이드바 - 100% 클릭 전용 & 컴팩트 레이아웃
st.sidebar.markdown("### 🗂️ 1. 시장 섹터 선택")
selected_sector = st.sidebar.selectbox(
    "분석할 카테고리를 선택하세요",
    options=list(SECTOR_DATABASE.keys()),
    index=0
)

default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 2. 종목 선택 (클릭 ON/OFF)")
st.sidebar.caption("터치/클릭으로 포트폴리오를 구성하세요.")

# 스크롤 박스로 감싸진 선택창
selected_tickers = []
with st.sidebar.container():
    st.markdown('<div class="checkbox-container">', unsafe_allow_html=True)
    for ticker in default_pool:
        is_default = ticker in default_pool[:4]
        if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_{selected_sector}_{ticker}"):
            selected_tickers.append(ticker)
    st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 백테스트 기간 (Quick Select)")

# 퀵 기간 선택 버튼
today = datetime.today()
col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)

if 'start_d' not in st.session_state:
    st.session_state.start_d = datetime(2023, 1, 1)

if col_q1.button("YTD"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.sidebar.date_input("시작일", st.session_state.start_d)
end_date = st.sidebar.date_input("종료일", today)

# SPY(S&P 500) 지수 자동 포함
analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('금융 데이터 수집 중...'):
        try:
            raw_data = yf.download(analysis_tickers, start=start_date, end=end_date)
            data = raw_data['Close'] if 'Close' in raw_data else raw_data
            if isinstance(data, pd.Series):
                data = data.to_frame()
            data = data.dropna(how='all', axis=1)
        except Exception:
            st.error("데이터 수집 중 오류가 발생했습니다.")
            data = pd.DataFrame()

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # 상단 시세 라이브 카드
        st.markdown("##### 📌 선택 종목 실시간 시세 현황")
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

        # 5. 메인 분석 탭
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 상대 수익률 & SPY 비교", 
            "🎯 포트폴리오 백테스터 & Risk", 
            "🔍 종목 기술적 분석 (SMA/RSI)", 
            "🛡️ 리스크 & 상관관계 행렬", 
            "📄 와튼 대회 제출용 보고서 생성"
        ])

        # TAB 1: 상대 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점(100) 기준 성과 비교")
            st.caption("시장 지수(SPY) 대비 내가 선택한 주식들의 상대적 상승률 흐름입니다.")
            
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['S&P 500 (SPY)'] = spy_data
                
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 백테스터 & Drawdown
        with tab2:
            st.markdown("### 🎯 포트폴리오 비중 설정 및 리스크 분석")
            
            # 1/N 자동 리밸런싱 버튼
            if st.button("⚖️ 모든 종목 비중 동일하게 맞추기 (1/N Auto-Rebalance)"):
                equal_w = int(100 / len(valid_tickers))
                for t in valid_tickers:
                    st.session_state[f"w_{t}"] = equal_w

            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    default_val = st.session_state.get(f"w_{ticker}", int(100 / len(valid_tickers)))
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, default_val, step=5, key=f"w_{ticker}")
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("⚠️ 최소 1개 이상의 종목 비중을 설정해 주세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                chart_df = pd.DataFrame({
                    "내 포트폴리오": port_cum_ret,
                    "벤치마크 (S&P 500)": spy_cum_ret
                }).dropna()

                st.markdown("#### 🚀 포트폴리오 VS S&P 500 누적 성과 추이")
                st.line_chart(chart_df, color=["#1E3A8A", "#9CA3AF"], use_container_width=True)

                # MDD 낙폭 그래프 계산
                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max * 100
                
                spy_cum_roll_max = spy_cum_ret.cummax()
                spy_drawdown = (spy_cum_ret - spy_cum_roll_max) / spy_cum_roll_max * 100

                dd_df = pd.DataFrame({
                    "포트폴리오 낙폭 (%)": drawdown,
                    "S&P 500 낙폭 (%)": spy_drawdown
                }).dropna()

                st.markdown("#### 📉 고점 대비 낙폭 추이 (Drawdown Risk)")
                st.caption("그래프가 0% 아래로 크게 내려갈수록 변동성 위험이 큰 구간입니다.")
                st.area_chart(dd_df, color=["#EF4444", "#CBD5E1"], use_container_width=True)

                # 주요 통계 계산
                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                mdd = drawdown.min()

                st.markdown("#### 📊 핵심 성과 및 알파(Alpha) 지표")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("총 수익률", f"{tot_return:.2f}%")
                m2.metric("초과 수익 (Alpha)", f"{alpha:+.2f}%", delta=f"{alpha:.2f}%p")
                m3.metric("연간 변동성", f"{ann_vol:.2f}%")
                m4.metric("샤프 지수 (Sharpe)", f"{sharpe:.2f}")
                m5.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

        # TAB 3: 기술적 분석
        with tab3:
            st.markdown("### 🔍 개별 종목 기술적 지표 분석")
            selected_ticker = st.selectbox("분석할 종목을 선택하세요", valid_tickers)
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 이동평균": sma_50,
                "200일 이동평균": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 가격 & 이동평균선")
            st.line_chart(chart_df, use_container_width=True)

            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} RSI (14일): **{latest_rsi:.1f}**")
            if latest_rsi >= 70:
                st.warning("⚠️ 과매수 상태 (RSI ≥ 70)")
            elif latest_rsi <= 30:
                st.success("💡 과매도 상태 (RSI ≤ 30)")
            else:
                st.info("ℹ️ 중립 상태 (30 < RSI < 70)")

        # TAB 4: 리스크 & 상관관계 분석
        with tab4:
            st.markdown("### 🛡️ 자산 간 상관관계 및 리스크 표")
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
            st.markdown("#### 🔗 자산 상관관계 행렬 (Correlation Matrix)")
            st.dataframe(corr_matrix.style.format("{:.2f}"), use_container_width=True)

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
                "수익률 (%)": ind_ann_ret.map("{:.2f}%".format),
                "변동성 (%)": ind_ann_vol.map("{:.2f}%".format),
                "샤프 지수": ind_sharpe.map("{:.2f}".format),
                "최대 낙폭 (%)": pd.Series(ind_mdd).map("{:.2f}%".format)
            })

            st.dataframe(summary_df.T, use_container_width=True)

        # TAB 5: 와튼 대회 보고서 자동 생성
        with tab5:
            st.markdown("### 📄 Wharton Investment Executive Summary Generator")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("언어 선택", ["한국어", "English"])
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                if lang == "한국어":
                    report_text = f"""
### 📄 와튼 투자 대회 포트폴리오 요약 보고서

**1. 자산 배분 전략 (Asset Allocation)**
- **선택 카테고리:** {selected_sector}
- **자산 비중:** {weight_summary}

**2. 성과 및 리스크 측정 (Performance & Risk)**
- **포트폴리오 총 수익률:** {tot_return:.2f}%
- **시장 초과 수익률 (Alpha vs SPY):** {alpha:+.2f}%
- **연간 변동성 (Volatility):** {ann_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {sharpe:.2f}
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 투자 결론 (Thesis)**
본 포트폴리오는 S&P 500 지수 대비 {alpha:+.2f}%의 Alpha를 달성하며 시장 대비 뛰어난 성과를 기록했습니다. 샤프 지수 {sharpe:.2f}와 MDD {mdd:.2f}%를 통해 리스크 관리 우수성을 입증합니다.
                    """
                else:
                    report_text = f"""
### 📄 Wharton Investment Strategy Executive Summary

**1. Portfolio Construction**
- **Sector Focus:** {selected_sector}
- **Asset Allocation:** {weight_summary}

**2. Benchmark & Risk Performance**
- **Total Return:** {tot_return:.2f}%
- **Alpha (vs. S&P 500):** {alpha:+.2f}%
- **Annualized Volatility:** {ann_vol:.2f}%
- **Sharpe Ratio:** {sharpe:.2f}
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Key Takeaway**
The strategy generated an Alpha of {alpha:+.2f}% relative to the S&P 500, showing strong outperformance with robust downside risk control (MDD {mdd:.2f}%).
                    """
                
                st.markdown(report_text)
                st.text_area("보고서 텍스트 복사", report_text, height=220)
            else:
                st.warning("탭 2에서 종목 비중을 먼저 설정해 주세요.")

        # CSV 다운로드
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 분석 데이터 다운로드", 
            data=csv_data, 
            file_name="wharton_terminal_data.csv", 
            mime="text/csv"
        )
    else:
        st.error("선택한 종목의 주가를 불러올 수 없습니다.")
else:
    st.warning("👈 사이드바에서 분석할 종목을 선택해 주세요.")
