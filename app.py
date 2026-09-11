import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. Page Configuration
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
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Caching Data & Optimization
# ---------------------------------------------------------
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

# PRO 요금제 결제 팝업 (Dialog)
if hasattr(st, "dialog"):
    @st.dialog("💳 StockLab Pro 요금제 결제")
    def show_payment_modal():
        st.markdown("### 👑 Pro 멤버십으로 스마트하게 투자하세요")
        st.write("월 **$9.99** / 연간 **$99.00** (20% 할인)")
        st.markdown("""
        * 🔮 **몬테카를로 1,000회 시뮬레이션** (미래 자산 예측)
        * 📄 **AI 퀀트 심층 종합 리포트** 제공
        * 🚀 **실시간 무제한 데이터 리프레시**
        """)
        st.markdown("---")
        card_num = st.text_input("카드 번호", placeholder="1234 - 5678 - 9012 - 3456")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.text_input("유효기간", placeholder="MM/YY")
        with col_p2:
            st.text_input("CVC", placeholder="123")
            
        if st.button("💳 7일 무료 체험 후 구독 시작하기", use_container_width=True):
            st.session_state['user_plan_status'] = "Pro (프리미엄)"
            st.success("🎉 Pro 요금제 승인이 완료되었습니다!")
            st.rerun()

# Sidebar: Version Selector
st.sidebar.markdown("### 📌 서비스 버전")
available_versions = ["1.0 (상용 최적화)", "0.9 (베타)"]
selected_version_str = st.sidebar.selectbox("버전 선택", available_versions, index=0)
current_version = selected_version_str.split(" ")[0]

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Plan Selector with Payment Modal Trigger
st.sidebar.markdown("### 👑 계정 요금제")
if 'user_plan_status' not in st.session_state:
    st.session_state['user_plan_status'] = "Free (일반 무료)"

selected_plan = st.sidebar.radio(
    "요금제 선택", 
    ["Free (일반 무료)", "Pro (프리미엄)"], 
    index=0 if st.session_state['user_plan_status'] == "Free (일반 무료)" else 1,
    key="plan_radio_input"
)

if selected_plan == "Pro (프리미엄)" and st.session_state['user_plan_status'] != "Pro (프리미엄)":
    if hasattr(st, "dialog"):
        show_payment_modal()
    else:
        st.sidebar.warning("💳 Pro 결제가 필요합니다.")

is_pro = True if st.session_state['user_plan_status'] == "Pro (프리미엄)" else False

st.sidebar.markdown("---")

# Header Section
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<p class="main-header">🧪 스톡랩 (StockLab)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">초보자도 클릭 몇 번으로 끝내는 나만의 미국 주식 포트폴리오 실험실</p>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">v{current_version}</span></div>', unsafe_allow_html=True)

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
    if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_v12_{selected_sector}_{ticker}"):
        selected_tickers.append(ticker)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 투자 분석 기간")

today = datetime.today()
if 'start_d' not in st.session_state:
    st.session_state.start_d = today - timedelta(days=365)

