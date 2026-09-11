import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="스톡랩 (StockLab) - 3초 포트폴리오 실험실", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS (콘텐츠형 리포트 카드 & 디자인 최적화)
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
    
    /* SNS 공유용 콘텐츠 리포트 카드 */
    .shareable-report-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 2px solid #38BDF8;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.15);
    }
    
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 12px 16px;
    }
    .kpi-title { font-size: 0.8rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; }
    .kpi-value { font-size: 1.5rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-sub { font-size: 0.85rem; font-weight: 600; }
    .kpi-pos { color: #10B981; }
    .kpi-neg { color: #EF4444; }
    
    .tutorial-box {
        background-color: #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 14px 18px;
        border-radius: 4px 8px 8px 4px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Data Fetcher
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

# Pro 결제 팝업 Modal
if hasattr(st, "dialog"):
    @st.dialog("💳 StockLab Pro 멤버십")
    def show_payment_modal():
        st.markdown("### 👑 AI 퀀트 리포트 & 자산 예측 구독")
        st.write("월 **$9.99** 로 나만의 스마트한 투자 리포트를 소장하세요.")
        st.markdown("""
        * 🔮 **1,000회 몬테카를로 미래 자산 예측**
        * 📄 **SNS 공유용 AI 심층 종합 리포트**
        * ⚡ **데이터 속도 최적화 모드**
        """)
        st.markdown("---")
        if st.button("💳 7일 무료 체험 시작하기", use_container_width=True):
            st.session_state['user_plan_status'] = "Pro (프리미엄)"
            st.success("🎉 Pro 멤버십이 승인되었습니다!")
            st.rerun()

# Sidebar: Version & Dev Mode
st.sidebar.markdown("### 📌 서비스 버전")
available_versions = ["1.0 (상용 버전)", "0.9 (베타)"]
selected_version_str = st.sidebar.selectbox("버전 선택", available_versions, index=0)
current_version = selected_version_str.split(" ")[0]

st.sidebar.markdown("<br>", unsafe_allow_html=True)

# Plan Selector & Developer Override
st.sidebar.markdown("### 👑 계정 요금제")
if 'user_plan_status' not in st.session_state:
    st.session_state['user_plan_status'] = "Free (일반 무료)"

# 개발자 프리패스 스위치
dev_pro = st.sidebar.toggle("🔑 개발자 Pro 권한 사용", value=True, help="체크하면 결제 없이 모든 Pro 기능을 바로 이용합니다.")

if dev_pro:
    is_pro = True
    st.sidebar.caption("✅ **관리자 Pro 권한 적용 중**")
else:
    selected_plan = st.sidebar.radio(
        "요금제 선택", 
        ["Free (일반 무료)", "Pro (프리미엄)"], 
        index=0 if st.session_state['user_plan_status'] == "Free (일반 무료)" else 1,
        key="plan_radio_input"
    )
    if selected_plan == "Pro (프리미엄)" and st.session_state['user_plan_status'] != "Pro (프리미엄)":
        if hasattr(st, "dialog"):
            show_payment_modal()
    is_pro = True if st.session_state['user_plan_status'] == "Pro (프리미엄)" else False

st.sidebar.markdown("---")

# Header Section
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<p class="main-header">🧪 스톡랩 (StockLab)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">3초 만에 검증하는 나만의 미국 주식 포트폴리오 시뮬레이터</p>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">v{current_version}</span></div>', unsafe_allow_html=True)

# 복원된 튜토리얼 가이드
with st.expander("📖 **[필독] StockLab 3초 사용 튜토리얼**", expanded=False):
    st.markdown("""
    <div class="tutorial-box">
    <b>💡 이렇게 사용해보세요!</b><br>
    1️⃣ <b>종목 담기</b>: 왼쪽 사이드바에서 원하는 투자 분야를 고르고 종목을 체크(✅)하세요.<br>
    2️⃣ <b>비중 설정</b>: <code>🎯 계산기</code> 탭에서 종목별 투자 비중(%)을 입력하고 <b>[🚀 계산 반영하기]</b>를 누르세요.<br>
    3️⃣ <b>결과 확인</b>: 내 포트폴리오가 S&P 500 시장 지수보다 얼마나 뛰어난지 한눈에 비교할 수 있습니다.
    </div>
    """, unsafe_allow_html=True)

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
    if st.sidebar.checkbox(f"✅ {ticker}", value=is_default, key=f"chk_v13_{selected_sector}_{ticker}"):
        selected_tickers.append(ticker)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 3. 투자 분석 기간")

today = datetime.today()
if 'start_d' not in st.session_state:
    st.session_state.start_d = today - timedelta(days=365)

col_q1, col_q2, col_q3, col_q4 = st.sidebar.columns(4)
if col_q1.button("올해", key="btn_ytd_v13"):
    st.session_state.start_d = datetime(today.year, 1, 1)
if col_q2.button("1년", key="btn_1y_v13"):
    st.session_state.start_d = today - timedelta(days=365)
if col_q3.button("3년", key="btn_3y_v13"):
    st.session_state.start_d = today - timedelta(days=365*3)
if col_q4.button("5년", key="btn_5y_v13"):
    st.session_state.start_d = today - timedelta(days=365*5)

start_date = st.session_state.start_d
end_date = today

analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('실시간 시세 불러오는 중...'):
        data = fetch_stock_data(tuple(sorted(analysis_tickers)), str(start_date.strftime('%Y-%m-%d')), str(end_date.strftime('%Y-%m-%d')))

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # Real-time Stock Cards
        st.markdown("##### 📌 선택한 종목 현재가")
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
            "📸 콘텐츠형 공유 리포트 👑"
        ])

        # TAB 1
        with tab1:
            st.markdown("### 📈 종목별 상대 성과 비교")
            comparison_df = valid_data.copy()
            if spy_data is not None:
                comparison_df['S&P 500 지수'] = spy_data
            norm_data = (comparison_df / comparison_df.iloc[0]) * 100
            st.line_chart(norm_data, use_container_width=True)

        # TAB 2
        with tab2:
            st.markdown("### 🎯 내 포트폴리오 비중 설정")
            with st.form("portfolio_form_v13"):
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
                            key=f"form_num_v13_{ticker}"
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
                    "S&P 500 시장평균": spy_cum_ret
                }).dropna()

                st.line_chart(chart_df, color=["#38BDF8", "#94A3B8"], use_container_width=True)

                tot_return = (port_cum_ret.iloc[-1] - 100)
                spy_tot_return = (spy_cum_ret.iloc[-1] - 100)
                alpha = tot_return - spy_tot_return
                ann_vol = port_daily_ret.std() * np.sqrt(252) * 100
                ann_ret = port_daily_ret.mean() * 252 * 100
                sharpe = (ann_ret - 4.0) / ann_vol if ann_vol != 0 else 0
                cum_roll_max = port_cum_ret.cummax()
                mdd = ((port_cum_ret - cum_roll_max) / cum_roll_max * 100).min()

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'tot_return': tot_return,
                    'spy_tot_return': spy_tot_return,
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
                st.warning("👑 Pro 전용 기능입니다. 사이드바 하단의 개발자 Pro 모드를 키거나 결제 후 사용하세요.")
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
                    
                    p50 = np.percentile(sim_results[-1], 50)
                    st.success(f"💡 1000회 시뮬레이션 결과: $10,000 투자 시 1년 후 예상 평균 금액은 **${p50:,.0f}** 입니다.")

        # TAB 4
        with tab4:
            st.markdown("### 🔍 선택 종목 상세 지표")
            selected_ticker = st.selectbox("분석 종목 선택", options=valid_tickers, index=0)
            stock_series = valid_data[selected_ticker]
            
            chart_df = pd.DataFrame({
                f"{selected_ticker} 주가": stock_series,
                "50일 이평선": stock_series.rolling(50).mean(),
                "200일 이평선": stock_series.rolling(200).mean()
            })
            st.line_chart(chart_df, use_container_width=True)

        # TAB 5
        with tab5:
            st.markdown("### 🛡️ 리스크 & 상관관계")
            daily_returns = valid_data.pct_change().dropna()
            st.dataframe(daily_returns.corr().style.format("{:.2f}"), use_container_width=True)

        # TAB 6: 콘텐츠형 리포트 (SNS 공유용 카드 디자인 적용)
        with tab6:
            st.markdown("### 📸 커뮤니티 공유용 퀀트 분석 카드 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            if not is_pro:
                st.warning("👑 Pro 전용 리포트 기능입니다.")
            else:
                sum_data = st.session_state.get('summary_data', None)
                if sum_data:
                    # SNS 공유용 캡처 카드 레이아웃
                    st.markdown(f"""
                    <div class="shareable-report-card">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h2 style="color:#38BDF8; margin:0;">🧪 StockLab Portfolio Report</h2>
                            <span style="color:#94A3B8; font-size:0.85rem;">{datetime.now().strftime('%Y-%m-%d')} 기준</span>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; text-align:center;">
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">포트폴리오 수익률</p>
                                <h3 style="color:#F8FAFC; margin:5px 0;">{sum_data['tot_return']:+.2f}%</h3>
                            </div>
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">시장 대비 초과 성과</p>
                                <h3 style="color:#10B981; margin:5px 0;">{sum_data['alpha']:+.2f}%p</h3>
                            </div>
                            <div>
                                <p style="color:#94A3B8; margin:0; font-size:0.85rem;">투자 효율성 (샤프)</p>
                                <h3 style="color:#F59E0B; margin:5px 0;">{sum_data['sharpe']:.2f}</h3>
                            </div>
                        </div>
                        <hr style="border-color:#334155; margin:15px 0;">
                        <p style="color:#E2E8F0; font-size:0.9rem; margin-bottom:5px;"><b>📊 자산 구성 비중:</b></p>
                        <p style="color:#94A3B8; font-size:0.85rem;">
                            {" | ".join([f"{t}: {w}%" for t, w in zip(sum_data['valid_tickers'], sum_data['weights']) if w > 0])}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    st.info("💡 위 카드를 캡처해서 블로그, 오픈채팅방, SNS에 공유해보세요!")
                else:
                    st.warning("탭 2에서 비중을 설정하고 [🚀 계산 반영하기]를 눌러주세요.")

        # Footer Contact Email
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤝 서비스 문의")
        st.sidebar.code("aseui995@gmail.com", language="text")
