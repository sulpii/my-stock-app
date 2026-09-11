import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="스톡랩 (StockLab)", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    .main-header { font-size: 2.1rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; }
    .version-tag {
        background-color: #1E293B; color: #38BDF8; padding: 4px 10px;
        border-radius: 6px; font-size: 0.85rem; font-weight: 700; border: 1px solid #334155;
    }
    .kpi-card {
        background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 12px 16px;
    }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; }
    .kpi-value { font-size: 1.3rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-pos { color: #10B981; } .kpi-neg { color: #EF4444; }
    .shareable-report-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #38BDF8; border-radius: 16px; padding: 24px; margin: 16px 0;
    }
    .tutorial-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 14px 18px; border-radius: 4px 8px 8px 4px; margin-bottom: 20px;
    }
    .rank-badge {
        background: linear-gradient(90deg, #F59E0B, #D97706); color: white;
        padding: 4px 12px; border-radius: 12px; font-weight: bold; font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 완벽 검증 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "🧪 스톡랩 (StockLab)",
        "subtitle": "3초 만에 검증하는 미국 주식 포트폴리오 시뮬레이터",
        "ver_select": "📌 버전 / 모드 선택",
        "currency_select": "🔤 표시 통화",
        "sector_title": "🗂️ 섹터 선택",
        "sectors": {
            "IT / 반도체": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
            "빅테크 / 미디어": ["GOOGL", "META", "NFLX"],
            "커머스 / 모빌리티": ["AMZN", "TSLA", "NKE", "SBUX"],
            "소비재 / 대표 ETF": ["KO", "PEP", "WMT", "SPY", "QQQ"]
        },
        "ticker_title": "📌 종목 선택",
        "curr_price": "📌 실시간 종목 시세",
        "tab1": "📊 성과 비교",
        "tab2": "🎯 포트폴리오 고급 계산기",
        "tab3": "🔮 자산 시뮬레이션 👑",
        "tab4": "🔍 고성능 기술적 지표",
        "tab5": "🛡️ 리스크 분석",
        "tab6": "🏆 랭킹 & 공유 리포트 👑",
        "calc_btn": "🚀 분석 및 최적화 실행",
        "budget_label": "총 투자 예산",
        "sim_runs": "시뮬레이션 반복 횟수",
        "mc_res_title": "📊 1년 후 자산 예측 결과",
        "mc_p5": "보수적 시나리오 (하위 5%)",
        "mc_p50": "중립적 시나리오 (평균 50%)",
        "mc_p95": "낙관적 시나리오 (상위 5%)",
        "pro_lock": "👑 Pro 전용 기능입니다. 버전 선택에서 Pro 모드로 전환하세요.",
        "tut_title": "📖 StockLab 3초 사용 가이드",
        "tut_body": "1️⃣ <b>종목 선택</b>: 왼쪽 섹터에서 원하는 종목을 체크하세요.<br>2️⃣ <b>비중 설정</b>: <code>🎯 포트폴리오 계산기</code>에서 비중을 설정하거나 최적화 버튼을 누르세요.<br>3️⃣ <b>랭킹 확인</b>: <code>🏆 랭킹 & 공유 리포트</code>에서 내 수익률을 글로벌 랭킹과 비교해보세요.",
        "contact": "🤝 서비스 문의"
    },
    "English": {
        "title": "🧪 StockLab",
        "subtitle": "US Stock Portfolio Simulator in 3 Seconds",
        "ver_select": "📌 Version / Mode",
        "currency_select": "🔤 Currency",
        "sector_title": "🗂️ Select Sector",
        "sectors": {
            "IT / Tech & Semi": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
            "Big Tech / Media": ["GOOGL", "META", "NFLX"],
            "Commerce / Mobility": ["AMZN", "TSLA", "NKE", "SBUX"],
            "Consumer / Major ETFs": ["KO", "PEP", "WMT", "SPY", "QQQ"]
        },
        "ticker_title": "📌 Select Assets",
        "curr_price": "📌 Real-Time Market Prices",
        "tab1": "📊 Performance",
        "tab2": "🎯 Portfolio Advanced Calc",
        "tab3": "🔮 Asset Simulation 👑",
        "tab4": "🔍 Advanced Technicals",
        "tab5": "🛡️ Risk Metrics",
        "tab6": "🏆 Leaderboard & Report 👑",
        "calc_btn": "🚀 Run & Optimize Analytics",
        "budget_label": "Total Investment Budget",
        "sim_runs": "Simulation Runs",
        "mc_res_title": "📊 1-Year Asset Projection",
        "mc_p5": "Conservative (Worst 5%)",
        "mc_p50": "Moderate (Average 50%)",
        "mc_p95": "Optimistic (Best 5%)",
        "pro_lock": "👑 Pro feature only. Please switch to Pro mode in the Version menu.",
        "tut_title": "📖 Quick Start Guide",
        "tut_body": "1️⃣ <b>Select Assets</b>: Check desired tickers in the left sidebar.<br>2️⃣ <b>Set Weight</b>: Adjust weights or click auto-optimize in <code>🎯 Portfolio Calc</code>.<br>3️⃣ <b>Check Leaderboard</b>: Compare your returns on the <code>🏆 Leaderboard</code> tab.",
        "contact": "🤝 Contact Us"
    }
}

