import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
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
    .tutorial-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 14px 18px; border-radius: 4px 8px 8px 4px; margin-bottom: 20px;
    }
    .risk-info-box {
        background-color: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 다국어 사전
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
        "tab2": "🎯 포트폴리오 계산기",
        "tab3": "🔮 종합 시뮬레이션 👑",
        "tab4": "🔍 기술적 지표",
        "tab5": "🛡️ 리스크 분석",
        "tab6": "🏆 유저 랭킹",
        "calc_btn": "🚀 분석 실행",
        "budget_label": "총 투자 예산",
        "sim_runs": "시뮬레이션 반복 횟수",
        "mc_res_title": "📊 1년 후 자산 예측 결과",
        "mc_p5": "보수적 (하위 5%)",
        "mc_p50": "중립적 (평균 50%)",
        "mc_p95": "낙관적 (상위 5%)",
        "pro_lock": "👑 Pro 전용 기능입니다. 버전 선택에서 Pro 모드로 전환하세요.",
        "tut_title": "📖 Quick 가이드",
        "tut_body": "1️⃣ <b>종목 선택</b>: 왼쪽 섹터에서 원하는 종목을 체크하세요.<br>2️⃣ <b>비중 설정</b>: <code>🎯 포트폴리오 계산기</code>에서 비중을 입력하고 [🚀 분석 실행]을 누르세요.<br>3️⃣ <b>리스크 분석</b>: 종목 간 상관관계와 최대 하락폭(MDD)을 확인해보세요.",
        "contact": "🤝 서비스 문의",
        "rank_empty": "🏆 아직 등록된 포트폴리오가 없습니다. 분석 실행 후 [랭킹에 내 포트폴리오 등록]을 눌러보세요!",
        "submit_rank": "🏆 내 포트폴리오 랭킹에 등록하기"
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
        "tab2": "🎯 Portfolio Calculator",
        "tab3": "🔮 Asset Simulation 👑",
        "tab4": "🔍 Technicals",
        "tab5": "🛡️ Risk Metrics",
        "tab6": "🏆 Leaderboard",
        "calc_btn": "🚀 Run Analytics",
        "budget_label": "Total Investment Budget",
        "sim_runs": "Simulation Runs",
        "mc_res_title": "📊 1-Year Asset Projection",
        "mc_p5": "Conservative (Worst 5%)",
        "mc_p50": "Moderate (Average 50%)",
        "mc_p95": "Optimistic (Best 5%)",
        "pro_lock": "👑 Pro feature only. Please switch to Pro mode in the Version menu.",
        "tut_title": "📖 Quick Start Guide",
        "tut_body": "1️⃣ <b>Select Assets</b>: Check tickers in sidebar.<br>2️⃣ <b>Set Weight</b>: Enter weights in Portfolio Calculator.<br>3️⃣ <b>Risk Analysis</b>: Check correlation heatmaps and Max Drawdown (MDD).",
        "contact": "🤝 Contact Us",
        "rank_empty": "🏆 No registered portfolios yet. Be the first to register yours!",
        "submit_rank": "🏆 Submit My Portfolio to Leaderboard"
    },
    "日本語": {
        "title": "🧪 ストックラボ (StockLab)",
        "subtitle": "3秒で検証する米国株ポートフォリオシミュレーター",
        "ver_select": "📌 バージョン / モード選択",
        "currency_select": "🔤 表示通貨",
        "sector_title": "🗂️ セクター選択",
        "sectors": {
            "IT / 半導体": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
            "ビッグテック / メディア": ["GOOGL", "META", "NFLX"],
            "コマース / モビリティ": ["AMZN", "TSLA", "NKE", "SBUX"],
            "消費財 / 代表 ETF": ["KO", "PEP", "WMT", "SPY", "QQQ"]
        },
        "ticker_title": "📌 銘柄選択",
        "curr_price": "📌 リアルタイム株価",
        "tab1": "📊 パフォーマンス比較",
        "tab2": "🎯 ポートフォリオ計算機",
        "tab3": "🔮 総合シミュレーション 👑",
        "tab4": "🔍 テクニカル指標",
        "tab5": "🛡️ リスク分析",
        "tab6": "🏆 ランキング",
        "calc_btn": "🚀 分析実行",
        "budget_label": "総投資予算",
        "sim_runs": "試行回数",
        "mc_res_title": "📊 1年後の資産予測結果",
        "mc_p5": "保守的 (下位5%)",
        "mc_p50": "標準 (中央50%)",
        "mc_p95": "楽観的 (上位5%)",
        "pro_lock": "👑 Pro専用機能です。バージョン選択でProモードに切り替えてください。",
        "tut_title": "📖 Quick ガイド",
        "tut_body": "1️⃣ <b>銘柄選択</b>: サイドバーで銘柄を選択します。<br>2️⃣ <b>比率設定</b>: ポートフォリオ計算機で比率を入力します。<br>3️⃣ <b>リスク分析</b>: 相関行列と最大ドローダウン(MDD)を確認します。",
        "contact": "🤝 お問い合わせ",
        "rank_empty": "🏆 登録されたポートフォリオはまだありません。最初のポートフォリオを登録してみましょう！",
        "submit_rank": "🏆 ランキングに登録する"
    },
    "中文": {
        "title": "🧪 股票实验室 (StockLab)",
        "subtitle": "3秒验证美股投资组合模拟器",
        "ver_select": "📌 版本 / 模式选择",
        "currency_select": "🔤 显示货币",
        "sector_title": "🗂️ 选择板块",
        "sectors": {
            "IT / 半导体": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
            "科技巨头 / 媒体": ["GOOGL", "META", "NFLX"],
            "电商 / 出行": ["AMZN", "TSLA", "NKE", "SBUX"],
            "消费品 / 代表 ETF": ["KO", "PEP", "WMT", "SPY", "QQQ"]
        },
        "ticker_title": "📌 选择股票",
        "curr_price": "📌 实时股票行情",
        "tab1": "📊 收益率对比",
        "tab2": "🎯 投资组合计算器",
        "tab3": "🔮 综合模拟预测 👑",
        "tab4": "🔍 技术指标",
        "tab5": "🛡️ 风险分析",
        "tab6": "🏆 排行榜",
        "calc_btn": "🚀 开始分析",
        "budget_label": "总投资预算",
        "sim_runs": "模拟重复次数",
        "mc_res_title": "📊 1年后资产预测结果",
        "mc_p5": "保守 (下位 5%)",
        "mc_p50": "基准 (平均 50%)",
        "mc_p95": "乐观 (上位 5%)",
        "pro_lock": "👑 此功能仅限 Pro 用户。请在版本菜单中切换至 Pro 模式。",
        "tut_title": "📖 快速指南",
        "tut_body": "1️⃣ <b>选择股票</b>: 在侧边栏勾选股票。<br>2️⃣ <b>设置权重</b>: 输入比重并点击开始分析。<br>3️⃣ <b>风险分析</b>: 查看相关系数矩阵及最大回撤 (MDD)。",
        "contact": "🤝 联系我们",
        "rank_empty": "🏆 暂无已注册的投资组合。快来提交您的第一个组合吧！",
        "submit_rank": "🏆 提交组合至排行榜"
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
        "GOOGL": "Alphabet", "META": "Meta", "NFLX": "Netflix", "AMZN": "Amazon", "TSLA": "Tesla", "NKE": "Nike",
        "SBUX": "Starbucks", "KO": "Coca-Cola", "PEP": "PepsiCo", "WMT": "Walmart", "SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF"
    },
    "日本語": {
        "NVDA": "NVIDIA", "AAPL": "Apple", "MSFT": "Microsoft", "AVGO": "Broadcom", "AMD": "AMD", "TSM": "TSMC",
        "GOOGL": "Alphabet", "META": "Meta", "NFLX": "Netflix", "AMZN": "Amazon", "TSLA": "Tesla", "NKE": "Nike",
        "SBUX": "Starbucks", "KO": "Coca-Cola", "PEP": "PepsiCo", "WMT": "Walmart", "SPY": "S&P 500 ETF", "QQQ": "Nasdaq 100 ETF"
    },
    "中文": {
        "NVDA": "英伟达", "AAPL": "苹果", "MSFT": "微软", "AVGO": "博通", "AMD": "AMD", "TSM": "台积电",
        "GOOGL": "谷歌", "META": "Meta", "NFLX": "网飞", "AMZN": "亚马逊", "TSLA": "特斯拉", "NKE": "耐克",
        "SBUX": "星巴克", "KO": "可口可乐", "PEP": "百事可乐", "WMT": "沃尔玛", "SPY": "标普 500 ETF", "QQQ": "纳斯达克 100 ETF"
    }
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rates():
    try:
        krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        jpy = yf.Ticker("JPY=X").history(period="1d")['Close'].iloc[-1]
        return {"USD": (1.0, "$"), "KRW": (krw, "₩"), "JPY": (jpy, "¥")}
    except Exception:
        return {"USD": (1.0, "$"), "KRW": (1350.0, "₩"), "JPY": (150.0, "¥")}

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

