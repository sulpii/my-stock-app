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
        font-size: 1.4rem !important;
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
    
    .badge-free {
        background-color: #334155; color: #94A3B8; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 700;
    }
    .badge-lite {
        background-color: #0284C7; color: #FFFFFF; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 700;
    }
    .badge-pro {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;
    }
    .guide-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 12px 16px;
        border-radius: 6px; font-size: 0.9rem; color: #CBD5E1; margin-bottom: 15px;
    }
    .plan-card {
        background: linear-gradient(135deg, #1E1B4B 0%, #111827 100%);
        border: 1px solid #6366F1; border-radius: 10px; padding: 15px; margin-top: 10px; margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "StockLab", "subtitle": "주식 모의투자 & AI 시뮬레이터",
        "currency_select": "표시 통화",
        "tab_sim": "모의투자 & 자산", "tab_calc": "포트폴리오 계산기",
        "tab_tech": "기술적 분석 차트", "tab_risk": "퀀트 & 리스크 분석", "tab_predict": "몬테카를로 AI 예측",
        "buy_btn": "매수하기", "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab", "subtitle": "Paper Trading & AI Simulator",
        "currency_select": "Currency",
        "tab_sim": "Trading & Holdings", "tab_calc": "Portfolio Calculator",
        "tab_tech": "Technical Chart", "tab_risk": "Quant Risk", "tab_predict": "Monte Carlo Forecast",
        "buy_btn": "Buy", "sell_btn": "Sell"
    }
}

