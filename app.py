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
st.sidebar.markdown("📌 **버전 정보**: `v1.3.0 (3-Tier Plan)`")

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
# TAB 1: 모의투자 및 보유 자산
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box">💡 <b>가상 모의투자</b>: 초기 자산 1억 원으로 실시간 주식을 거래하고 포트폴리오를 관리해보세요.</div>', unsafe_allow_html=True)
    
    eval_stock_val = 0.0
    portfolio_rows = []
    
    for t, holdings in st.session_state['portfolio'].items():
        qty = holdings['qty']
        if qty > 0:
            t_data = fetch_single_ticker_data(t, str(today - timedelta(days=5)), str(today))
            if t_data is not None and not t_data.empty:
                last_p = t_data['Close'].iloc[-1]
                p_krw = last_p if t.endswith(".KS") else last_p * c_krw
                current_val = p_krw * qty
                eval_stock_val += current_val
                
                avg_p = holdings['avg_price']
                profit_krw = (p_krw - avg_p) * qty
                profit_rate = ((p_krw - avg_p) / avg_p) * 100 if avg_p > 0 else 0
                
                portfolio_rows.append({
                    "종목": t,
                    "보유수량": f"{qty:,}주",
                    "평균단가": f"{curr_symbol}{avg_p * disp_scale:,.0f}",
                    "현재가": f"{curr_symbol}{p_krw * disp_scale:,.0f}",
                    "평가금액": f"{curr_symbol}{current_val * disp_scale:,.0f}",
                    "평가손익": f"{curr_symbol}{profit_krw * disp_scale:,.0f} ({profit_rate:+.2f}%)"
                })

    total_asset_krw = st.session_state['cash'] + eval_stock_val
    
    k1, k2, k3, k4 = st.columns([1.3, 1.3, 1.3, 0.9])
    k1.metric("💰 총 자산", f"{curr_symbol}{total_asset_krw * disp_scale:,.0f}")
    k2.metric("💳 보유 현금", f"{curr_symbol}{st.session_state['cash'] * disp_scale:,.0f}")
    k3.metric("🏢 주식 평가액", f"{curr_symbol}{eval_stock_val * disp_scale:,.0f}")
    with k4:
        st.write("")
        if st.button("🔄 잔고 초기화", use_container_width=True):
            st.session_state['cash'] = INIT_CASH
            st.session_state['portfolio'] = {}
            st.success("자산이 초기화되었습니다.")
            st.rerun()

    st.markdown("---")
    
    col_trade, col_hold = st.columns([1, 1])
    with col_trade:
        st.markdown(f"##### 🛒 주문 실행 ({current_ticker})")
        if ticker_df is not None and not ticker_df.empty:
            curr_p_raw = ticker_df['Close'].iloc[-1]
            curr_p_krw = curr_p_raw if current_ticker.endswith(".KS") else curr_p_raw * c_krw
            st.write(f"현재 실시간가: **{curr_symbol}{curr_p_krw * disp_scale:,.0f}**")
            
            st.caption("⚡ 빠른 매수 비율 선택")
            b_c1, b_c2, b_c3 = st.columns(3)
            calc_qty = 1
            if b_c1.button("25% 매수"):
                calc_qty = max(1, int((st.session_state['cash'] * 0.25) // curr_p_krw))
            if b_c2.button("50% 매수"):
                calc_qty = max(1, int((st.session_state['cash'] * 0.50) // curr_p_krw))
            if b_c3.button("MAX (100%)"):
                calc_qty = max(1, int(st.session_state['cash'] // curr_p_krw))

            tb1, tb2 = st.columns(2)
            with tb1:
                buy_qty = st.number_input("매수 수량", min_value=1, value=calc_qty, key="b_q")
                if st.button(f"🟢 {L['buy_btn']}", use_container_width=True):
                    cost = curr_p_krw * buy_qty
                    if st.session_state['cash'] >= cost:
                        st.session_state['cash'] -= cost
                        old_info = st.session_state['portfolio'].get(current_ticker, {'qty': 0, 'avg_price': 0})
                        new_qty = old_info['qty'] + buy_qty
                        new_avg = ((old_info['qty'] * old_info['avg_price']) + cost) / new_qty
                        st.session_state['portfolio'][current_ticker] = {'qty': new_qty, 'avg_price': new_avg}
                        st.success(f"{current_ticker} {buy_qty}주 매수 완료!")
                        st.rerun()
                    else:
                        st.error("보유 현금이 부족합니다.")
            
            with tb2:
                sell_qty = st.number_input("매도 수량", min_value=1, value=1, key="s_q")
                if st.button(f"🔴 {L['sell_btn']}", use_container_width=True):
                    old_info = st.session_state['portfolio'].get(current_ticker, {'qty': 0, 'avg_price': 0})
                    if old_info['qty'] >= sell_qty:
                        st.session_state['cash'] += curr_p_krw * sell_qty
                        old_info['qty'] -= sell_qty
                        st.session_state['portfolio'][current_ticker] = old_info
                        st.success(f"{current_ticker} {sell_qty}주 매도 완료!")
                        st.rerun()
                    else:
                        st.error("보유 수량이 부족합니다.")
        else:
            st.warning("데이터를 불러올 수 없습니다.")

    with col_hold:
        st.markdown("##### 📋 내 보유 종목 현황")
        if portfolio_rows:
            st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True, hide_index=True)
        else:
            st.info("보유 중인 주식이 없습니다.")

# ----------------------------------------------------
# TAB 2: 포트폴리오 계산기
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box">💡 <b>비중 분석</b>: 자산 비중을 조정하며 포트폴리오 구성을 검토하세요.</div>', unsafe_allow_html=True)
    sample_tickers = ["AAPL", "NVDA", "TSLA", "005930.KS"]
    weights = []
    
    col_w, col_pie = st.columns([1, 1])
    with col_w:
        st.markdown("##### ⚙️ 비중 설정 (%)")
        for t in sample_tickers:
            w = st.slider(f"{t} 비중", 0, 100, 25, step=5)
            weights.append(w)
            
    with col_pie:
        if sum(weights) > 0:
            fig_pie = go.Figure(data=[go.Pie(labels=sample_tickers, values=weights, hole=.4)])
            fig_pie.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                height=280,
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

# ----------------------------------------------------
# TAB 3: 기술적 분석
# ----------------------------------------------------
with tab3:
    st.markdown(f'<div class="guide-box">💡 <b>기술적 차트</b>: {current_ticker} 종목의 이동평균선과 거래량을 분석합니다.</div>', unsafe_allow_html=True)
    if ticker_df is not None and not ticker_df.empty:
        df_t = ticker_df.copy()
        df_t['MA20'] = df_t['Close'].rolling(20).mean()
        df_t['MA60'] = df_t['Close'].rolling(60).mean()

        fig_candle = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_candle.add_trace(go.Candlestick(
            x=df_t.index, open=df_t['Open']*fx_rate, high=df_t['High']*fx_rate,
            low=df_t['Low']*fx_rate, close=df_t['Close']*fx_rate, name="주가"
        ), row=1, col=1)
        fig_candle.add_trace(go.Scatter(x=df_t.index, y=df_t['MA20']*fx_rate, name="20일선", line=dict(color='#F59E0B', width=1)), row=1, col=1)
        fig_candle.add_trace(go.Scatter(x=df_t.index, y=df_t['MA60']*fx_rate, name="60일선", line=dict(color='#6366F1', width=1)), row=1, col=1)

        colors = ['#EF4444' if row['Open'] > row['Close'] else '#10B981' for _, row in df_t.iterrows()]
        fig_candle.add_trace(go.Bar(x=df_t.index, y=df_t['Volume'], name="거래량", marker_color=colors), row=2, col=1)

        fig_candle.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_rangeslider_visible=False,
            height=450,
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_candle, use_container_width=True)

# ----------------------------------------------------
# TAB 4: 퀀트 & 리스크 분석
# ----------------------------------------------------
with tab4:
    st.markdown(f'<div class="guide-box">💡 <b>퀀트 리스크 분석</b>: 최근 1년 변동성, 샤프 지수, 최대 낙폭(MDD)을 산출합니다.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty and len(ticker_df) > 20:
        df_risk = ticker_df.copy()
        df_risk['Daily_Return'] = df_risk['Close'].pct_change()
        
        annual_return = df_risk['Daily_Return'].mean() * 252 * 100
        annual_volatility = df_risk['Daily_Return'].std() * np.sqrt(252) * 100
        risk_free_rate = 3.5
        sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility != 0 else 0
        
        df_risk['Cum_Max'] = df_risk['Close'].cummax()
        df_risk['Drawdown'] = (df_risk['Close'] - df_risk['Cum_Max']) / df_risk['Cum_Max'] * 100
        mdd = df_risk['Drawdown'].min()
        
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("📈 연간 예상 수익률", f"{annual_return:+.2f}%")
        r2.metric("⚡ 연간 변동성", f"{annual_volatility:.2f}%")
        r3.metric("🎯 샤프 지수", f"{sharpe_ratio:.2f}")
        r4.metric("📉 최대 낙폭 (MDD)", f"{mdd:.2f}%")
        
        st.markdown("---")
        col_mdd, col_dist = st.columns([1, 1])
        with col_mdd:
            st.markdown("##### 📉 고점 대비 낙폭(Drawdown) 추이")
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=df_risk.index, y=df_risk['Drawdown'],
                fill='tozeroy', fillcolor='rgba(239, 68, 68, 0.3)',
                line=dict(color='#EF4444', width=1.5), name="낙폭 (%)"
            ))
            fig_dd.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=280,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_dd, use_container_width=True)
            
        with col_dist:
            st.markdown("##### 📊 일간 수익률 분포")
            fig_dist = px.histogram(df_risk.dropna(), x="Daily_Return", nbins=40, color_discrete_sequence=['#38BDF8'])
            fig_dist.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=280,
                margin=dict(l=10, r=10, t=20, b=10)
            )
            st.plotly_chart(fig_dist, use_container_width=True)

# ----------------------------------------------------
# 🎲 TAB 5: 몬테카를로 시뮬레이션 (플랜별 1k / 3k / 10k 차등)
# ----------------------------------------------------
with tab5:
    st.markdown(f'<div class="guide-box">💡 <b>몬테카를로 확률 예측</b>: 기하 브라운 운동(GBM) 기반의 <b>미래 주가 시뮬레이션</b>을 실행합니다.</div>', unsafe_allow_html=True)
    
    if ticker_df is not None and not ticker_df.empty and len(ticker_df) > 30:
        df_mc = ticker_df.copy()
        last_price = df_mc['Close'].iloc[-1]
        
        log_returns = np.log(df_mc['Close'] / df_mc['Close'].shift(1)).dropna()
        u = log_returns.mean()
        var = log_returns.var()
        drift = u - (0.5 * var)
        stdev = log_returns.std()
        
        col_ctrl1, col_ctrl2 = st.columns([1, 2])
        with col_ctrl1:
            pred_days = st.slider("📆 미래 예측 기간 (일수)", min_value=30, max_value=252, value=90, step=30)
            
            # 플랜별 시뮬레이션 횟수 결정
            if current_plan == "Free":
                num_simulations = 1000
                st.info("💡 **Free 플랜**: 1,000회 시뮬레이션을 수행합니다.")
            elif current_plan == "Lite":
                num_simulations = 3000
                st.success("⚡ **Lite 플랜**: 3,000회 시뮬레이션을 수행합니다.")
            else: # Pro
                num_simulations = st.slider("🎲 몬테카를로 횟수 (Pro)", min_value=3000, max_value=10000, value=10000, step=1000)
                st.markdown('<span class="badge-pro">👑 Pro 플랜: 최대 10,000회 정밀 시뮬레이션 가능</span>', unsafe_allow_html=True)

        # 연산 실행
        np.random.seed(42)
        daily_returns = np.exp(drift + stdev * np.random.normal(0, 1, (pred_days, num_simulations)))
        
        price_list = np.zeros_like(daily_returns)
        price_list[0] = last_price
        for t in range(1, pred_days):
            price_list[t] = price_list[t - 1] * daily_returns[t]
            
        final_prices = price_list[-1]
        p_10 = np.percentile(final_prices, 10)
        p_25 = np.percentile(final_prices, 25)
        p_50 = np.median(final_prices)
        p_75 = np.percentile(final_prices, 75)
        p_90 = np.percentile(final_prices, 90)

        p_scale = fx_rate if not current_ticker.endswith(".KS") else 1.0
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("🔥 상위 10% (Best)", f"{curr_symbol}{p_90 * p_scale:,.0f}", f"{((p_90 - last_price)/last_price)*100:+.1f}%")
        m2.metric("📈 상위 25%", f"{curr_symbol}{p_75 * p_scale:,.0f}", f"{((p_75 - last_price)/last_price)*100:+.1f}%")
        m3.metric("🎯 중앙값 (Expected)", f"{curr_symbol}{p_50 * p_scale:,.0f}", f"{((p_50 - last_price)/last_price)*100:+.1f}%")
        m4.metric("📉 하위 25%", f"{curr_symbol}{p_25 * p_scale:,.0f}", f"{((p_25 - last_price)/last_price)*100:+.1f}%")
        m5.metric("❄️ 하위 10% (Worst)", f"{curr_symbol}{p_10 * p_scale:,.0f}", f"{((p_10 - last_price)/last_price)*100:+.1f}%")

        st.markdown("---")
        
        col_c1, col_c2 = st.columns([2, 1])
        with col_c1:
            st.markdown(f"##### 🎲 {num_simulations:,}개 경로 시뮬레이션 시각화 ({pred_days}일 후)")
            fig_mc = go.Figure()
            
            sample_paths = price_list[:, :min(100, num_simulations)]
            for i in range(sample_paths.shape[1]):
                fig_mc.add_trace(go.Scatter(
                    y=sample_paths[:, i] * p_scale, 
                    mode='lines', 
                    line=dict(width=0.6, color='rgba(56, 189, 248, 0.15)'), 
                    showlegend=False
                ))
                
            fig_mc.add_trace(go.Scatter(y=np.percentile(price_list, 90, axis=1) * p_scale, name="상위 10%", line=dict(color='#10B981', width=2)))
            fig_mc.add_trace(go.Scatter(y=np.median(price_list, axis=1) * p_scale, name="중앙값 (50%)", line=dict(color='#F59E0B', width=2.5)))
            fig_mc.add_trace(go.Scatter(y=np.percentile(price_list, 10, axis=1) * p_scale, name="하위 10%", line=dict(color='#EF4444', width=2)))

            fig_mc.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=380,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(title="경과 일수 (Day)"),
                yaxis=dict(title=f"예상 주가 ({curr_symbol})")
            )
            st.plotly_chart(fig_mc, use_container_width=True)

        with col_c2:
            st.markdown("##### 📊 최종 도달 주가 분포")
            fig_hist = px.histogram(
                x=final_prices * p_scale, nbins=50, 
                color_discrete_sequence=['#A855F7'],
                labels={'x': f'최종 주가 ({curr_symbol})'}
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

st.sidebar.markdown("---")
st.sidebar.caption("ⓒ StockLab All Rights Reserved.")