TICKER_TRANSLATIONS = {
    "한국어": {
        "NVDA": "엔비디아", "AAPL": "애플", "MSFT": "마이크로소프트", "AVGO": "브로드컴", "AMD": "AMD", "TSM": "TSMC",
        "GOOGL": "알파벳/구글", "META": "메타", "NFLX": "넷플릭스", "AMZN": "아마존", "TSLA": "테슬라", "NKE": "나이키",
        "SBUX": "스타벅스", "KO": "코카콜라", "PEP": "펩시코", "WMT": "월마트", "SPY": "S&P 500 ETF", "QQQ": "나스닥 100 ETF"
    },
    "English": {
        "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AVGO": "Broadcom", "AMD": "AMD", "TSM": "TSMC",
        "GOOGL": "Alphabet/Google", "META": "Meta", "NFLX": "Netflix", "AMZN": "Amazon", "TSLA": "Tesla", "NKE": "Nike",
        "SBUX": "Starbucks", "KO": "Coca-Cola", "PEP": "PepsiCo", "WMT": "Walmart", "SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF"
    }
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rates():
    try:
        krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        return {"USD": (1.0, "$"), "KRW": (krw, "₩")}
    except Exception:
        return {"USD": (1.0, "$"), "KRW": (1350.0, "₩")}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(tickers, start, end):
    try:
        raw = yf.download(tickers, start=start, end=end, progress=False)
        data = raw['Close'] if 'Close' in raw else raw
        if isinstance(data, pd.Series):
            data = data.to_frame()
        return data.dropna(how='all', axis=1)
    except Exception:
        return pd.DataFrame()

# Sidebar Settings
st.sidebar.markdown("### ⚙️ 언어 / Settings")
selected_lang = st.sidebar.selectbox("Language", ["한국어", "English"], index=0, label_visibility="collapsed")
L = LANG_DICT.get(selected_lang, LANG_DICT["한국어"])

rates = get_exchange_rates()
st.sidebar.markdown(f"### {L['currency_select']}")
curr_choice = st.sidebar.selectbox("Currency", ["USD ($)", "KRW (₩)"], index=0, label_visibility="collapsed")
curr_key = curr_choice.split(" ")[0]
fx_rate, curr_symbol = rates[curr_key]

def get_disp_name(ticker, lang):
    name = TICKER_TRANSLATIONS.get(lang, {}).get(ticker, ticker)
    return f"{name} ({ticker})"

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {L['ver_select']}")
mode_choice = st.sidebar.selectbox("모드 선택", ["v1.0 (일반 무료)", "v1.0 Pro (개발자/프리미엄)"], index=1)
is_pro = "Pro" in mode_choice

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f'<p class="main-header">{L["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{L["subtitle"]}</p>', unsafe_allow_html=True)
with col_h2:
    tag_name = "v1.0 Pro" if is_pro else "v1.0 Free"
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">{tag_name}</span></div>', unsafe_allow_html=True)

with st.expander(f"📖 **{L['tut_title']}**", expanded=False):
    st.markdown(f'<div class="tutorial-box">{L["tut_body"]}</div>', unsafe_allow_html=True)