# Sidebar
st.sidebar.markdown("### ⚙️ 언어 / Settings")
selected_lang = st.sidebar.selectbox("Language", ["한국어", "English", "日本語", "中文"], index=0, label_visibility="collapsed")
L = LANG_DICT[selected_lang]

rates = get_exchange_rates()
st.sidebar.markdown(f"### {L['currency_select']}")
curr_choice = st.sidebar.selectbox("Currency", ["USD ($)", "KRW (₩)", "JPY (¥)"], index=0, label_visibility="collapsed")
curr_key = curr_choice.split(" ")[0]
fx_rate, curr_symbol = rates[curr_key]

def get_disp_name(ticker, lang):
    name = TICKER_TRANSLATIONS.get(lang, {}).get(ticker, ticker)
    return f"{name} ({ticker})" if name != ticker else ticker

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

# Sector & Ticker Selection
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

def update_chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode='pan',
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380
    )

if selected_tickers:
    with st.spinner('Data Fetching...'):
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
                fig.add_trace(go.Scatter(x=norm_df.index, y=norm_df[t], mode='lines', name=get_disp_name(t, selected_lang)))
            update_chart_layout(fig)
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2: Portfolio Calculator
        with tab2:
            with st.form("portfolio_form"):
                weights = []
                slider_cols = st.columns(min(len(valid_tickers), 4))
                for i, ticker in enumerate(valid_tickers):
                    with slider_cols[i % 4]:
                        default_w = int(100 / len(valid_tickers))
                        val = st.number_input(f"{get_disp_name(ticker, selected_lang)} (%)", 0, 100, default_w, step=1)
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
                fig_port.add_trace(go.Scatter(x=port_cum_ret.index, y=port_cum_ret, mode='lines', name='Portfolio', line=dict(color='#38BDF8', width=3)))
                fig_port.add_trace(go.Scatter(x=spy_cum_ret.index, y=spy_cum_ret, mode='lines', name='S&P 500', line=dict(color='#94A3B8', dash='dash')))
                update_chart_layout(fig_port)
                st.plotly_chart(fig_port, use_container_width=True)

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'norm_weights': norm_weights,
                    'tot_return': (port_cum_ret.iloc[-1] - 100),
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3: Asset Simulation
        with tab3:
            if not is_pro:
                st.warning(L["pro_lock"])
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    default_budget = 10000 * fx_rate
                    col_mc1, col_mc2 = st.columns([2, 1])
                    with col_mc1:
                        user_budget = st.number_input(f"{L['budget_label']} ({curr_symbol})", min_value=float(100*fx_rate), value=float(default_budget), step=float(500*fx_rate))
                    with col_mc2:
                        sim_runs = st.selectbox(L["sim_runs"], [1000, 5000, 10000], index=0)

                    # Expander로 안내 숨김 처리
                    with st.expander("💡 **시뮬레이션 원리 및 종목별 배분 가이드 보기**"):
                        st.markdown("""
                        * **몬테카를로 시뮬레이션**: 과거 종목들의 일일 수익률/변동성을 바탕으로 1년 후 발생 가능한 주가 경로를 무작위 산출합니다.
                        * **하위 5% (보수적)**: 주식 시장이 폭락하는 극단적 악재 상황의 예상 잔고입니다.
                        * **상위 5% (낙관적)**: 강력한 상승장이 지속되는 호재 상황의 예상 잔고입니다.
                        """)

                    st.markdown("##### 📌 종목별 투자금 배분")
                    alloc_cols = st.columns(min(len(sum_data['valid_tickers']), 4))
                    for idx, (t, w) in enumerate(zip(sum_data['valid_tickers'], sum_data['weights'])):
                        allocated_amt = user_budget * (w / 100.0)
                        with alloc_cols[idx % 4]:
                            st.metric(label=get_disp_name(t, selected_lang), value=f"{curr_symbol}{allocated_amt:,.0f}", delta=f"{w}% 비중")

                    st.markdown("---")

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
                    for i in range(min(sim_runs, 30)):
                        fig_mc.add_trace(go.Scatter(y=sim_results[:, i], mode='lines', line=dict(width=1), opacity=0.25, showlegend=False))
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
                else:
                    st.info("Tab 2에서 [🚀 분석 실행]을 먼저 클릭하세요.")

        # TAB 4: Technicals (Expander로 지표 설명 추가)
        with tab4:
            selected_ticker = st.selectbox("Ticker", options=valid_tickers, format_func=lambda x: get_disp_name(x, selected_lang), index=0)
            stock_series = valid_data[selected_ticker] * fx_rate
            
            with st.expander("❓ **기술적 지표 용어 정리가 필요하신가요? (클릭해서 펼치기)**"):
                st.markdown("""
                * **이동평균선 (Moving Average, MA 50)**: 최근 50일간의 평균 주가입니다. 주가가 이 선 위에 있으면 **상승 추세**, 아래에 있으면 **하락 추세**로 해석합니다.
                * **RSI (상대강도지수)**: 주가의 과열 정도를 측정합니다. **70 이상**은 과매수(수익실현 고려), **30 이하**는 과매도(저점 매수 고려) 구간입니다.
                """)

            # 주가 + MA50
            fig_detail = go.Figure()
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series, mode='lines', name='Price', line=dict(color='#38BDF8')))
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series.rolling(50).mean(), mode='lines', name='MA 50 (50일 평균)', line=dict(color='#F59E0B')))
            update_chart_layout(fig_detail)
            st.plotly_chart(fig_detail, use_container_width=True)

        # TAB 5: Risk Analysis (초보자 친화적 개편 + 추가 지표)
        with tab5:
            st.markdown("### 🛡️ 포트폴리오 리스크 완벽 분석")
            
            with st.expander("💡 **리스크 지표 쉬운 설명서 (클릭해서 펼치기)**"):
                st.markdown("""
                * **상관관계(Correlation)란?**: 종목들이 얼마나 **함께 움직이는지** 나타냅니다.
                  - **`+1.0`에 가까움**: 두 종목이 같이 오르고 같이 떨어집니다 (분산투자 효과 낮음).
                  - **`0.0`에 가까움**: 두 종목이 서로 상관없이 제각각 움직입니다 (분산투자 효과 높음).
                  - **`-1.0`에 가까움**: 한 종목이 오르면 다른 종목은 떨어집니다.
                * **최대 낙폭(MDD, Max Drawdown)**: 전고점 대비 **가장 크게 폭락했을 때의 하락률**입니다. 내 통장이 버틸 수 있는 '매집 한계선'을 뜻합니다.
                """)

            col_r1, col_r2 = st.columns(2)
            
            with col_r1:
                st.markdown("##### 1. 종목 간 상관관계 히트맵")
                daily_returns = valid_data.pct_change().dropna()
                corr_df = daily_returns.corr()
                labels = [get_disp_name(t, selected_lang) for t in corr_df.columns]
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_df.values, x=labels, y=labels, colorscale='Blues',
                    zmin=-1, zmax=1, text=np.round(corr_df.values, 2), texttemplate="%{text}"
                ))
                update_chart_layout(fig_corr)
                st.plotly_chart(fig_corr, use_container_width=True)

            with col_r2:
                st.markdown("##### 2. 종목별 최대 낙폭 (MDD, 최근 1년)")
                mdd_dict = {}
                for t in valid_tickers:
                    s = valid_data[t]
                    peak = s.cummax()
                    drawdown = (s - peak) / peak
                    mdd_dict[get_disp_name(t, selected_lang)] = drawdown.min() * 100
                
                mdd_df = pd.DataFrame(list(mdd_dict.items()), columns=['종목', 'MDD (%)'])
                fig_mdd = px.bar(mdd_df, x='종목', y='MDD (%)', color='MDD (%)', color_continuous_scale='Reds_r')
                update_chart_layout(fig_mdd)
                st.plotly_chart(fig_mdd, use_container_width=True)

        # TAB 6: Leaderboard
        with tab6:
            if 'rankings' not in st.session_state:
                st.session_state['rankings'] = []

            sum_data = st.session_state.get('summary_data', None)
            if sum_data:
                if st.button(L["submit_rank"], use_container_width=True):
                    entry = {
                        "등록일시": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "수익률 (%)": f"{sum_data['tot_return']:+.2f}%",
                        "포트폴리오 구성": ", ".join([f"{t}({w}%)" for t, w in zip(sum_data['valid_tickers'], sum_data['weights']) if w > 0])
                    }
                    st.session_state['rankings'].append(entry)
                    st.success("랭킹에 성공적으로 등록되었습니다!")

            st.markdown("---")
            if not st.session_state['rankings']:
                st.info(L["rank_empty"])
            else:
                rank_df = pd.DataFrame(st.session_state['rankings'])
                st.dataframe(rank_df, use_container_width=True)

        st.sidebar.markdown("---")
        st.sidebar.markdown(f"### {L['contact']}")
        st.sidebar.code("aseui995@gmail.com", language="text")