POPULAR_STOCKS = {
    "🔥 인기: 애플 (AAPL)": "AAPL",
    "🔥 인기: 엔비디아 (NVDA)": "NVDA",
    "🔥 인기: 테슬라 (TSLA)": "TSLA",
    "🔥 인기: 삼성전자 (005930.KS)": "005930.KS",
    "🔥 인기: SK하이닉스 (000660.KS)": "000660.KS",
    "🔥 인기: S&P500 ETF (SPY)": "SPY"
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
def fetch_single_ticker_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df.dropna()
    except Exception:
        return None

# 세션 상태 초기화
INIT_CASH = 100000000.0

if 'cash' not in st.session_state:
    st.session_state['cash'] = INIT_CASH
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {}
if 'search_ticker' not in st.session_state:
    st.session_state['search_ticker'] = "AAPL"
if 'user_plan' not in st.session_state:
    st.session_state['user_plan'] = "Free"  # Free, Lite, Pro
if 'trial_end_date' not in st.session_state:
    st.session_state['trial_end_date'] = None

# ====================================================
# 💳 결제 및 멤버십 구매 팝업 모달 (Dialog)
# ====================================================
@st.dialog("💳 StockLab 플랜 결제 및 변경")
def show_buy_dialog():
    st.markdown("### 플랜을 선택하고 결제를 진행하세요")
    
    plan_choice = st.radio(
        "요금제 선택",
        [
            "⚡ Lite 플랜 (₩9,800 / 월) - 3,000회 시뮬레이션",
            "👑 Pro 플랜 (₩39,000 / 월) - 10,000회 시뮬레이션 + 고속 분석"
        ]
    )
    
    st.text_input("💳 카드 번호", placeholder="0000 - 0000 - 0000 - 0000")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.text_input("유효기간", placeholder="MM/YY")
    with col_c2:
        st.text_input("CVC", placeholder="3자리 숫자")
        
    st.markdown("---")
    if st.button("🚀 결제 완료 및 구독 시작", use_container_width=True, type="primary"):
        if "Lite" in plan_choice:
            st.session_state['user_plan'] = "Lite"
            st.success("🎉 Lite 플랜 구독이 시작되었습니다!")
        else:
            st.session_state['user_plan'] = "Pro"
            st.success("🎉 Pro 플랜 구독이 시작되었습니다!")
        st.session_state['trial_end_date'] = None
        st.rerun()

# ====================================================
# 👈 사이드바 구성
# ====================================================
selected_lang = st.sidebar.selectbox("🌐 Language", ["한국어", "English"], index=0)
L = LANG_DICT.get(selected_lang, LANG_DICT["한국어"])

st.sidebar.markdown(f'<p class="sidebar-header">🧪 {L["title"]}</p>', unsafe_allow_html=True)
st.sidebar.markdown(f'<p class="sidebar-subheader">{L["subtitle"]}</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

rates = get_exchange_rates()
curr_choice = st.sidebar.selectbox(L['currency_select'], ["KRW (₩)", "USD ($)", "JPY (¥)"], index=0)
curr_key = curr_choice.split(" ")[0]
fx_rate, curr_symbol = rates[curr_key]

# 멤버십 플랜 상태 표출 및 변경 영역
current_plan = st.session_state['user_plan']

st.sidebar.markdown("##### 👤 나의 멤버십 현황")
if current_plan == "Free":
    st.sidebar.markdown('현재 이용 플랜: <span class="badge-free">Free (1,000회)</span>', unsafe_allow_html=True)
    
    st.sidebar.markdown("""
    <div class="plan-card">
        <div style="font-weight: 800; color: #38BDF8; font-size: 0.9rem;">🎁 2주 무료 체험 혜택</div>
        <div style="font-size: 0.78rem; color: #CBD5E1; margin-top: 4px;">
            지금 신청 시 <b>14일간 Pro 모드 (10,000회 시뮬레이션)</b>를 조건 없이 무료로 이용할 수 있습니다.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.sidebar.button("🎁 Pro 2주 무료 체험 시작", use_container_width=True):
        st.session_state['user_plan'] = "Pro"
        st.session_state['trial_end_date'] = datetime.today() + timedelta(days=14)
        st.success("🎉 2주 무료 체험이 시작되었습니다!")
        st.rerun()
        
    if st.sidebar.button("💳 유료 멤버십 결제하기", use_container_width=True, type="primary"):
        show_buy_dialog()

elif current_plan == "Lite":
    st.sidebar.markdown('현재 이용 플랜: <span class="badge-lite">Lite (3,000회)</span>', unsafe_allow_html=True)
    st.sidebar.write("월 ₩9,800 구독 중")
    if st.sidebar.button("👑 Pro로 업그레이드", use_container_width=True, type="primary"):
        show_buy_dialog()
    if st.sidebar.button("Free 모드로 변경", use_container_width=True):
        st.session_state['user_plan'] = "Free"
        st.rerun()

elif current_plan == "Pro":
    st.sidebar.markdown('현재 이용 플랜: <span class="badge-pro">👑 Pro (10,000회)</span>', unsafe_allow_html=True)
    if st.session_state['trial_end_date']:
        remaining = (st.session_state['trial_end_date'] - datetime.today()).days + 1
        st.sidebar.info(f"⏳ 2주 무료 체험 중 (남은 기간: {remaining}일)")
    
    if st.sidebar.button("플랜 변경 / 해지", use_container_width=True):
        st.session_state['user_plan'] = "Free"
        st.session_state['trial_end_date'] = None
        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("ⓒ StockLab All Rights Reserved.")

# ====================================================
# 메인 화면 영역
# ====================================================
st.markdown("### 🔍 종목 검색 및 선택")
col_s1, col_s2 = st.columns([2, 3])

with col_s1:
    quick_choice = st.selectbox("🔥 인기 추천 종목 퀵 선택", ["선택 안함"] + list(POPULAR_STOCKS.keys()))
    if quick_choice != "선택 안함":
        st.session_state['search_ticker'] = POPULAR_STOCKS[quick_choice]

with col_s2:
    input_ticker = st.text_input("직접 티커 검색 (예: AAPL, TSLA, 005930.KS)", value=st.session_state['search_ticker'])
    if input_ticker:
        st.session_state['search_ticker'] = input_ticker.strip().upper()

current_ticker = st.session_state['search_ticker']

# 시세 데이터 로딩
today = datetime.today()
start_date = today - timedelta(days=365)

with st.spinner(f"'{current_ticker}' 시세 데이터 로딩 중..."):
    ticker_df = fetch_single_ticker_data(current_ticker, str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

col_m1, col_m2 = st.columns([4, 1])
with col_m2:
    if current_plan == "Pro":
        st.markdown('<div style="text-align:right;"><span class="badge-pro">👑 Pro Plan</span></div>', unsafe_allow_html=True)
    elif current_plan == "Lite":
        st.markdown('<div style="text-align:right;"><span class="badge-lite">Lite Plan</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:right;"><span class="badge-free">Free Plan</span></div>', unsafe_allow_html=True)

# 탭 구성
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    f"💵 {L['tab_sim']}", 
    f"🧮 {L['tab_calc']}", 
    f"📈 {L['tab_tech']}", 
    f"📊 {L['tab_risk']}", 
    f"🎯 {L['tab_predict']}"
])

c_krw = rates["KRW"][0]
disp_scale = (fx_rate / c_krw) if curr_key != "KRW" else 1.0

# ----------------------------------------------------
# 💵 TAB 1: 모의투자 & 자산 현황
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box">💡 <b>가상 모의투자</b>: 초기 자산 1억 원으로 실시간 주식을 거래하고 포트폴리오를 관리해보세요.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty:
        curr_price_raw = ticker_df['Close'].iloc[-1]
        
        # 한국 주식(.KS, .KQ)은 원화 기준, 해외주식은 USD 기준 환율 적용
        if current_ticker.endswith(".KS") or current_ticker.endswith(".KQ"):
            curr_price_disp = curr_price_raw * disp_scale
        else:
            curr_price_disp = curr_price_raw * (rates["KRW"][0] if curr_key == "KRW" else fx_rate)

        st.markdown(f"#### 📌 {current_ticker} 현재가: **{curr_symbol}{curr_price_disp:,.2f}**")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            trade_qty = st.number_input("매수/매도 수량", min_value=1, value=10, step=1)
            buy_btn = st.button(f"🟢 {L['buy_btn']}", use_container_width=True)
        with col_t2:
            st.write("") # 높이 맞춤용
            st.write("")
            sell_btn = st.button(f"🔴 {L['sell_btn']}", use_container_width=True)
            
        if buy_btn:
            total_cost = curr_price_disp * trade_qty
            if st.session_state['cash'] >= total_cost:
                st.session_state['cash'] -= total_cost
                if current_ticker in st.session_state['portfolio']:
                    prev_qty, prev_avg = st.session_state['portfolio'][current_ticker]
                    new_qty = prev_qty + trade_qty
                    new_avg = ((prev_qty * prev_avg) + total_cost) / new_qty
                    st.session_state['portfolio'][current_ticker] = (new_qty, new_avg)
                else:
                    st.session_state['portfolio'][current_ticker] = (trade_qty, curr_price_disp)
                st.success(f"{current_ticker} {trade_qty}주 매수 완료!")
                st.rerun()
            else:
                st.error("현금이 부족합니다!")

        if sell_btn:
            if current_ticker in st.session_state['portfolio'] and st.session_state['portfolio'][current_ticker][0] >= trade_qty:
                prev_qty, prev_avg = st.session_state['portfolio'][current_ticker]
                st.session_state['cash'] += curr_price_disp * trade_qty
                if prev_qty == trade_qty:
                    del st.session_state['portfolio'][current_ticker]
                else:
                    st.session_state['portfolio'][current_ticker] = (prev_qty - trade_qty, prev_avg)
                st.success(f"{current_ticker} {trade_qty}주 매도 완료!")
                st.rerun()
            else:
                st.error("보유 수량이 부족합니다!")

        st.markdown("---")
        st.markdown("##### 💼 나의 보유 자산 현황")
        st.metric("보유 현금", f"{curr_symbol}{st.session_state['cash'] * disp_scale:,.0f}")
        
        if st.session_state['portfolio']:
            port_data = []
            for t, (q, avg_p) in st.session_state['portfolio'].items():
                port_data.append({"종목": t, "보유수량": q, "평균단가": f"{curr_symbol}{avg_p:,.2f}"})
            st.table(pd.DataFrame(port_data))
        else:
            st.info("현재 보유 중인 주식이 없습니다.")
    else:
        st.error("주가 데이터를 불러올 수 없습니다.")

# ----------------------------------------------------
# 🧮 TAB 2: 포트폴리오 계산기
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box">💡 <b>비중 분석</b>: 자산 비중을 조정하며 포트폴리오 구성을 검토하세요.</div>', unsafe_allow_html=True)
    
    st.markdown("##### 📐 자산 비중 시뮬레이터")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        w_stock = st.slider("주식 비중 (%)", 0, 100, 70)
    with col_p2:
        w_bond = 100 - w_stock
        st.slider("채권 비중 (%)", 0, 100, w_bond, disabled=True)
        
    fig_pie = px.pie(
        names=["주식", "채권"], 
        values=[w_stock, w_bond], 
        hole=0.4,
        color_discrete_sequence=['#38BDF8', '#6366F1']
    )
    fig_pie.update_layout(template="plotly_dark", height=300)
    st.plotly_chart(fig_pie, use_container_width=True)

# ----------------------------------------------------
# 📈 TAB 3: 기술적 분석 차트
# ----------------------------------------------------
with tab3:
    st.markdown(f'<div class="guide-box">💡 <b>기술적 차트</b>: {current_ticker} 종목의 이동평균선과 거래량을 분석합니다.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty:
        df_chart = ticker_df.copy()
        df_chart['MA20'] = df_chart['Close'].rolling(20).mean()
        df_chart['MA60'] = df_chart['Close'].rolling(60).mean()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        fig.add_trace(go.Candlestick(
            x=df_chart.index,
            open=df_chart['Open'], high=df_chart['High'],
            low=df_chart['Low'], close=df_chart['Close'], name="주가"
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA20'], name="20일 이평선", line=dict(color='#F59E0B', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['MA60'], name="60일 이평선", line=dict(color='#10B981', width=1)), row=1, col=1)
        
        fig.add_trace(go.Bar(x=df_chart.index, y=df_chart['Volume'], name="거래량", marker_color='#6366F1'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=450, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# 📊 TAB 4: 퀀트 & 리스크 분석
# ----------------------------------------------------
with tab4:
    st.markdown(f'<div class="guide-box">💡 <b>퀀트 리스크 분석</b>: 최근 1년 변동성, 샤프 지수, 최대 낙폭(MDD)을 산출합니다.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty:
        daily_ret = ticker_df['Close'].pct_change().dropna()
        volatility = daily_ret.std() * np.sqrt(252) * 100
        sharpe = (daily_ret.mean() * 252) / (daily_ret.std() * np.sqrt(252)) if daily_ret.std() != 0 else 0
        
        cum_ret = (1 + daily_ret).cumprod()
        peak = cum_ret.cummax()
        mdd = ((cum_ret - peak) / peak).min() * 100
        
        q1, q2, q3 = st.columns(3)
        q1.metric("연 변동성", f"{volatility:.2f}%")
        q2.metric("샤프 지수", f"{sharpe:.2f}")
        q3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")

# ----------------------------------------------------
# 🎯 TAB 5: 몬테카를로 AI 예측 (종목/예산/목표 설정 포함)
# ----------------------------------------------------
with tab5:
    st.markdown(f'<div class="guide-box">💡 <b>몬테카를로 예산 기반 예측</b>: 종목과 투자 예산(원금)을 설정하면 미래 자산 가치와 수익/손실 확률을 시뮬레이션합니다.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty and len(ticker_df) > 30:
        df_mc = ticker_df.copy()
        last_price = df_mc['Close'].iloc[-1]
        
        # ⚙️ 종목 / 예산 / 기간 설정 박스
        st.markdown("##### ⚙️ 시뮬레이션 조건 및 예산 설정")
        col_m1, col_m2, col_m3 = st.columns([1.5, 1.5, 1])
        
        with col_m1:
            init_budget = st.number_input("💰 투자 예산 (원금)", min_value=100000, value=10000000, step=1000000, format="%d")
            st.caption(f"선택 종목: **{current_ticker}** (현재가: {last_price:,.2f})")
            
        with col_m2:
            pred_days = st.slider("📆 미래 예측 기간 (일수)", min_value=30, max_value=252, value=90, step=30)
            
        with col_m3:
            # 플랜별 시뮬레이션 횟수
            if current_plan == "Free":
                num_simulations = 1000
                st.info("💡 **Free**: 1,000회")
            elif current_plan == "Lite":
                num_simulations = 3000
                st.success("⚡ **Lite**: 3,000회")
            else:
                num_simulations = st.slider("🎲 횟수 (Pro)", min_value=3000, max_value=10000, value=10000, step=1000)

        # 연산 실행
        log_returns = np.log(df_mc['Close'] / df_mc['Close'].shift(1)).dropna()
        u = log_returns.mean()
        var = log_returns.var()
        drift = u - (0.5 * var)
        stdev = log_returns.std()
        
        np.random.seed(42)
        daily_returns = np.exp(drift + stdev * np.random.normal(0, 1, (pred_days, num_simulations)))
        
        price_list = np.zeros_like(daily_returns)
        price_list[0] = last_price
        for t in range(1, pred_days):
            price_list[t] = price_list[t - 1] * daily_returns[t]
            
        final_prices = price_list[-1]
        
        # 주가 수익률 계산 -> 예산 기반 자산 가치 계산
        return_rates = (final_prices - last_price) / last_price
        final_assets = init_budget * (1 + return_rates)
        
        a_10 = np.percentile(final_assets, 10)
        a_50 = np.median(final_assets)
        a_90 = np.percentile(final_assets, 90)
        
        profit_prob = (return_rates > 0).sum() / num_simulations * 100

        st.markdown("---")
        
        # 예산 기준 결과 리포트
        st.markdown(f"##### 📊 {init_budget:,.0f}원 투자 시 {pred_days}일 후 예상 자산 평가")
        
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("🎯 예상 자산 (중앙값)", f"₩{a_50:,.0f}", f"{((a_50 - init_budget)/init_budget)*100:+.1f}%")
        r2.metric("🚀 상위 10% (Best)", f"₩{a_90:,.0f}", f"{((a_90 - init_budget)/init_budget)*100:+.1f}%")
        r3.metric("❄️ 하위 10% (Worst)", f"₩{a_10:,.0f}", f"{((a_10 - init_budget)/init_budget)*100:+.1f}%")
        r4.metric("📈 원금 보존/수익 확률", f"{profit_prob:.1f}%")

        st.markdown("---")
        
        # 차트 시각화 (자산 기반 경로)
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.markdown(f"##### 🎲 자산 평가액 추이 시뮬레이션 ({num_simulations:,}회)")
            fig_mc = go.Figure()
            
            # 주가 경로를 예산으로 환산
            asset_paths = (price_list / last_price) * init_budget
            sample_paths = asset_paths[:, :min(100, num_simulations)]
            
            for i in range(sample_paths.shape[1]):
                fig_mc.add_trace(go.Scatter(
                    y=sample_paths[:, i], 
                    mode='lines', 
                    line=dict(width=0.6, color='rgba(56, 189, 248, 0.12)'), 
                    showlegend=False
                ))
                
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 90, axis=1), name="상위 10%", line=dict(color='#10B981', width=2)))
            fig_mc.add_trace(go.Scatter(y=np.median(asset_paths, axis=1), name="중앙값 (50%)", line=dict(color='#F59E0B', width=2.5)))
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 10, axis=1), name="하위 10%", line=dict(color='#EF4444', width=2)))

            fig_mc.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title="경과 일수 (Day)"),
                yaxis=dict(title="예상 자산 평가액 (₩)")
            )
            st.plotly_chart(fig_mc, use_container_width=True)

        with col_c2:
            st.markdown("##### 📊 최종 예상 자산 분포")
            fig_hist = px.histogram(
                x=final_assets, nbins=50, 
                color_discrete_sequence=['#A855F7'],
                labels={'x': '최종 자산 (₩)'}
            )
            fig_hist.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis=dict(title="빈도수")
            )
            st.plotly_chart(fig_hist, use_container_width=True)

    else:
        st.warning("몬테카를로 시뮬레이션을 수행하기 위한 충분한 주가 데이터가 존재하지 않습니다.")
