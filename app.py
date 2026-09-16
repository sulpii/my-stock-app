import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="스톡랩 (StockLab)", 
    page_icon="🧪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        width: 290px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #94A3B8 !important;
    }
    .stApp { background-color: #0B0E14; color: #E2E8F0; font-family: 'Pretendard', sans-serif; }
    .sidebar-header { font-size: 1.8rem; font-weight: 800; color: #38BDF8; margin-bottom: 2px; }
    .sidebar-subheader { font-size: 0.85rem; color: #94A3B8; margin-bottom: 15px; }
    .badge-free { background-color: #334155; color: #94A3B8; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-lite { background-color: #0284C7; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-pro { background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .guide-box { background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; color: #CBD5E1; margin-bottom: 15px; }
    .plan-card { background: linear-gradient(135deg, #1E1B4B 0%, #111827 100%); border: 1px solid #6366F1; border-radius: 10px; padding: 15px; margin-top: 10px; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# 2. 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "StockLab", "subtitle": "주식 모의투자 & AI 시뮬레이터",
        "currency_select": "표시 통화",
        "tab_sim": "모의투자 & 자산", "tab_calc": "포트폴리오 분석기",
        "tab_tech": "기술적 분석 차트", "tab_risk": "퀀트 & 리스크 분석", "tab_predict": "몬테카를로 AI 예측",
        "buy_btn": "매수하기", "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab", "subtitle": "Paper Trading & AI Simulator",
        "currency_select": "Currency",
        "tab_sim": "Trading & Holdings", "tab_calc": "Portfolio Analyzer",
        "tab_tech": "Technical Chart", "tab_risk": "Quant Risk", "tab_predict": "Monte Carlo Forecast",
        "buy_btn": "Buy", "sell_btn": "Sell"
    }
}

POPULAR_STOCKS = {
    "애플 (AAPL)": "AAPL",
    "엔비디아 (NVDA)": "NVDA",
    "테슬라 (TSLA)": "TSLA",
    "삼성전자 (005930.KS)": "005930.KS",
    "SK하이닉스 (000660.KS)": "000660.KS",
    "S&P500 ETF (SPY)": "SPY"
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rates():
    try:
        krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        jpy = yf.Ticker("JPY=X").history(period="1d")['Close'].iloc[-1]
        return {"USD": (1.0, "$"), "KRW": (krw, "₩"), "JPY": (jpy, "¥")}
    except Exception:
        return {"USD": (1.0, "$"), "KRW": (1350.0, "₩"), "JPY": (150.0, "¥")}

@st.cache_data(ttl=1800, show_spinner=False)
def fetch_multi_ticker_data(tickers, start, end):
    try:
        df = yf.download(tickers, start=start, end=end, progress=False)['Close']
        if isinstance(df, pd.Series):
            df = df.to_frame()
        return df.dropna()
    except Exception:
        return None

# 세션 상태 초기화
if 'cash' not in st.session_state: st.session_state['cash'] = 100000000.0
if 'portfolio' not in st.session_state: st.session_state['portfolio'] = {}
if 'search_ticker' not in st.session_state: st.session_state['search_ticker'] = "AAPL"
if 'user_plan' not in st.session_state: st.session_state['user_plan'] = "Free" # Free, Lite, Pro

# ====================================================
# 👈 사이드바
# ====================================================
selected_lang = st.sidebar.selectbox("🌐 Language", ["한국어", "English"], index=0)
L = LANG_DICT.get(selected_lang, LANG_DICT["한국어"])

st.sidebar.markdown(f'<p class="sidebar-header">🧪 {L["title"]}</p>', unsafe_allow_html=True)
st.sidebar.markdown(f'<p class="sidebar-subheader">{L["subtitle"]}</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

current_plan = st.session_state['user_plan']
st.sidebar.markdown("##### 👤 나의 멤버십 현황")

plan_col1, plan_col2 = st.sidebar.columns([2, 1])
with plan_col1:
    if current_plan == "Free": st.markdown('<span class="badge-free">Free 모드</span>', unsafe_allow_html=True)
    elif current_plan == "Lite": st.markdown('<span class="badge-lite">⚡ Lite 모드</span>', unsafe_allow_html=True)
    else: st.markdown('<span class="badge-pro">👑 Pro 모드</span>', unsafe_allow_html=True)

with plan_col2:
    # 테스트용 플랜 전환 버튼
    new_plan = st.selectbox("플랜변경(테스트)", ["Free", "Lite", "Pro"], index=["Free", "Lite", "Pro"].index(current_plan), label_visibility="collapsed")
    if new_plan != current_plan:
        st.session_state['user_plan'] = new_plan
        st.rerun()

st.sidebar.markdown("---")

# ====================================================
# 메인 화면 영역
# ====================================================
st.markdown("### 🔍 기준 종목 선택")
col_s1, col_s2 = st.columns([2, 3])
with col_s1:
    quick_choice = st.selectbox("🔥 인기 추천 종목 퀵 선택", ["선택 안함"] + list(POPULAR_STOCKS.keys()))
    if quick_choice != "선택 안함": st.session_state['search_ticker'] = POPULAR_STOCKS[quick_choice]

with col_s2:
    input_ticker = st.text_input("직접 티커 입력 (예: AAPL, TSLA, 005930.KS)", value=st.session_state['search_ticker'])
    if input_ticker: st.session_state['search_ticker'] = input_ticker.strip().upper()

current_ticker = st.session_state['search_ticker']

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"💵 {L['tab_sim']}", 
    f"🧮 {L['tab_calc']}", 
    f"📈 {L['tab_tech']}", 
    f"📊 {L['tab_risk']}", 
    f"🎯 {L['tab_predict']}"
])

# ----------------------------------------------------
# TAB 1: 모의투자 (생략 없이 유지)
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box">💡 <b>가상 모의투자</b>: 초기 자산 1억 원으로 자유롭게 거래를 진행해보세요.</div>', unsafe_allow_html=True)
    st.metric("현재 잔고", f"₩{st.session_state['cash']:,.0f}")

# ----------------------------------------------------
# 🧮 [대폭 강화] TAB 2: 포트폴리오 분석기 (백테스트, 상관계수, 리밸런싱)
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box">💡 <b>포트폴리오 통합 분석</b>: 선택한 종목들의 과거 백테스팅, 종목 간 상관관계, 리밸런싱 계산까지 통합 지원합니다.</div>', unsafe_allow_html=True)
    
    # 1. 종목 및 비중 선택
    selected_port_tickers = st.multiselect(
        "📌 분석할 포트폴리오 종목 선택", 
        list(POPULAR_STOCKS.values()) + ["GOOGL", "AMZN", "MSFT"],
        default=["AAPL", "NVDA", "SPY"]
    )
    
    if len(selected_port_tickers) >= 2:
        weights = {}
        st.markdown("##### ⚖️ 종목별 투자 비중 설정 (%)")
        cols = st.columns(len(selected_port_tickers))
        default_w = round(100 / len(selected_port_tickers), 1)
        
        for idx, t in enumerate(selected_port_tickers):
            with cols[idx]:
                weights[t] = st.number_input(f"{t} 비중", min_value=0.0, max_value=100.0, value=default_w, step=5.0)
                
        tot_weight = sum(weights.values())
        if abs(tot_weight - 100.0) > 0.1:
            st.warning(f"⚠️ 비중 합계가 {tot_weight}%입니다. (100%로 맞춰주세요)")
        else:
            st.success("✅ 비중 합계: 100%")
            
        # 데이터 수집
        today = datetime.today()
        start_3y = today - timedelta(days=365*2)
        df_port = fetch_multi_ticker_data(selected_port_tickers, str(start_3y.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))
        
        if df_port is not None and not df_port.empty:
            # Daily Returns & Portfolio Returns
            daily_returns = df_port.pct_change().dropna()
            w_list = np.array([weights[t]/100.0 for t in selected_port_tickers])
            port_returns = (daily_returns * w_list).sum(axis=1)
            cum_returns = (1 + port_returns).cumprod()
            
            st.markdown("---")
            
            # Sub Tabs
            sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📈 과거 성과 백테스트", "🔗 상관계수 히트맵", "⚖️ 리밸런싱 계산기"])
            
            with sub_tab1:
                # 성과 지표
                total_ret = (cum_returns.iloc[-1] - 1) * 100
                cagr = ((cum_returns.iloc[-1]) ** (365 / len(cum_returns)) - 1) * 100
                peak = cum_returns.cummax()
                mdd = ((cum_returns - peak) / peak).min() * 100
                
                m1, m2, m3 = st.columns(3)
                m1.metric("총 수익률 (2년)", f"{total_ret:+.2f}%")
                m2.metric("연평균 수익률 (CAGR)", f"{cagr:.2f}%")
                m3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
                
                fig_bt = px.line(cum_returns, labels={'value': '자산 가치 (1.0 = 시작점)', 'index': '날짜'}, title="포트폴리오 누적 성과 추이")
                fig_bt.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_bt, use_container_width=True)

            with sub_tab2:
                # 상관계수
                st.markdown("##### 🔗 종목 간 상관계수 (Correlation)")
                st.caption("1.0에 가까울수록 같이 움직이고, 0에 가까울수록 분산투자 효과가 큽니다.")
                corr_matrix = daily_returns.corr()
                fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="Blues", aspect="auto")
                fig_corr.update_layout(template="plotly_dark", height=350)
                st.plotly_chart(fig_corr, use_container_width=True)

            with sub_tab3:
                # 리밸런싱
                st.markdown("##### ⚖️ 목표 비중 맞춤 리밸런싱 주문 계산")
                total_inv = st.number_input("현재 포트폴리오 총 평가금액 (원)", value=10000000, step=1000000)
                
                rebal_data = []
                for t in selected_port_tickers:
                    target_amt = total_inv * (weights[t] / 100.0)
                    last_p = df_port[t].iloc[-1]
                    target_shares = target_amt / last_p
                    rebal_data.append({
                        "종목": t,
                        "목표 비중": f"{weights[t]}%",
                        "목표 금액": f"₩{target_amt:,.0f}",
                        "현재가": f"{last_p:,.2f}",
                        "필요 목표 주수": f"{target_shares:.2f} 주"
                    })
                st.table(pd.DataFrame(rebal_data))
    else:
        st.info("포트폴리오 분석을 위해 최소 2개 이상의 종목을 선택해 주세요.")

# ----------------------------------------------------
# TAB 3 & 4: 기술적 차트 / 퀀트 리스크 (기존 동일)
# ----------------------------------------------------
with tab3: st.write("기술적 분석 차트 영역")
with tab4: st.write("퀀트 리스크 분석 영역")

# ----------------------------------------------------
# 🎯 [Lite / Pro 적용] TAB 5: 몬테카를로 시뮬레이션
# ----------------------------------------------------
with tab5:
    st.markdown('<div class="guide-box">💡 <b>몬테카를로 확률 예측</b>: 유료 플랜(Lite/Pro)에서는 복수 종목 분할 투자 시뮬레이션을 지원합니다.</div>', unsafe_allow_html=True)
    
    # 🔒 유료 기능 제한 로직
    if current_plan == "Free":
        st.info("💡 **Free 플랜 사용 중**: 단일 종목 시뮬레이션만 이용 가능합니다.")
        st.warning("⚡ **Lite 및 Pro 멤버십으로 업그레이드하시면 여러 종목을 분할 투자한 포트폴리오 몬테카를로 시뮬레이션을 이용할 수 있습니다!**")
        
        # 단일 종목 처리
        selected_mc_tickers = [current_ticker]
        mc_weights = {current_ticker: 100.0}
    else:
        st.success(f"🔓 **{current_plan} 멤버십 혜택**: 복수 종목 분할 투자 시뮬레이션 모드가 활성화되었습니다!")
        selected_mc_tickers = st.multiselect(
            "🎲 시뮬레이션할 포트폴리오 종목 구성", 
            list(POPULAR_STOCKS.values()) + ["GOOGL", "AMZN", "MSFT"],
            default=["AAPL", "NVDA"]
        )
        
        if len(selected_mc_tickers) > 1:
            mc_weights = {}
            cols = st.columns(len(selected_mc_tickers))
            def_w = round(100 / len(selected_mc_tickers), 1)
            for idx, t in enumerate(selected_mc_tickers):
                with cols[idx]:
                    mc_weights[t] = st.number_input(f"{t} 비중(%)", min_value=0.0, max_value=100.0, value=def_w, key=f"mc_w_{t}")
        else:
            mc_weights = {selected_mc_tickers[0]: 100.0} if selected_mc_tickers else {}

    st.markdown("---")
    
    if selected_mc_tickers:
        col_m1, col_m2, col_m3 = st.columns([1.5, 1.5, 1])
        with col_m1:
            init_budget = st.number_input("💰 투자 예산 (원금)", min_value=100000, value=10000000, step=1000000)
        with col_m2:
            pred_days = st.slider("📆 예측 기간 (일수)", min_value=30, max_value=252, value=90, step=30)
        with col_m3:
            num_sims = 1000 if current_plan == "Free" else (3000 if current_plan == "Lite" else 10000)
            st.caption(f"시뮬레이션 횟수: **{num_sims:,}회**")
            
        # 시뮬레이션 실행
        today = datetime.today()
        start_1y = today - timedelta(days=365)
        df_mc = fetch_multi_ticker_data(selected_mc_tickers, str(start_1y.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))
        
        if df_mc is not None and not df_mc.empty:
            daily_returns = df_mc.pct_change().dropna()
            
            # 단일 vs 복수 종목 포트폴리오 수익률 산출
            if len(selected_mc_tickers) == 1:
                port_daily_ret = daily_returns.iloc[:, 0]
            else:
                w_arr = np.array([mc_weights[t]/100.0 for t in selected_mc_tickers])
                port_daily_ret = (daily_returns * w_arr).sum(axis=1)
                
            u = port_daily_ret.mean()
            var = port_daily_ret.var()
            drift = u - (0.5 * var)
            stdev = port_daily_ret.std()
            
            np.random.seed(42)
            sim_daily_returns = np.exp(drift + stdev * np.random.normal(0, 1, (pred_days, num_sims)))
            
            asset_paths = np.zeros_like(sim_daily_returns)
            asset_paths[0] = init_budget
            for t in range(1, pred_days):
                asset_paths[t] = asset_paths[t - 1] * sim_daily_returns[t]
                
            final_assets = asset_paths[-1]
            a_10 = np.percentile(final_assets, 10)
            a_50 = np.median(final_assets)
            a_90 = np.percentile(final_assets, 90)
            profit_prob = (final_assets > init_budget).sum() / num_sims * 100

            st.markdown(f"##### 📊 {init_budget:,.0f}원 투자 시 {pred_days}일 후 예상 자산 평가")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("🎯 예상 자산 (중앙값)", f"₩{a_50:,.0f}", f"{((a_50 - init_budget)/init_budget)*100:+.1f}%")
            r2.metric("🚀 상위 10% (Best)", f"₩{a_90:,.0f}", f"{((a_90 - init_budget)/init_budget)*100:+.1f}%")
            r3.metric("❄️ 하위 10% (Worst)", f"₩{a_10:,.0f}", f"{((a_10 - init_budget)/init_budget)*100:+.1f}%")
            r4.metric("📈 원금 보존/수익 확률", f"{profit_prob:.1f}%")

            # 차트
            fig_mc = go.Figure()
            sample_paths = asset_paths[:, :min(100, num_sims)]
            for i in range(sample_paths.shape[1]):
                fig_mc.add_trace(go.Scatter(y=sample_paths[:, i], mode='lines', line=dict(width=0.5, color='rgba(56, 189, 248, 0.1)'), showlegend=False))
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 90, axis=1), name="상위 10%", line=dict(color='#10B981', width=2)))
            fig_mc.add_trace(go.Scatter(y=np.median(asset_paths, axis=1), name="중앙값 (50%)", line=dict(color='#F59E0B', width=2.5)))
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 10, axis=1), name="하위 10%", line=dict(color='#EF4444', width=2)))
            fig_mc.update_layout(template="plotly_dark", height=380, xaxis=dict(title="경과 일수 (Day)"), yaxis=dict(title="예상 평가액 (₩)"))
            
            st.plotly_chart(fig_mc, use_container_width=True)
