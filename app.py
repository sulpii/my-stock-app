import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
    .pro-badge {
        background: linear-gradient(135deg, #F59E0B, #D97706); color: white;
        padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-left: 8px;
    }
    .kpi-card {
        background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 12px 16px;
    }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; }
    .kpi-value { font-size: 1.4rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-pos { color: #10B981; } .kpi-neg { color: #EF4444; }
    .shareable-report-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #38BDF8; border-radius: 16px; padding: 24px; margin: 16px 0;
    }
    .tutorial-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 14px 18px; border-radius: 4px 8px 8px 4px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 완벽 검증 다국어 사전 (Strict Translation Dictionary)
LANG_DICT = {
    "한국어": {
        "title": "🧪 스톡랩 (StockLab)",
        "subtitle": "3초 만에 검증하는 미국 주식 포트폴리오 시뮬레이터",
        "ver_select": "📌 버전 / 모드 선택",
        "settings": "⚙️ 언어 설정",
        "sector_title": "🗂️ 섹터 선택",
        "ticker_title": "📌 종목 선택",
        "curr_price": "📌 실시간 종목 시세",
        "tab1": "📊 성과 비교",
        "tab2": "🎯 포트폴리오 계산기",
        "tab3": "🔮 자산 시뮬레이션 👑",
        "tab4": "🔍 기술적 지표",
        "tab5": "🛡️ 리스크 분석",
        "tab6": "📸 공유용 리포트 👑",
        "calc_btn": "🚀 분석 실행",
        "budget_label": "💵 총 투자 예산 ($)",
        "sim_runs": "시뮬레이션 반복 횟수",
        "mc_res_title": "📊 1년 후 자산 예측 결과",
        "mc_p5": "보수적 시나리오 (하위 5%)",
        "mc_p50": "중립적 시나리오 (평균 50%)",
        "mc_p95": "낙관적 시나리오 (상위 5%)",
        "pro_lock": "👑 Pro 전용 기능입니다. 버전 선택에서 Pro 모드로 전환하세요.",
        "tut_title": "📖 StockLab 3초 사용 가이드",
        "tut_body": "1️⃣ <b>종목 선택</b>: 왼쪽 섹터에서 원하는 종목을 체크하세요.<br>2️⃣ <b>비중 설정</b>: <code>🎯 포트폴리오 계산기</code>에서 종목별 비중(%)을 입력하고 <b>[🚀 분석 실행]</b>을 누르세요.<br>3️⃣ <b>결과 확인</b>: S&P 500 대비 수익률 및 1년 후 예상 자산을 확인해보세요.",
        "contact": "🤝 서비스 문의"
    },
    "English": {
        "title": "🧪 StockLab",
        "subtitle": "US Stock Portfolio Simulator in 3 Seconds",
        "ver_select": "📌 Version / Mode Select",
        "settings": "⚙️ Language Settings",
        "sector_title": "🗂️ Select Sector",
        "ticker_title": "📌 Select Assets",
        "curr_price": "📌 Real-Time Market Prices",
        "tab1": "📊 Performance",
        "tab2": "🎯 Portfolio Calculator",
        "tab3": "🔮 Asset Simulation 👑",
        "tab4": "🔍 Technicals",
        "tab5": "🛡️ Risk Metrics",
        "tab6": "📸 Shareable Report 👑",
        "calc_btn": "🚀 Run Analytics",
        "budget_label": "💵 Total Budget ($)",
        "sim_runs": "Simulation Runs",
        "mc_res_title": "📊 1-Year Asset Projection",
        "mc_p5": "Conservative (Worst 5%)",
        "mc_p50": "Moderate (Average 50%)",
        "mc_p95": "Optimistic (Best 5%)",
        "pro_lock": "👑 Pro feature only. Please switch to Pro mode in the Version menu.",
        "tut_title": "📖 Quick Start Guide",
        "tut_body": "1️⃣ <b>Select Assets</b>: Check desired tickers in the left sidebar.<br>2️⃣ <b>Set Weight</b>: Enter weights (%) in <code>🎯 Portfolio Calculator</code> and click <b>[🚀 Run Analytics]</b>.<br>3️⃣ <b>View Results</b>: Compare returns against S&P 500 and run 1-year asset projections.",
        "contact": "🤝 Contact Us"
    },
    "日本語": {
        "title": "🧪 ストックラボ (StockLab)",
        "subtitle": "3秒で検証する米国株ポートフォリオシミュレーター",
        "ver_select": "📌 バージョン / モード選択",
        "settings": "⚙️ 言語設定",
        "sector_title": "🗂️ セクター選択",
        "ticker_title": "📌 銘柄選択",
        "curr_price": "📌 リアルタイム株価",
        "tab1": "📊 パフォーマンス比較",
        "tab2": "🎯 ポートフォリオ計算機",
        "tab3": "🔮 資産シミュレーション 👑",
        "tab4": "🔍 テクニカル指標",
        "tab5": "🛡️ リスク分析",
        "tab6": "📸 共有用レポート 👑",
        "calc_btn": "🚀 分析実行",
        "budget_label": "💵 投資予算 ($)",
        "sim_runs": "試行回数",
        "mc_res_title": "📊 1年後の資産予測結果",
        "mc_p5": "保守的シナリオ (下位5%)",
        "mc_p50": "標準シナリオ (中央50%)",
        "mc_p95": "楽観的シナリオ (上位5%)",
        "pro_lock": "👑 Pro専用機能です。バージョン選択でProモードに切り替えてください。",
        "tut_title": "📖 Quick ガイド",
        "tut_body": "1️⃣ <b>銘柄選択</b>: 左のサイドバーで希望の銘柄をチェックします。<br>2️⃣ <b>比率設定</b>: <code>🎯 ポートフォリオ計算機</code>で投資比率(%)を入力し<b>[🚀 分析実行]</b>をクリックします。<br>3️⃣ <b>結果確認</b>: S&P 500との比較や1年後の予想資産を確認できます。",
        "contact": "🤝 お問い合わせ"
    }
}

TICKER_NAMES = {
    "NVDA": "엔비디아 (NVDA)", "AAPL": "애플 (AAPL)", "MSFT": "마이크로소프트 (MSFT)", 
    "AVGO": "브로드컴 (AVGO)", "AMD": "AMD (AMD)", "TSM": "TSMC (TSM)",
    "GOOGL": "알파벳 (GOOGL)", "META": "메타 (META)", "NFLX": "넷플릭스 (NFLX)",
    "AMZN": "아마존 (AMZN)", "TSLA": "테슬라 (TSLA)", "NKE": "나이키 (NKE)", "SBUX": "스타벅스 (SBUX)",
    "KO": "코카콜라 (KO)", "PEP": "펩시코 (PEP)", "WMT": "월마트 (WMT)",
    "BRK-B": "버크셔 해서웨이 (BRK-B)", "JPM": "JP모건 (JPM)", "SPY": "S&P 500 (SPY)", "QQQ": "나스닥 100 (QQQ)"
}

def get_disp_name(ticker):
    return TICKER_NAMES.get(ticker, ticker)

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

# Sidebar: Language & Version Mode Selection
st.sidebar.markdown("### ⚙️ 언어 (Language)")
selected_lang = st.sidebar.selectbox("Language", ["한국어", "English", "日本語"], index=0, label_visibility="collapsed")
L = LANG_DICT[selected_lang]

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {L['ver_select']}")
mode_choice = st.sidebar.selectbox(
    "모드 선택", 
    ["v1.0 (일반 무료)", "v1.0 Pro (개발자/프리미엄)"], 
    index=1
)
is_pro = "Pro" in mode_choice

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f'<p class="main-header">{L["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{L["subtitle"]}</p>', unsafe_allow_html=True)
with col_h2:
    tag_name = "v1.0 Pro" if is_pro else "v1.0 Free"
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">{tag_name}</span></div>', unsafe_allow_html=True)

