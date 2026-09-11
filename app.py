import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. Page Configuration & Theme
st.set_page_config(
    page_title="스톡랩 (StockLab) - 미국 주식 포트폴리오 실험실", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp {
        background-color: #0B0E14;
        color: #E2E8F0;
    }
    
    .main-header { font-size: 2.1rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; letter-spacing: -0.5px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; font-weight: 400; }
    
    .version-tag {
        background-color: #1E293B;
        color: #38BDF8;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #334155;
        display: inline-block;
    }
    
    .pro-badge {
        background: linear-gradient(135deg, #F59E0B, #D97706);
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
        margin-left: 8px;
    }
    
    .report-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
    
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
    
    .stRadio label, .stCheckbox label {
        padding: 10px 14px !important;
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px !important;
        margin-bottom: 6px !important;
        width: 100%;
        cursor: pointer;
        font-size: 1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Cached Data Fetcher (속도 최적화 핵심)
# ---------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(tickers, start, end):
    try:
        raw = yf.download(tickers, start=start, end=end, progress=False)
        data = raw['Close'] if 'Close' in raw else raw
        if isinstance(data, pd.Series):
            data = data.to_frame()
        data = data.dropna(how='all', axis=1)
        return data
    except Exception:
        return pd.DataFrame()

# Sidebar: Version Selector (버전 관리 추가)
st.sidebar.markdown("### 📌 서비스 버전")
available_versions = ["1.0 (최신 상용 버전)", "0.9 (베타)"]
selected_version_str = st.sidebar.selectbox("사용할 버전을 선택하세요", available_versions, index=0)
current_version = selected_version_str.split(" ")[0]

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Plan Selector
st.sidebar.markdown("### 👑 계정 요금제")
user_plan = st.sidebar.radio(
    "요금제 선택", 
    ["Free (일반 무료)", "Pro (프리미엄)"], 
    index=1, 
    key="plan_selector"
)
is_pro = True if "Pro" in user_plan else False

st.sidebar.markdown("---")

# Header Section
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<p class="main-header">🧪 스톡랩 (StockLab)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">초보자도 클릭 몇 번으로 끝내는 나만의 미국 주식 포트폴리오 실험실</p>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">v{current_version}</span></div>', unsafe_allow_html=True)

# Guide Expander
with st.expander("❓ 초보자용 3초 퀵 스타트 가이드"):
    st.markdown("""
    1. **왼쪽 사이드바**에서 투자하고 싶은 **관심 분야(섹터)**를 선택하세요.
    2. 원하는 주식 종목 체크박스에 **체크(✅)**를 합니다.
    3. 메인 화면의 **[🎯 내 포트폴리오 수익률 계산기]** 탭에서 주식별 투자 비중을 조절 후 **[🚀 계산 반영하기]**를 눌러보세요.
    4. 지수(S&P 500) 대비 얼마나 수익을 냈는지 한눈에 확인할 수 있습니다!
    """)

# Sector Database
SECTOR_DATABASE = {
    "🇺🇸 IT & 반도체 (엔비디아, 애플 등)": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM", "ASML", "INTC"],
    "🌐 인터넷 & 미디어 (구글, 메타 등)": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "VZ"],
    "🛍️ 쇼핑 & 전기차 (아마존, 테슬라 등)": ["AMZN", "TSLA", "HD", "NKE", "MCD", "SBUX"],
    "🛒 일상 생활용품 (코카콜라, 월마트)": ["PG", "KO", "PEP", "WMT", "COST"],
    "🏥 병원 & 제약 (일라이릴리, 존슨앤존슨)": ["LLY", "UNH", "JNJ", "MRK", "ABBV", "PFE"],
    "🏦 은행 & 투자 (버크셔, 워렌버핏)": ["BRK-B", "JPM", "V", "MA", "BAC", "GS"],
    "📊 인기 미국 대표 ETF (SPY, QQQ)": ["SPY", "QQQ", "DIA", "IWM", "TLT", "SCHD"]
}

# Sidebar Selectors
st.sidebar.markdown("### 🗂️ 1. 투자 분야 선택")
selected_sector = st.sidebar.radio(
    "분야 선택",
    options=list(SECTOR_DATABASE.keys()),
    index=0,
    key="unique_sector_radio",
    label_visibility="collapsed"
)

default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 2. 포함할 종목 선택")
selected_tickers = []
for ticker in default_pool:
    is_default = ticker in default_pool[:4]
    if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_v11_{selected_sector}_{ticker}"):
        selected_tickers.append(ticker)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 투자 분석 기간")

today = datetime.today()

if 'start_d' not in st.session_state:
    st.session_state.start_d = today - timedelta(days=365)

col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)

if col_q1.button("올해", key="btn_ytd_v11"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년", key="btn_1y_v11"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년", key="btn_3y_v11"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년", key="btn_5y_v11"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.session_state.start_d
end_date = today

st.sidebar.caption(f"📅 분석 기간: {start_date.strftime('%Y-%m-%d')} ~ 오늘까지")

analysis_tickers = list(set(selected_tickers + ["SPY"]))

# Main Logic
if selected_tickers:
    with st.spinner('실시간 주가 데이터를 불러오는 중입니다...'):
        data = fetch_stock_data(tuple(sorted(analysis_tickers)), str(start_date.strftime('%Y-%m-%d')), str(end_date.strftime('%Y-%m-%d')))

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # Live Real-time KPI Cards
        st.markdown("##### 📌 선택한 주식들의 현재 가격")
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

        # Tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 종목별 수익률 비교", 
            "🎯 내 포트폴리오 수익률 계산기", 
            "🔮 미래 자산 예측 (몬테카를로) 👑",
            "🔍 종목 상세 및 기술 지표", 
            "🛡️ 리스크 & 위험도 분석", 
            "📄 심층 종합 분석 리포트 👑"
        ])

        # TAB 1: Relative Return Chart
        with tab1:
            st.markdown("### 📈 주식들의 성과 비교 그래프")
            st.caption("시작일 주가를 '100'으로 동일하게 맞추어, 어느 주식이 더 많이 올랐는지 비교합니다.")
            
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['미국 대표지수 (S&P 500)'] = spy_data
                
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2: Form 기반을 통한 랙 없는 포트폴리오 계산기
        with tab2:
            st.markdown("### 🎯 내 맘대로 주식 비중 조절하기")
            st.caption("비중(%)을 설정한 후 아래 **[🚀 계산 반영하기]** 버튼을 누르면 끊김 없이 즉시 계산됩니다.")

            # Form 도입으로 슬라이더 조작 시 매번 렉 걸리는 문제 완벽 해결
            with st.form("portfolio_form"):
                weights = []
                slider_cols = st.columns(min(len(valid_tickers), 4))
                
                for i, ticker in enumerate(valid_tickers):
                    with slider_cols[i % 4]:
                        default_w = int(100 / len(valid_tickers))
                        val = st.number_input(
                            f"{ticker} 비중 (%)", 
                            min_value=0, 
                            max_value=100, 
                            value=default_w,
                            step=1, 
                            key=f"form_num_{ticker}"
                        )
                        weights.append(val)
                
                submitted = st.form_submit_button("🚀 계산 반영하기", use_container_width=True)

            total_weight = sum(weights)
            
            if total_weight == 0:
                st.warning("⚠️ 최소 1개 이상의 주식 비중에 숫자를 넣어주세요.")
            else:
                norm_weights = np.array(weights) / total_weight
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                chart_df = pd.DataFrame({
                    "내 포트폴리오": port_cum_ret,
                    "미국 시장 평균 (S&P 500)": spy_cum_ret
                }).dropna()

                st.markdown("#### 🚀 내 포트폴리오 vs 미국 시장 평균 수익률")
                st.line_chart(chart_df, color=["#38BDF8", "#94A3B8"], use_container_width=True)

                cum_roll_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_roll_max) / cum_roll_max * 100
                
                spy_cum_roll_max = spy_cum_ret.cummax()
                spy_drawdown = (spy_cum_ret - spy_cum_roll_max) / spy_cum_roll_max * 100

                dd_df = pd.DataFrame({
                    "내 포트폴리오 하락폭 (%)": drawdown,
                    "S&P 500 하락폭 (%)": spy_drawdown
                }).dropna()

                st.markdown("#### 📉 주가 하락 위험도 (최고점 대비 하락률)")
                st.area_chart(dd_df, color=["#EF4444", "#475569"], use_container_width=True)

                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                mdd = drawdown.min()

                st.markdown("#### 📊 한눈에 보는 성과 요약")
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("총 수익률", f"{tot_return:.2f}%")
                m2.metric("시장 대비 초과수익", f"{alpha:+.2f}%p", help="S&P 500 지수 대비 수익입니다.")
                m3.metric("주가 흔들림(변동성)", f"{ann_vol:.2f}%", help="높을수록 변동성이 큽니다.")
                m4.metric("투자 효율성(샤프지수)", f"{sharpe:.2f}", help="1.0 이상 시 우수합니다.")
                m5.metric("최대 하락폭(MDD)", f"{mdd:.2f}%", help="최대 폭락 하락률입니다.")

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'weights_summary': ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0]),
                    'tot_return': tot_return,
                    'spy_tot_return': spy_tot_return,
                    'alpha': alpha,
                    'ann_vol': ann_vol,
                    'sharpe': sharpe,
                    'mdd': mdd,
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3: Monte Carlo Simulation (PRO)
        with tab3:
            st.markdown("### 🔮 몬테카를로 1년 후 내 자산 예측 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            
            if not is_pro:
                st.markdown("""
                <div class="upgrade-card">
                    <h3>👑 Pro 플랜 전용 예측 기능입니다</h3>
                    <p style="color:#A5B4FC;">과거 주가 데이터 1,000가지 시나리오를 바탕으로 1년 뒤 내 자산을 예측합니다.</p>
                    <p style="font-size:0.85rem; color:#67E8F9;">👈 사이드바에서 'Pro (프리미엄)'을 선택하세요!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data and 'port_daily_ret' in sum_data:
                    port_daily_ret = sum_data['port_daily_ret']
                    mc_sims = 1000
                    T = 252 
                    initial_portfolio = 10000 

                    mean_daily = port_daily_ret.mean()
                    stdev_daily = port_daily_ret.std()

                    sim_results = np.zeros((T, mc_sims))
                    sim_results[0] = initial_portfolio

                    np.random.seed(42) 
                    for t in range(1, T):
                        rand_shocks = np.random.normal(mean_daily, stdev_daily, mc_sims)
                        sim_results[t] = sim_results[t-1] * (1 + rand_shocks)

                    mc_df = pd.DataFrame(sim_results)
                    
                    st.markdown("#### 📊 1,000가지 가상 자산 변화 경로 ($10,000 투자 시작 시)")
                    st.line_chart(mc_df.iloc[:, :50], use_container_width=True)

                    p5 = np.percentile(sim_results[-1], 5)
                    p50 = np.percentile(sim_results[-1], 50)
                    p95 = np.percentile(sim_results[-1], 95)

                    st.markdown("#### 🎯 1년 후 예상 자산 평가액 구간")
                    c_mc1, c_mc2, c_mc3 = st.columns(3)
                    c_mc1.metric("최악의 경우 (하위 5%)", f"${p5:,.0f}", delta=f"{((p5-10000)/10000)*100:.1f}%")
                    c_mc2.metric("평균적인 경우 (중위 50%)", f"${p50:,.0f}", delta=f"{((p50-10000)/10000)*100:.1f}%")
                    c_mc3.metric("최선의 경우 (상위 5%)", f"${p95:,.0f}", delta=f"{((p95-10000)/10000)*100:.1f}%")
                else:
                    st.warning("탭 2에서 포트폴리오 비중을 먼저 설정한 후 [🚀 계산 반영하기]를 눌러주세요.")

        # TAB 4: Technical Analysis
        with tab4:
            st.markdown("### 🔍 종목별 심층 분석 및 이동평균선")
            selected_ticker = st.radio("분석할 주식 선택", valid_tickers, horizontal=True, key="sb_tech_ticker_v11")
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                selected_ticker: stock_series,
                "50일 평균선 (단기 추세)": sma_50,
                "200일 평균선 (장기 추세)": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 주가 및 이동평균선 추세")
            st.line_chart(chart_df, use_container_width=True)

            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 과열/냉각 지표 (RSI 지수): **{latest_rsi:.1f}점**")
            if latest_rsi >= 70:
                st.warning("⚠️ 과열 상태입니다. (과매수 구간)")
            elif latest_rsi <= 30:
                st.success("💡 과도하게 떨어진 상태입니다. (과매도 구간)")
            else:
                st.info("ℹ️ 정상적이고 안정적인 구간입니다.")

        # TAB 5: Risk & Correlation
        with tab5:
            st.markdown("### 🛡️ 함께 흔들리는 정도 (상관관계 분석)")
            st.caption("1.0에 가까울수록 같은 방향으로 움직이며, 0에 가까울수록 분산 효과가 큽니다.")
            
            daily_returns = valid_data.pct_change().dropna()
            corr_matrix = daily_returns.corr()
            
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
                "주가 변동 폭 (%)": ind_ann_vol.map("{:.2f}%".format),
                "투자 효율성 점수": ind_sharpe.map("{:.2f}".format),
                "최대 낙폭 (MDD %)": pd.Series(ind_mdd).map("{:.2f}%".format)
            })

            st.markdown("#### 📋 개별 주식별 성과 종합 표")
            st.dataframe(summary_df.T, use_container_width=True)

        # TAB 6: Detailed Professional Report (Pro 전용 대폭 강화)
        with tab6:
            st.markdown("### 📄 프로 심층 포트폴리오 진단 리포트 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            
            if not is_pro:
                st.markdown("""
                <div class="upgrade-card">
                    <h3>👑 Pro 플랜 전용 프리미엄 진단 리포트입니다</h3>
                    <p style="color:#A5B4FC;">포트폴리오 비중 진단, 퀀트 샤프지수 평가, 리밸런싱 가이드라인이 포함된 전문 보고서를 제공합니다.</p>
                    <p style="font-size:0.85rem; color:#67E8F9;">👈 사이드바에서 'Pro (프리미엄)'을 선택해 보세요!</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    st.markdown("---")
                    
                    # Section 1: Portfolio Structure Diagnostic
                    st.markdown("#### 1. 📌 자산 배분 구조 및 집중도 진단")
                    col_r1, col_r2 = st.columns(2)
                    
                    with col_r1:
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        st.markdown("**종목별 구성 비율**")
                        for t, w in zip(sum_data['valid_tickers'], sum_data['weights']):
                            if w > 0:
                                st.write(f"- **{t}**: `{w}%`")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with col_r2:
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        st.markdown("**투자 집중도 평가**")
                        max_w = max(sum_data['weights'])
                        if max_w >= 50:
                            st.warning(f"⚠️ 특정 단일 종목에 비중이 {max_w}% 이상 쏠려 있어 개별 종목 리스크에 취약합니다.")
                        else:
                            st.success("✅ 특정 종목 쏠림 현상이 적고 적절하게 분산 배치되었습니다.")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Section 2: Quant Risk & Return Evaluation
                    st.markdown("#### 2. 📊 퀀트 성과 및 위험 효율성 종합 평가")
                    r_col1, r_col2, r_col3 = st.columns(3)
                    
                    with r_col1:
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        st.markdown("**수익성 (Alpha)**")
                        st.markdown(f"### `{sum_data['tot_return']:+.2f}%`")
                        if sum_data['alpha'] > 0:
                            st.caption(f"S&P 500 대비 **+{sum_data['alpha']:.2f}%p** 뛰어난 초과 성과 기록")
                        else:
                            st.caption(f"S&P 500 대비 **{sum_data['alpha']:.2f}%p** 부진함")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with r_col2:
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        st.markdown("**위험 대비 효율 (Sharpe)**")
                        st.markdown(f"### `{sum_data['sharpe']:.2f}`")
                        if sum_data['sharpe'] >= 1.0:
                            st.caption("🏆 **우수**: 감수한 위험 대비 수익 창출 능력이 탁월합니다.")
                        else:
                            st.caption("💡 **보통/개선필요**: 변동성에 비해 수익률 호율이 다소 낮습니다.")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                    with r_col3:
                        st.markdown('<div class="report-card">', unsafe_allow_html=True)
                        st.markdown("**최대 방어력 (MDD)**")
                        st.markdown(f"### `{sum_data['mdd']:.2f}%`")
                        st.caption(f"과거 가장 높은 폭락장에서 최대 **{abs(sum_data['mdd']):.1f}%** 하락을 경험했습니다.")
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Section 3: Professional Rebalancing Action Plan
                    st.markdown("#### 3. 💡 전문가 리밸런싱 가이드라인")
                    st.markdown('<div class="report-card">', unsafe_allow_html=True)
                    st.markdown("""
                    * **변동성 관리**: 주가 변동성(`{:.2f}%`) 수준을 감안할 때, 정기적인 6개월/1년 주기 리밸런싱을 권장합니다.
                    * **하락장 대비**: 최대 하락폭(`{:.2f}%`) 견딤 유무를 점검하고, 감당하기 어려운 경우 지수 ETF(SPY, QQQ) 비중을 10~20% 늘려 안정성을 보강하세요.
                    * **섹터 점검**: 현재 구성된 섹터(`{}`) 주식들 간 상관관계를 확인하여 같은 방향으로 움직이는 종목 간 비중을 조절해보세요.
                    """.format(sum_data['ann_vol'], sum_data['mdd'], selected_sector))
                    st.markdown('</div>', unsafe_allow_html=True)

                else:
                    st.warning("탭 2에서 포트폴리오 비중을 설정한 후 [🚀 계산 반영하기]를 눌러주세요.")

        # Sidebar Footer
        st.sidebar.markdown("---")
        csv_data = valid_data.to_csv().encode('utf-8')
        st.sidebar.download_button(
            "📥 주가 데이터 엑셀(CSV) 다운로드", 
            data=csv_data, 
            file_name="stocklab_data.csv", 
            mime="text/csv",
            key="btn_csv_download_v11"
        )
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤝 서비스 / 제휴 문의")
        st.sidebar.caption("스톡랩 개발팀 문의:")
        st.sidebar.code("contact.stocklab@gmail.com", language="text")
    else:
        st.error("선택한 주식의 데이터를 가져올 수 없습니다.")
else:
    st.warning("👈 왼쪽 사이드바에서 분석할 주식을 하나 이상 체크해 주세요.")
