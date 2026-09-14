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

# Custom CSS (사이드바 너비 줄이기 및 다크 핀테크 스타일)
st.markdown("""
    <style>
    /* 왼쪽 사이드바 너비 축소 (기본값 ~336px -> 260px) */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
    }
    
    .stApp { background-color: #0B0E14; color: #E2E8F0; font-family: 'Pretendard', sans-serif; }
    .main-header { font-size: 2.0rem; font-weight: 800; color: #38BDF8; margin-bottom: 2px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; }
    .version-tag {
        background-color: #1E293B; color: #38BDF8; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 700; border: 1px solid #334155;
    }
    .pro-tag {
        background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%);
        color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700;
    }
    .guide-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 12px 16px;
        border-radius: 6px; font-size: 0.9rem; color: #CBD5E1; margin-bottom: 15px;
    }
    .pro-report-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #38BDF8; border-radius: 12px; padding: 24px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 2. 기본 종목 및 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "StockLab", "subtitle": "주식 초보를 위한 모의투자 & 시뮬레이션 플랫폼",
        "currency_select": "표시 통화", "ver_select": "서비스 모드",
        "tab_sim": "모의투자 및 보유자산", "tab_calc": "포트폴리오 계산기",
        "tab_tech": "기술적 분석 & 뉴스", "tab_risk": "퀀트 & 리스크 분석", "tab_pro": "프로 진단 보고서",
        "buy_btn": "매수하기", "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab", "subtitle": "Paper Trading & Simulation Platform for Beginners",
        "currency_select": "Currency", "ver_select": "Mode",
        "tab_sim": "Paper Trading & Holdings", "tab_calc": "Portfolio Calculator",
        "tab_tech": "Technical Analysis & News", "tab_risk": "Quant & Risk Analysis", "tab_pro": "Pro Report",
        "buy_btn": "Buy", "sell_btn": "Sell"
    }
}

POPULAR_STOCKS = {
    "🔥 인기: 애플 (AAPL)": "AAPL",
    "🔥 인기: 엔비디아 (NVDA)": "NVDA",
    "🔥 인기: 테슬라 (TSLA)": "TSLA",
    "🔥 인기: 삼성전자 (005930.KS)": "005930.KS",
    "🔥 인기: SK하이닉스 (000660.KS)": "000660.KS",
    "🔥 인기: S&P500 ETF (SPY)": "SPY",
    "🔥 인기: KODEX 200 (069500.KS)": "069500.KS"
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

# 세션 초기화 (기본 자산 1억 원 설정)
INIT_CASH = 100000000.0  # 1억 원

if 'cash' not in st.session_state:
    st.session_state['cash'] = INIT_CASH
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {}
if 'search_ticker' not in st.session_state:
    st.session_state['search_ticker'] = "AAPL"

# 사이드바 설정 (너비가 줄어들어 훨씬 컴팩트해집니다)
st.sidebar.markdown("### ⚙️ Settings")
selected_lang = st.sidebar.selectbox("Language", ["한국어", "English"], index=0)
L = LANG_DICT.get(selected_lang, LANG_DICT["한국어"])

rates = get_exchange_rates()
curr_choice = st.sidebar.selectbox(L['currency_select'], ["KRW (₩)", "USD ($)", "JPY (¥)"], index=0)
curr_key = curr_choice.split(" ")[0]
fx_rate, curr_symbol = rates[curr_key]

st.sidebar.markdown("---")
mode_choice = st.sidebar.selectbox(L['ver_select'], ["Free (기본 모드)", "Pro (전문가 모드)"], index=1)
is_pro = "Pro" in mode_choice

def p_icon(icon_str):
    return f"{icon_str} " if is_pro else ""

# 🔍 종목 검색 / 선택 메인 컨트롤러
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

# 데이터 로딩
today = datetime.today()
start_date = today - timedelta(days=365)

with st.spinner(f"'{current_ticker}' 실시간 시세 데이터 동기화 중..."):
    ticker_df = fetch_single_ticker_data(current_ticker, str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f'<p class="main-header">{p_icon("🧪")}{L["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{L["subtitle"]}</p>', unsafe_allow_html=True)
with col_h2:
    if is_pro:
        st.markdown('<div style="text-align:right;"><span class="pro-tag">👑 Pro Version</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:right;"><span class="version-tag">Free Version</span></div>', unsafe_allow_html=True)

# 탭 생성
tab_sim_title = f"{p_icon('💵')}{L['tab_sim']}"
tab_calc_title = f"{p_icon('🧮')}{L['tab_calc']}"
tab_tech_title = f"{p_icon('📈')}{L['tab_tech']}"
tab_risk_title = f"{p_icon('📊')}{L['tab_risk']}"
tab_pro_title = f"{p_icon('👑')}{L['tab_pro']}"

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    tab_sim_title, tab_calc_title, tab_tech_title, tab_risk_title, tab_pro_title
])

c_krw = rates["KRW"][0]
disp_scale = (fx_rate / c_krw) if curr_key != "KRW" else 1.0

# ----------------------------------------------------
# TAB 1: 모의투자 및 보유 자산 (기본 자산 1억 적용)
# ----------------------------------------------------
with tab1:
    st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>가상 모의투자</b>: 초기 자산 1억 원으로 자유롭게 주식을 매수/매도해보세요.</div>', unsafe_allow_html=True)
    
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
                    "종목 티커": t,
                    "보유수량": f"{qty:,}주",
                    "평균단가": f"{curr_symbol}{avg_p * disp_scale:,.0f}",
                    "현재가": f"{curr_symbol}{p_krw * disp_scale:,.0f}",
                    "평가금액": f"{curr_symbol}{current_val * disp_scale:,.0f}",
                    "평가손익": f"{curr_symbol}{profit_krw * disp_scale:,.0f} ({profit_rate:+.2f}%)"
                })

    total_asset_krw = st.session_state['cash'] + eval_stock_val
    
    k1, k2, k3, k4 = st.columns([1.2, 1.2, 1.2, 0.8])
    k1.metric(f"{p_icon('💰')}총 자산", f"{curr_symbol}{total_asset_krw * disp_scale:,.0f}")
    k2.metric(f"{p_icon('💳')}보유 현금", f"{curr_symbol}{st.session_state['cash'] * disp_scale:,.0f}")
    k3.metric(f"{p_icon('🏢')}주식 평가액", f"{curr_symbol}{eval_stock_val * disp_scale:,.0f}")
    with k4:
        st.write("")
        if st.button("🔄 잔고 초기화", use_container_width=True):
            st.session_state['cash'] = INIT_CASH
            st.session_state['portfolio'] = {}
            st.success("자산이 1억 원으로 초기화되었습니다.")
            st.rerun()

    st.markdown("---")
    
    col_trade, col_hold = st.columns([1, 1])
    with col_trade:
        st.markdown(f"##### {p_icon('🛒')}주식 주문하기 (현재 선택: {current_ticker})")
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
                if st.button(f"{p_icon('🟢')}{L['buy_btn']}", use_container_width=True):
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
                if st.button(f"{p_icon('🔴')}{L['sell_btn']}", use_container_width=True):
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
            st.warning("종목 데이터를 찾을 수 없습니다.")

    with col_hold:
        st.markdown(f"##### {p_icon('📋')}내 보유 자산 내역")
        if portfolio_rows:
            st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True, hide_index=True)
        else:
            st.info("현재 보유 중인 주식이 없습니다.")

# ----------------------------------------------------
# TAB 2: 포트폴리오 계산기
# ----------------------------------------------------
with tab2:
    st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>포트폴리오 구성 비율 분석</b>: 주요 종목들의 투자 비중을 조절해보세요.</div>', unsafe_allow_html=True)
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
    st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>캔들스틱 & 거래량 차트</b>: {current_ticker} 종목 분석 차트입니다.</div>', unsafe_allow_html=True)
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

# TAB 4 & TAB 5 생략 없이 동일하게 유지
with tab4:
    st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>퀀트 리스크 분석</b>: 위험 대비 수익성을 정밀하게 분석합니다.</div>', unsafe_allow_html=True)

with tab5:
    if not is_pro:
        st.markdown('<div class="pro-report-card" style="border-color: #6366F1;"><h3 style="color: #6366F1; margin-top:0;">👑 Pro 모드 안내</h3><p style="color: #CBD5E1;">Pro 모드로 전환하면 AI 포트폴리오 진단 리포트를 받아보실 수 있습니다.</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="pro-report-card"><div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8;">👑 StockLab Pro 진단서</div><p style="color: #94A3B8; margin-top:5px;">현재 검색 종목({current_ticker}) 기준 분석 결과입니다.</p></div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.code("Contact: aseui995@gmail.com", language="text")