# Guide Tutorial Expander
with st.expander(f"📖 **{L['tut_title']}**", expanded=False):
    st.markdown(f"""
    <div class="tutorial-box">
    {L['tut_body']}
    </div>
    """, unsafe_allow_html=True)

# Sector Database
SECTOR_DATABASE = {
    "IT / 반도체": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
    "빅테크 / 미디어": ["GOOGL", "META", "NFLX"],
    "커머스 / 모빌리티": ["AMZN", "TSLA", "NKE", "SBUX"],
    "소비재 / 대표 ETF": ["KO", "PEP", "WMT", "SPY", "QQQ"]
}

st.sidebar.markdown(f"### {L['sector_title']}")
selected_sector = st.sidebar.radio("Sector", list(SECTOR_DATABASE.keys()), index=0, label_visibility="collapsed")
default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown(f"### {L['ticker_title']}")
selected_tickers = []
for ticker in default_pool:
    disp = get_disp_name(ticker)
    if st.sidebar.checkbox(f"{disp}", value=(ticker in default_pool[:3]), key=f"chk_v17_{ticker}"):
        selected_tickers.append(ticker)

today = datetime.today()
start_date = today - timedelta(days=365)
analysis_tickers = list(set(selected_tickers + ["SPY"]))

def update_chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode='pan',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=400
    )

