import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. 페이지 레이아웃 및 하이엔드 금융 단말기 테마 설정
st.set_page_config(
    page_title="Wharton Institutional Analytics Terminal", 
    page_icon="🏛️", 
    layout="wide"
)

# Custom CSS - Bloomberg/FactSet Style Dark Professional Theme
st.markdown("""
    <style>
    /* Global Styles */
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    
    .main-header { font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin-bottom: 2px; letter-spacing: -0.5px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 24px; font-weight: 400; }
    
    /* KPI Card Styling */
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .kpi-title { font-size: 0.8rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.5rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-sub { font-size: 0.85rem; font-weight: 600; }
    .kpi-pos { color: #10B981; }
    .kpi-neg { color: #EF4444; }
    
    /* Sidebar Fixes */
    .checkbox-container {
        max-height: 250px;
        overflow-y: auto;
        border: 1px solid #334155;
        padding: 12px;
        border-radius: 8px;
        background-color: #0F172A;
        margin-bottom: 15px;
    }
    
    /* Section Divider */
    hr { border-color: #1E293B !important; }
    
    .stButton>button {
        background-color: #0EA5E9;
        color: white;
        border-radius: 6px;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0284C7;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 헤더 섹션
st.markdown('<p class="main-header">🏛️ Wharton Investment Competition Analytics Terminal Pro</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">글로벌 GICS 섹터 분석, 알파(Alpha) 검증, 몬테카를로 자산 시뮬레이션 및 와튼 심사보고서 생성기</p>', unsafe_allow_html=True)

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

# 4. 사이드바 - 설정 제어 영역
st.sidebar.markdown("### 🗂️ 1. GICS 섹터 선택")
selected_sector = st.sidebar.selectbox(
    "카테고리를 선택하세요",
    options=list(SECTOR_DATABASE.keys()),
    index=0,
    key="unique_sector_select_box"
)

default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 2. 구성 종목 선택 (클릭 ON/OFF)")
st.sidebar.caption("클릭만으로 포트폴리오를 자유롭게 조절하세요.")

selected_tickers = []
with st.sidebar.container():
    st.markdown('<div class="checkbox-container">', unsafe_allow_html=True)
    for ticker in default_pool:
        is_default = ticker in default_pool[:4]
        if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_v3_{selected_sector}_{ticker}"):
            selected_tickers.append(ticker)
    st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 분석 기간 (Quick Select)")

today = datetime.today()
col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)

if 'start_d' not in st.session_state:
    st.session_state.start_d = datetime(2023, 1, 1)

if col_q1.button("YTD", key="btn_ytd_v3"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년", key="btn_1y_v3"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년", key="btn_3y_v3"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년", key="btn_5y_v3"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.sidebar.date_input("시작일", st.session_state.start_d, key="input_start_d_v3")
end_date = st.sidebar.date_input("종료일", today, key="input_end_d_v3")

# SPY 지수 자동 포함
analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('금융 시장 데이터를 실시간으로 수집 중...'):
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

        # 실시간 KPI 시세 카드 (커스텀 시각화 적용)
        st.markdown("##### 📌 선택 자산 실시간 데이터 카드")
        metric_cols = st.columns(min(len(valid_tickers), 5))
        for idx, ticker in enumerate(valid_tickers):
            col_target = metric_cols[idx % 5]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                cls_style = "kpi-pos" if chg >= 0 else "kpi-neg"
                sign = "+" if chg >= 0 else ""
                
                col_target.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{ticker}</div>
                    <div class="kpi-value">${curr_p:.2f}</div>
                    <div class="kpi-sub {cls_style}">{sign}{chg:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 5. 확장된 메인 분석 탭 (총 6개 탭)
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 상대 수익률 & SPY 비교", 
            "🎯 포트폴리오 백테스터 & Risk", 
            "🔮 Monte Carlo 자산 시뮬레이션",
            "🔍 개별 종목 심층 분석 (SMA/RSI)", 
            "🛡️ 리스크 & 상관관계 행렬", 
            "📄 와튼 심사용 Executive Summary"
        ])

        # TAB 1: 상대 수익률 비교
        with tab1:
            st.markdown("### 📈 시작 시점 기준(100 Indexing) Relative Performance")
            st.caption("기준 가격 100에서 시작하여 벤치마크 지수(S&P 500) 대비 상승률을 추적합니다.")
            
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['S&P 500 (SPY)'] = spy_data
                
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: 포트폴리오 백테스터 & Risk
        with tab2:
            st.markdown("### 🎯 자산 배분(Asset Allocation) 및 초과수익(Alpha) 산출")
            
            if st.button("⚖️ 모든 종목 비중 동일하게 맞추기 (1/N Rebalance)", key="btn_equal_w_v3"):
                equal_w = int(100 / len(valid_tickers))
                for t in valid_tickers:
                    st.session_state[f"w_v3_{t}"] = equal_w

            weights = []
            slider_cols = st.columns(min(len(valid_tickers), 4))
            for i, ticker in enumerate(valid_tickers):
                with slider_cols[i % 4]:
                    default_val = st.session_state.get(f"w_v3_{ticker}", int(100 / len(valid_tickers)))
                    w = st.slider(f"{ticker} 비중 (%)", 0, 100, default_val, step=5, key=f"w_v3_{ticker}")
                    weights.append(w)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("⚠️ 최소 1개 이상의 종목 비중을 1% 이상 설정해 주세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                chart_df = pd.DataFrame({
                    "포트폴리오 (Portfolio)": port_cum_ret,
                    "벤치마크 (S&P 500)": spy_cum_ret
                }).dropna()

                st.markdown("#### 🚀 Cumulative Return vs Benchmark")
                st.line_chart(chart_df, color=["#38BDF8", "#94A3B8"], use_container_width=True)

                # MDD 계산 및 차트
                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max * 100
                
                spy_cum_roll_max = spy_cum_ret.cummax()
                spy_drawdown = (spy_cum_ret - spy_cum_roll_max) / spy_cum_roll_max * 100

                dd_df = pd.DataFrame({
                    "포트폴리오 낙폭 (%)": drawdown,
                    "S&P 500 낙폭 (%)": spy_drawdown
                }).dropna()

                st.markdown("#### 📉 Drawdown Profile (고점 대비 하락 폭)")
                st.area_chart(dd_df, color=["#EF4444", "#475569"], use_container_width=True)

                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                mdd = drawdown.min()

                st.markdown("#### 📊 기관급 성과/위험 핵심 지표 (Key Institutional Metrics)")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("총 수익률", f"{tot_return:.2f}%")
                m2.metric("초과 수익 (Alpha)", f"{alpha:+.2f}%", delta=f"{alpha:.2f}%p")
                m3.metric("연간 변동성", f"{ann_vol:.2f}%")
                m4.metric("샤프 지수 (Sharpe)", f"{sharpe:.2f}")
                m5.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

        # TAB 3: Monte Carlo 자산 시뮬레이션 (신규 고급 기능)
        with tab3:
            st.markdown("### 🔮 몬테카를로(Monte Carlo) 향후 1년 자산 시뮬레이션")
            st.caption("과거 변동성과 수익률 패턴을 토대로 1,000가지 시나리오의 미래 자산 가치 범위를 정밀 예측합니다.")
            
            if 'port_daily_ret' in locals() and len(port_daily_ret) > 0:
                mc_sims = 1000
                T = 252 # 1년 거래일
                initial_portfolio = 10000 # 기준 자산 $10,000

                mean_daily = port_daily_ret.mean()
                stdev_daily = port_daily_ret.std()

                # Monte Carlo Engine
                sim_results = np.zeros((T, mc_sims))
                sim_results[0] = initial_portfolio

                np.random.seed(42) # 결과 일관성 유지
                for t in range(1, T):
                    rand_shocks = np.random.normal(mean_daily, stdev_daily, mc_sims)
                    sim_results[t] = sim_results[t-1] * (1 + rand_shocks)

                mc_df = pd.DataFrame(sim_results)
                
                st.markdown("#### 📊 1,000개 자산 시나리오 경로 추이 ($10,000 시작 기준)")
                st.line_chart(mc_df.iloc[:, :50], use_container_width=True) # 50개 샘플 시각화

                p5 = np.percentile(sim_results[-1], 5)
                p50 = np.percentile(sim_results[-1], 50)
                p95 = np.percentile(sim_results[-1], 95)

                st.markdown("#### 🎯 1년 후 예상 자산 평가액 구간")
                c_mc1, c_mc2, c_mc3 = st.columns(3)
                c_mc1.metric("하단 5% (최악 시나리오)", f"${p5:,.0f}", delta=f"{((p5-10000)/10000)*100:.1f}%")
                c_mc2.metric("중위 50% (기대 자산가치)", f"${p50:,.0f}", delta=f"{((p50-10000)/10000)*100:.1f}%")
                c_mc3.metric("상단 95% (최선 시나리오)", f"${p95:,.0f}", delta=f"{((p95-10000)/10000)*100:.1f}%")

        # TAB 4: 기술적 분석
        with tab4:
            st.markdown("### 🔍 개별 종목 기술적 지표 (Technical Indicators)")
            selected_ticker = st.selectbox("분석할 종목을 선택하세요", valid_tickers, key="sb_tech_ticker_v3")
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 이동평균 (SMA 50)": sma_50,
                "200일 이동평균 (SMA 200)": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 이동평균 추세")
            st.line_chart(chart_df, use_container_width=True)

            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} 상대강도지수 (RSI 14일): **{latest_rsi:.1f}**")
            if latest_rsi >= 70:
                st.warning("⚠️ 과매수 구간 (RSI ≥ 70) - 단기 조정 가능성 고려")
            elif latest_rsi <= 30:
                st.success("💡 과매도 구간 (RSI ≤ 30) - 기술적 반등 가능성 고려")
            else:
                st.info("ℹ️ 중립 구간 (30 < RSI < 70)")

        # TAB 5: 리스크 & 상관관계 분석
        with tab5:
            st.markdown("### 🛡️ 상관관계 행렬 (Correlation Matrix) & Risk Table")
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
            st.markdown("#### 🔗 포트폴리오 자산 간 상관계수 (낮을수록 분산효과 극대화)")
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
                "연간 수익률 (%)": ind_ann_ret.map("{:.2f}%".format),
                "연간 변동성 (%)": ind_ann_vol.map("{:.2f}%".format),
                "샤프 지수 (Sharpe)": ind_sharpe.map("{:.2f}".format),
                "최대 낙폭 (MDD %)": pd.Series(ind_mdd).map("{:.2f}%".format)
            })

            st.dataframe(summary_df.T, use_container_width=True)

        # TAB 6: 와튼 보고서 자동 생성
        with tab6:
            st.markdown("### 📄 Wharton Investment Competition Executive Summary Generator")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("보고서 언어 선택", ["English (권장)", "한국어"], key="radio_lang_v3")
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                if lang == "English (권장)":
                    report_text = f"""
### 📄 Executive Summary: Wharton Investment Competition Portfolio

**1. Strategy & Asset Allocation**
- **Target Sector:** {selected_sector}
- **Portfolio Construction:** {weight_summary}

**2. Quantitative Risk & Return Performance**
- **Total Cumulative Return:** {tot_return:.2f}%
- **Alpha (vs. S&P 500 Benchmark):** {alpha:+.2f}%
- **Annualized Volatility:** {ann_vol:.2f}%
- **Sharpe Ratio (Rf=4%):** {sharpe:.2f}
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Monte Carlo Forward Simulation (1-Year Horizon)**
- **5th Percentile (Downside Risk):** ${p5:,.0f} ({((p5-10000)/10000)*100:.1f}%)
- **50th Percentile (Expected Value):** ${p50:,.0f} ({((p50-10000)/10000)*100:.1f}%)
- **95th Percentile (Upside Potential):** ${p95:,.0f} ({((p95-10000)/10000)*100:.1f}%)

**4. Investment Thesis**
Our strategic asset allocation achieved an Alpha of {alpha:+.2f}% over the S&P 500 benchmark. By maintaining a Sharpe ratio of {sharpe:.2f} and an MDD of {mdd:.2f}%, the portfolio demonstrates superior risk-adjusted return efficiency suitable for Wharton Competition standards.
                    """
                else:
                    report_text = f"""
### 📄 와튼 투자 대회 포트폴리오 요약 보고서

**1. 자산 배분 전략 (Asset Allocation)**
- **선택 카테고리:** {selected_sector}
- **자산 비중:** {weight_summary}

**2. 정량적 성과 및 위험 측정 (Performance)**
- **포트폴리오 총 수익률:** {tot_return:.2f}%
- **시장 초과 수익률 (Alpha vs SPY):** {alpha:+.2f}%
- **연간 변동성 (Volatility):** {ann_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {sharpe:.2f}
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 몬테카를로 미래 시뮬레이션 (1년 미래 자산가치)**
- **하단 5% (최악 시나리오):** ${p5:,.0f} ({((p5-10000)/10000)*100:.1f}%)
- **중위 50% (기대 자산가치):** ${p50:,.0f} ({((p50-10000)/10000)*100:.1f}%)
- **상단 95% (최선 시나리오):** ${p95:,.0f} ({((p95-10000)/10000)*100:.1f}%)

**4. 종합 투자 제안 (Investment Thesis)**
본 포트폴리오는 S&P 500 벤치마크 대비 {alpha:+.2f}%의 Alpha를 기록했습니다. 샤프 지수 {sharpe:.2f} 및 MDD {mdd:.2f}%를 통해 최적화된 위험 대비 수익 효율성을 입증합니다.
                    """
                
                st.markdown(report_text)
                st.text_area("보고서 텍스트 복사", report_text, height=260, key="ta_report_v3")
            else:
                st.warning("탭 2에서 종목 비중을 먼저 설정해 주세요.")

        # CSV 다운로드
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 분석 데이터 다운로드", 
            data=csv_data, 
            file_name="wharton_terminal_data.csv", 
            mime="text/csv",
            key="btn_csv_download_v3"
        )
    else:
        st.error("선택한 종목의 주가를 불러올 수 없습니다.")
else:
    st.warning("👈 사이드바에서 분석할 종목을 선택해 주세요.")