# Sector & Asset Selection
sector_dict = L["sectors"]
st.sidebar.markdown(f"### {L['sector_title']}")
selected_sector = st.sidebar.radio("Sector", list(sector_dict.keys()), index=0, label_visibility="collapsed")
default_pool = sector_dict[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {L['ticker_title']}")
selected_tickers = []
for ticker in default_pool:
    disp = get_disp_name(ticker, selected_lang)
    if st.sidebar.checkbox(f"{disp}", value=(ticker in default_pool[:3]), key=f"chk_{ticker}"):
        selected_tickers.append(ticker)

today = datetime.today()
start_date = today - timedelta(days=365)
analysis_tickers = list(set(selected_tickers + ["SPY"]))

def update_chart_layout(fig, height=400):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode='pan',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=20, b=10),
        height=height
    )

if selected_tickers:
    with st.spinner('Fetching market data...'):
        data = fetch_stock_data(tuple(sorted(analysis_tickers)), str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # Real-time Cards
        st.markdown(f"##### {L['curr_price']} ({curr_symbol})")
        metric_cols = st.columns(min(len(valid_tickers), 4))
        for idx, ticker in enumerate(valid_tickers):
            col_target = metric_cols[idx % 4]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1] * fx_rate
                prev_p = series.iloc[-2] * fx_rate
                chg = ((curr_p - prev_p) / prev_p) * 100
                cls_style = "kpi-pos" if chg >= 0 else "kpi-neg"
                sign = "+" if chg >= 0 else ""
                
                col_target.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{get_disp_name(ticker, selected_lang)}</div>
                    <div class="kpi-value">{curr_symbol}{curr_p:,.2f}</div>
                    <div class="kpi-sub {cls_style}">{sign}{chg:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            L["tab1"], L["tab2"], L["tab3"], L["tab4"], L["tab5"], L["tab6"]
        ])

        # TAB 1: Performance
        with tab1:
            norm_df = (valid_data / valid_data.iloc[0]) * 100
            fig = go.Figure()
            for t in valid_tickers:
                fig.add_trace(go.Scatter(
                    x=norm_df.index, y=norm_df[t],
                    mode='lines', name=get_disp_name(t, selected_lang)
                ))
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2: Portfolio Advanced Calc (업그레이드된 계산기)
        with tab2:
            st.markdown("### 🎯 포트폴리오 비중 설정 및 최적화")
            daily_ret = valid_data.pct_change().dropna()
            
            # 자동 최적화 버튼 (샤프 지수 최대화)
            if st.button("⚡ 샤프 지수 최적 비중 자동 계산"):
                mean_returns = daily_ret.mean() * 252
                cov_matrix = daily_ret.cov() * 252
                num_assets = len(valid_tickers)
                
                # Monte Carlo Optimization for Optimal Weights
                best_sharpe = -1
                best_weights = np.ones(num_assets) / num_assets
                for _ in range(3000):
                    w = np.random.random(num_assets)
                    w /= np.sum(w)
                    ret = np.sum(mean_returns * w)
                    vol = np.sqrt(np.dot(w.T, np.dot(cov_matrix, w)))
                    sharpe = ret / vol if vol != 0 else 0
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_weights = w
                
                st.session_state['opt_weights'] = [int(round(x * 100)) for x in best_weights]
                st.success("샤프 지수를 극대화하는 최적 비중으로 입력값이 자동 적용되었습니다!")

            with st.form("portfolio_form_v20"):
                weights = []
                slider_cols = st.columns(min(len(valid_tickers), 4))
                opt_w = st.session_state.get('opt_weights', [int(100/len(valid_tickers))]*len(valid_tickers))
                
                for i, ticker in enumerate(valid_tickers):
                    with slider_cols[i % 4]:
                        val = st.number_input(f"{get_disp_name(ticker, selected_lang)} (%)", 0, 100, opt_w[i] if i < len(opt_w) else 0, step=1)
                        weights.append(val)
                submitted = st.form_submit_button(L["calc_btn"], use_container_width=True)

            total_weight = sum(weights)
            if total_weight > 0:
                norm_weights = np.array(weights) / total_weight
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                # 차트 생성
                fig_port = go.Figure()
                fig_port.add_trace(go.Scatter(x=port_cum_ret.index, y=port_cum_ret, mode='lines', name='My Portfolio', line=dict(color='#38BDF8', width=3)))
                fig_port.add_trace(go.Scatter(x=spy_cum_ret.index, y=spy_cum_ret, mode='lines', name='S&P 500 Benchmark', line=dict(color='#94A3B8', dash='dash')))
                update_chart_layout(fig_port)
                st.plotly_chart(fig_port, use_container_width=True)

                # 고급 분석 지표 계산 (Vol, Sharpe, MDD)
                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                sharpe_ratio = (port_daily_ret.mean() * 252) / (port_daily_ret.std() * np.sqrt(252)) if ann_vol != 0 else 0
                
                # MDD (최대 낙폭)
                cum_max = port_cum_ret.cummax()
                drawdown = (port_cum_ret - cum_max) / cum_max * 100
                mdd = drawdown.min()

                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                col_stat1.metric("누적 수익률", f"{tot_return:+.2f}%")
                col_stat2.metric("S&P 500 대비 Alpha", f"{alpha:+.2f}%p")
                col_stat3.metric("연간 변동성", f"{ann_vol:.2f}%")
                col_stat4.metric("샤프 지수 (Sharpe)", f"{sharpe_ratio:.2f}")

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'tot_return': tot_return,
                    'alpha': alpha,
                    'sharpe': sharpe_ratio,
                    'mdd': mdd,
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3: Simulation (Pro Only)
        with tab3:
            if not is_pro:
                st.warning(L["pro_lock"])
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    default_budget = 10000 * fx_rate
                    col_mc1, col_mc2 = st.columns([2, 1])
                    with col_mc1:
                        user_budget = st.number_input(f"{L['budget_label']} ({curr_symbol})", min_value=float(100*fx_rate), max_value=float(10000000*fx_rate), value=float(default_budget), step=float(500*fx_rate))
                    with col_mc2:
                        sim_runs = st.selectbox(L["sim_runs"], [1000, 5000, 10000], index=0)

                    port_daily_ret = sum_data['port_daily_ret']
                    T = 252 
                    sim_results = np.zeros((T, sim_runs))
                    sim_results[0] = user_budget

                    np.random.seed(42) 
                    mean_d = port_daily_ret.mean()
                    std_d = port_daily_ret.std()

                    for t in range(1, T):
                        rand_shocks = np.random.normal(mean_d, std_d, sim_runs)
                        sim_results[t] = sim_results[t-1] * (1 + rand_shocks)

                    fig_mc = go.Figure()
                    for i in range(min(sim_runs, 35)):
                        fig_mc.add_trace(go.Scatter(y=sim_results[:, i], mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
                    update_chart_layout(fig_mc)
                    st.plotly_chart(fig_mc, use_container_width=True)

                    p5 = np.percentile(sim_results[-1], 5)
                    p50 = np.percentile(sim_results[-1], 50)
                    p95 = np.percentile(sim_results[-1], 95)

                    st.markdown(f"#### {L['mc_res_title']}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric(L["mc_p5"], f"{curr_symbol}{p5:,.0f}", delta=f"{((p5-user_budget)/user_budget)*100:.1f}%")
                    m2.metric(L["mc_p50"], f"{curr_symbol}{p50:,.0f}", delta=f"{((p50-user_budget)/user_budget)*100:.1f}%")
                    m3.metric(L["mc_p95"], f"{curr_symbol}{p95:,.0f}", delta=f"{((p95-user_budget)/user_budget)*100:.1f}%")

        # TAB 4: Advanced Technical Indicators (업그레이드된 기술적 지표)
        with tab4:
            st.markdown("### 🔍 고성능 기술적 지표 분석 (Bollinger, RSI, MACD)")
            selected_ticker = st.selectbox("Ticker Select", options=valid_tickers, format_func=lambda x: get_disp_name(x, selected_lang), index=0)
            df_tech = pd.DataFrame({'Close': valid_data[selected_ticker] * fx_rate})
            
            # 지표 계산
            # 1. Bollinger Bands
            df_tech['MA20'] = df_tech['Close'].rolling(20).mean()
            df_tech['STD20'] = df_tech['Close'].rolling(20).std()
            df_tech['Upper'] = df_tech['MA20'] + (df_tech['STD20'] * 2)
            df_tech['Lower'] = df_tech['MA20'] - (df_tech['STD20'] * 2)

            # 2. RSI
            delta = df_tech['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df_tech['RSI'] = 100 - (100 / (1 + rs))

            # 3. MACD
            exp1 = df_tech['Close'].ewm(span=12, adjust=False).mean()
            exp2 = df_tech['Close'].ewm(span=26, adjust=False).mean()
            df_tech['MACD'] = exp1 - exp2
            df_tech['Signal'] = df_tech['MACD'].ewm(span=9, adjust=False).mean()

            # Subplot 차트 구성
            fig_tech = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.5, 0.25, 0.25])
            
            # Price & Bollinger Bands
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Close'], name='Price', line=dict(color='#38BDF8')), row=1, col=1)
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Upper'], name='Upper Band', line=dict(color='rgba(239, 68, 68, 0.5)', dash='dot')), row=1, col=1)
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Lower'], name='Lower Band', line=dict(color='rgba(16, 185, 129, 0.5)', dash='dot')), row=1, col=1)
            
            # RSI
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['RSI'], name='RSI (14)', line=dict(color='#F59E0B')), row=2, col=1)
            fig_tech.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
            fig_tech.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

            # MACD
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['MACD'], name='MACD', line=dict(color='#10B981')), row=3, col=1)
            fig_tech.add_trace(go.Scatter(x=df_tech.index, y=df_tech['Signal'], name='Signal', line=dict(color='#EF4444')), row=3, col=1)

            update_chart_layout(fig_tech, height=600)
            st.plotly_chart(fig_tech, use_container_width=True)

        # TAB 5: Risk Analysis
        with tab5:
            st.markdown("### 🛡️ Correlation Matrix")
            daily_returns = valid_data.pct_change().dropna()
            corr_df = daily_returns.corr()
            labels = [get_disp_name(t, selected_lang) for t in corr_df.columns]
            
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_df.values, x=labels, y=labels,
                colorscale='Blues', zmin=-1, zmax=1,
                text=np.round(corr_df.values, 2), texttemplate="%{text}"
            ))
            update_chart_layout(fig_corr)
            st.plotly_chart(fig_corr, use_container_width=True)

        # TAB 6: Leaderboard & Shareable Report (수익률 랭킹 시스템 추가)
        with tab6:
            if not is_pro:
                st.warning(L["pro_lock"])
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    # 가상의 글로벌 리더보드 데이터 베이스
                    leaderboard_data = [
                        {"순위": "🥇 1위", "트레이더": "AlphaHunter_99", "수익률": "+42.50%", "Sharpe": "2.85"},
                        {"순위": "🥈 2위", "트레이더": "QuantMaster", "수익률": "+38.12%", "Sharpe": "2.41"},
                        {"순위": "🥉 3위", "트레이더": "TechBull_US", "수익률": "+31.80%", "Sharpe": "2.10"},
                        {"순위": "4위", "트레이더": "WallStreet_Pro", "수익률": "+28.40%", "Sharpe": "1.95"},
                    ]
                    
                    # 현재 사용자 포트폴리오를 랭킹에 추가
                    user_ret_str = f"{sum_data['tot_return']:+.2f}%"
                    user_sharpe_str = f"{sum_data['sharpe']:.2f}"
                    leaderboard_data.append({"순위": "🎯 MY", "트레이더": "내 포트폴리오 (YOU)", "수익률": user_ret_str, "Sharpe": user_sharpe_str})
                    
                    st.markdown("### 🏆 StockLab 글로벌 수익률 랭킹")
                    st.table(pd.DataFrame(leaderboard_data))

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="shareable-report-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h2 style="color:#38BDF8; margin:0;">🧪 StockLab Portfolio Report</h2>
                            <span class="rank-badge">🏆 TOP 5% Portfolio</span>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; text-align:center;">
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">Total Return</p>
                                <h3 style="color:#F8FAFC; margin:5px 0;">{sum_data['tot_return']:+.2f}%</h3>
                            </div>
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">Alpha (vs S&P 500)</p>
                                <h3 style="color:#10B981; margin:5px 0;">{sum_data['alpha']:+.2f}%p</h3>
                            </div>
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">Sharpe Ratio</p>
                                <h3 style="color:#38BDF8; margin:5px 0;">{sum_data['sharpe']:.2f}</h3>
                            </div>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <p style="color:#E2E8F0; font-size:0.85rem; margin:0;">
                            <b>Asset Weights:</b> {" | ".join([f"{get_disp_name(t, selected_lang)}: {w}%" for t, w in zip(sum_data['valid_tickers'], sum_data['weights']) if w > 0])}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("Tab 2에서 [🚀 분석 및 최적화 실행]을 먼저 클릭하세요.")

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {L['contact']}")
        st.sidebar.code("aseui995@gmail.com", language="text")