if selected_tickers:
    with st.spinner('Data Fetching...'):
        data = fetch_stock_data(tuple(sorted(analysis_tickers)), str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # Real-time Cards
        st.markdown(f"##### {L['curr_price']}")
        metric_cols = st.columns(min(len(valid_tickers), 4))
        for idx, ticker in enumerate(valid_tickers):
            col_target = metric_cols[idx % 4]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                cls_style = "kpi-pos" if chg >= 0 else "kpi-neg"
                sign = "+" if chg >= 0 else ""
                
                col_target.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{get_disp_name(ticker)}</div>
                    <div class="kpi-value">${curr_p:.2f}</div>
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
                    mode='lines', name=get_disp_name(t),
                    hovertemplate="%{x|%Y-%m-%d}<br><b>" + get_disp_name(t) + "</b>: %{y:.1f}pt"
                ))
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

        # TAB 2: Portfolio Calculator
        with tab2:
            with st.form("portfolio_form_v17"):
                weights = []
                slider_cols = st.columns(min(len(valid_tickers), 4))
                for i, ticker in enumerate(valid_tickers):
                    with slider_cols[i % 4]:
                        default_w = int(100 / len(valid_tickers))
                        val = st.number_input(f"{get_disp_name(ticker)} (%)", 0, 100, default_w, step=1)
                        weights.append(val)
                submitted = st.form_submit_button(L["calc_btn"], use_container_width=True)

            total_weight = sum(weights)
            if total_weight > 0:
                norm_weights = np.array(weights) / total_weight
                daily_ret = valid_data.pct_change().dropna()
                port_daily_ret = (daily_ret * norm_weights).sum(axis=1)
                port_cum_ret = (1 + port_daily_ret).cumprod() * 100

                spy_daily_ret = spy_data.pct_change().dropna() if spy_data is not None else port_daily_ret
                spy_cum_ret = (1 + spy_daily_ret).cumprod() * 100

                fig_port = go.Figure()
                fig_port.add_trace(go.Scatter(x=port_cum_ret.index, y=port_cum_ret, mode='lines', name='My Portfolio', line=dict(color='#38BDF8', width=3)))
                fig_port.add_trace(go.Scatter(x=spy_cum_ret.index, y=spy_cum_ret, mode='lines', name='S&P 500 Benchmark', line=dict(color='#94A3B8', dash='dash')))
                update_chart_layout(fig_port)
                st.plotly_chart(fig_port, use_container_width=True, config={'scrollZoom': True})

                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'tot_return': tot_return,
                    'alpha': alpha,
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3: Simulation (Pro Only)
        with tab3:
            if not is_pro:
                st.warning(L["pro_lock"])
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    col_mc1, col_mc2 = st.columns([2, 1])
                    with col_mc1:
                        user_budget = st.number_input(L["budget_label"], min_value=100, max_value=10000000, value=10000, step=500)
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
                    st.plotly_chart(fig_mc, use_container_width=True, config={'scrollZoom': True})

                    p5 = np.percentile(sim_results[-1], 5)
                    p50 = np.percentile(sim_results[-1], 50)
                    p95 = np.percentile(sim_results[-1], 95)

                    st.markdown(f"#### {L['mc_res_title']}")
                    m1, m2, m3 = st.columns(3)
                    m1.metric(L["mc_p5"], f"${p5:,.0f}", delta=f"{((p5-user_budget)/user_budget)*100:.1f}%")
                    m2.metric(L["mc_p50"], f"${p50:,.0f}", delta=f"{((p50-user_budget)/user_budget)*100:.1f}%")
                    m3.metric(L["mc_p95"], f"${p95:,.0f}", delta=f"{((p95-user_budget)/user_budget)*100:.1f}%")

        # TAB 4: Technicals
        with tab4:
            selected_ticker = st.selectbox("Ticker", options=valid_tickers, format_func=get_disp_name, index=0)
            stock_series = valid_data[selected_ticker]
            
            fig_detail = go.Figure()
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series, mode='lines', name='Price', line=dict(color='#38BDF8')))
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series.rolling(50).mean(), mode='lines', name='MA 50'))
            update_chart_layout(fig_detail)
            st.plotly_chart(fig_detail, use_container_width=True, config={'scrollZoom': True})

        # TAB 5: Risk Correlation Matrix
        with tab5:
            st.markdown("### 🛡️ 종목 간 상관관계 Matrix")
            daily_returns = valid_data.pct_change().dropna()
            corr_df = daily_returns.corr()
            st.dataframe(corr_df.style.format("{:.2f}").background_gradient(cmap="Blues"), use_container_width=True)

        # TAB 6: Shareable Card (Pro Only)
        with tab6:
            if not is_pro:
                st.warning(L["pro_lock"])
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    st.markdown(f"""
                    <div class="shareable-report-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h2 style="color:#38BDF8; margin:0;">🧪 StockLab Report</h2>
                            <span style="color:#94A3B8; font-size:0.85rem;">{datetime.now().strftime('%Y-%m-%d')}</span>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <div style="display:grid; grid-template-columns: repeat(2, 1fr); gap:10px; text-align:center;">
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">Total Return</p>
                                <h3 style="color:#F8FAFC; margin:5px 0;">{sum_data['tot_return']:+.2f}%</h3>
                            </div>
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">Alpha (vs S&P 500)</p>
                                <h3 style="color:#10B981; margin:5px 0;">{sum_data['alpha']:+.2f}%p</h3>
                            </div>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <p style="color:#E2E8F0; font-size:0.85rem; margin:0;">
                            <b>Allocation:</b> {" | ".join([f"{t}: {w}%" for t, w in zip(sum_data['valid_tickers'], sum_data['weights']) if w > 0])}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.info("탭 2에서 [🚀 분석 실행]을 먼저 클릭하세요.")

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {L['contact']}")
        st.sidebar.code("aseui995@gmail.com", language="text")