col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)
if col_q1.button("올해", key="btn_ytd_v12"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년", key="btn_1y_v12"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년", key="btn_3y_v12"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년", key="btn_5y_v12"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.session_state.start_d
end_date = today

analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('실시간 데이터를 불러오는 중...'):
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
            "🔍 선택 종목 상세 지표", 
            "🛡️ 리스크 & 위험도 분석", 
            "📄 심층 종합 분석 리포트 👑"
        ])

        # TAB 1
        with tab1:
            st.markdown("### 📈 주식들의 성과 비교 그래프")
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['미국 대표지수 (S&P 500)'] = spy_data
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2
        with tab2:
            st.markdown("### 🎯 내 맘대로 주식 비중 조절하기")
            with st.form("portfolio_form_v12"):
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
                            key=f"form_num_v12_{ticker}"
                        )
                        weights.append(val)
                submitted = st.form_submit_button("🚀 계산 반영하기", use_container_width=True)

            total_weight = sum(weights)
            if total_weight > 0:
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

                st.line_chart(chart_df, color=["#38BDF8", "#94A3B8"], use_container_width=True)

                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                rf = 4.0
                sharpe = (ann_ret - rf) / ann_vol if ann_vol != 0 else 0
                cum_roll_max = port_cum_ret.cummax()
                mdd = ((port_cum_ret - cum_roll_max) / cum_roll_max * 100).min()

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'tot_return': tot_return,
                    'alpha': alpha,
                    'ann_vol': ann_vol,
                    'sharpe': sharpe,
                    'mdd': mdd,
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3
        with tab3:
            st.markdown("### 🔮 몬테카를로 1년 후 내 자산 예측 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            if not is_pro:
                st.warning("👑 Pro 요금제 전용 기능입니다. 사이드바에서 Pro 요금제를 클릭해 결제 후 이용해 주세요.")
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    port_daily_ret = sum_data['port_daily_ret']
                    mc_sims = 1000
                    T = 252 
                    initial_portfolio = 10000 
                    sim_results = np.zeros((T, mc_sims))
                    sim_results[0] = initial_portfolio

                    np.random.seed(42) 
                    for t in range(1, T):
                        rand_shocks = np.random.normal(port_daily_ret.mean(), port_daily_ret.std(), mc_sims)
                        sim_results[t] = sim_results[t-1] * (1 + rand_shocks)

                    st.line_chart(pd.DataFrame(sim_results).iloc[:, :50], use_container_width=True)

        # TAB 4: Selected Tickers Detail Analytics (요청사항 반영: 추가한 종목 모두 동적 선택)
        with tab4:
            st.markdown("### 🔍 선택한 종목별 기술적 지표 상세 분석")
            st.caption("초기 화면에서 선택한 종목들을 자유롭게 전환하며 지표를 확인하세요.")
            
            selected_ticker = st.selectbox(
                "분석할 종목을 선택하세요", 
                options=valid_tickers, 
                index=0, 
                key="tab4_ticker_selector"
            )
            
            stock_series = valid_data[selected_ticker]
            sma_50 = stock_series.rolling(window=50).mean()
            sma_200 = stock_series.rolling(window=200).mean()
            
            chart_df = pd.DataFrame({
                f"{selected_ticker} 주가": stock_series,
                "50일 이동평균선": sma_50,
                "200일 이동평균선": sma_200
            })
            
            st.markdown(f"#### 📉 {selected_ticker} 이동평균선 추세")
            st.line_chart(chart_df, use_container_width=True)

            # RSI Calculation
            delta = stock_series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            latest_rsi = rsi.dropna().iloc[-1] if not rsi.dropna().empty else 50
            
            st.markdown(f"#### 📊 {selected_ticker} RSI 과열/냉각 지수: **{latest_rsi:.1f} / 100**")
            if latest_rsi >= 70:
                st.warning("⚠️ 과매수(과열) 상태입니다. 조정 가능성에 유의하세요.")
            elif latest_rsi <= 30:
                st.success("💡 과매도(냉각) 상태입니다. 반등 가능성이 높습니다.")
            else:
                st.info("ℹ️ 안정적이고 주가 변동 폭이 적당한 구간입니다.")

        # TAB 5
        with tab5:
            st.markdown("### 🛡️ 종목 간 상관관계")
            daily_returns = valid_data.pct_change().dropna()
            st.dataframe(daily_returns.corr().style.format("{:.2f}"), use_container_width=True)

        # TAB 6
        with tab6:
            st.markdown("### 📄 프로 심층 포트폴리오 진단 리포트 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            if not is_pro:
                st.warning("👑 Pro 요금제 전용 리포트입니다. 사이드바에서 Pro 요금제로 변경해 주세요.")
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    st.markdown("#### 1. 📌 비중 및 쏠림 진단")
                    st.write(f"- 구성 종목 수: {len(sum_data['valid_tickers'])}개")
                    st.write(f"- 초과 수익률: {sum_data['alpha']:+.2f}%p")
                    st.write(f"- 샤프지수: {sum_data['sharpe']:.2f}")

        # Sidebar Footer & Contact Email Update
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤝 서비스 / 제휴 문의")
        st.sidebar.caption("스톡랩 개발팀 문의:")
        st.sidebar.code("aseui995@gmail.com", language="text")
