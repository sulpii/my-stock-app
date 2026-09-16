import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# ----------------------------------------------------
# 1. Page Config & CSS UI Style
# ----------------------------------------------------
st.set_page_config(
    page_title="StockLab - Quant Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0B0E14; }
    
    /* 메트릭 박스 글자 잘림 방지 핵심 스타일 */
    [data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        white-space: normal !important;
        word-break: break-all !important;
        line-height: 1.2 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.8rem !important;
        color: #94A3B8 !important;
    }
    .stMetric {
        background-color: #1E293B;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
    }
    
    /* 타이틀 및 가이드 박스 */
    .sidebar-title { font-size: 1.6rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .sidebar-subtitle { font-size: 0.8rem; color: #94A3B8; margin-bottom: 15px; }
    .main-title { font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .main-subtitle { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; }
    
    .badge-free { background-color: #334155; color: #94A3B8; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-lite { background-color: #0284C7; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-pro { background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    
    .guide-box {
        background-color: #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.9rem;
        color: #CBD5E1;
    }
    .version-tag { font-size: 0.75rem; color: #64748B; text-align: center; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Session State Initialize (모의투자 잔고)
# ----------------------------------------------------
if 'cash' not in st.session_state:
    st.session_state.cash = 100000000.0  # 초기 가상 현금 100,000,000원 ($100,000)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []
if 'trade_qty_val' not in st.session_state:
    st.session_state.trade_qty_val = 10
if 'user_plan' not in st.session_state:
    st.session_state.user_plan = "Free"

# ----------------------------------------------------
# 3. Data Fetching & Caching (인기 종목 리스트)
# ----------------------------------------------------
POPULAR_STOCKS = {
    "애플 (AAPL)": "AAPL",
    "엔비디아 (NVDA)": "NVDA",
    "테슬라 (TSLA)": "TSLA",
    "마이크로소프트 (MSFT)": "MSFT",
    "아마존 (AMZN)": "AMZN",
    "구글 (GOOGL)": "GOOGL",
    "S&P500 ETF (SPY)": "SPY",
    "TQQQ (나스닥 3배)": "TQQQ",
    "SOXL (반도체 3배)": "SOXL",
    "비트코인 (BTC-USD)": "BTC-USD",
    "삼성전자 (005930.KS)": "005930.KS"
}

APP_VERSION = "v1.5.0 Pro"

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, start_date, end_date):
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

@st.cache_data(ttl=3600)
def fetch_multi_ticker_data(tickers, start_date, end_date):
    try:
        df = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
        if df.empty:
            return None
        return df
    except Exception:
        return None

# ----------------------------------------------------
# 4. Sidebar Setup
# ----------------------------------------------------
with st.sidebar:
    st.markdown('<h2 class="sidebar-title">StockLab</h2>', unsafe_allow_html=True)
    st.markdown('<p class="sidebar-subtitle">주식 모의투자 & AI 시뮬레이터</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("##### 나의 멤버십 현황")
    current_plan = st.session_state.user_plan
    
    plan_col1, plan_col2 = st.columns([2, 1])
    with plan_col1:
        if current_plan == "Free": st.markdown('<span class="badge-free">Free 모드</span>', unsafe_allow_html=True)
        elif current_plan == "Lite": st.markdown('<span class="badge-lite">Lite 모드</span>', unsafe_allow_html=True)
        else: st.markdown('<span class="badge-pro">Pro 모드</span>', unsafe_allow_html=True)

    with plan_col2:
        new_plan = st.selectbox("플랜변경", ["Free", "Lite", "Pro"], index=["Free", "Lite", "Pro"].index(current_plan), label_visibility="collapsed")
        if new_plan != current_plan:
            st.session_state.user_plan = new_plan
            st.rerun()

    st.markdown("---")
    st.markdown("##### 분석 자산 설정")
    
    selected_name = st.selectbox("인기 추천 종목 퀵 선택", list(POPULAR_STOCKS.keys()))
    custom_ticker = st.text_input("직접 Ticker 입력 (선택)", value="").strip().upper()
    
    ticker = custom_ticker if custom_ticker else POPULAR_STOCKS[selected_name]
    
    today = datetime.today()
    start_default = today - timedelta(days=365)
    
    start_date = st.date_input("시작일", start_default)
    end_date = st.date_input("종료일", today)
    
    st.markdown("---")
    
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("새로고침", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    with col_sb2:
        if st.button("잔고 리셋", use_container_width=True):
            st.session_state.cash = 100000000.0
            st.session_state.portfolio = {}
            st.session_state.trade_history = []
            st.toast("예수금 및 포트폴리오가 리셋되었습니다.")
            st.rerun()

    st.markdown(f'<div class="version-tag">StockLab Version: <b>{APP_VERSION}</b></div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Main Body & Data Fetching
# ----------------------------------------------------
st.markdown('<h1 class="main-title">StockLab</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="main-subtitle">선택 종목: <b>{ticker}</b> | 퀀트 분석 & 모의투자 대시보드</p>', unsafe_allow_html=True)

df = fetch_stock_data(ticker, start_date, end_date)

if df is None or len(df) < 20:
    st.warning("데이터가 부족하거나 불러올 수 없습니다. 날짜 범위나 Ticker를 확인해주세요.")
    st.stop()

# 보조 지표 계산
df['SMA20'] = df['Close'].rolling(window=20).mean()
df['SMA60'] = df['Close'].rolling(window=60).mean()
df['STD20'] = df['Close'].rolling(window=20).std()
df['UpperBB'] = df['SMA20'] + (df['STD20'] * 2)
df['LowerBB'] = df['SMA20'] - (df['STD20'] * 2)

# RSI
delta = df['Close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# ----------------------------------------------------
# 6. Key Metrics Top Display
# ----------------------------------------------------
curr_price = float(df['Close'].iloc[-1])
prev_price = float(df['Close'].iloc[-2])
price_chg = curr_price - prev_price
price_chg_pct = (price_chg / prev_price) * 100

high_52 = df['High'].max()
low_52 = df['Low'].min()

unit = "₩" if ticker.endswith(".KS") else "$"

m1, m2, m3, m4 = st.columns(4)
m1.metric("현재가", f"{unit}{curr_price:,.2f}", f"{price_chg_pct:+.2f}%")
m2.metric("보유 예수금 (잔고)", f"₩{st.session_state.cash:,.0f}")
m3.metric("52주 최고가", f"{unit}{high_52:,.2f}")
m4.metric("52주 최저가", f"{unit}{low_52:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------
# 7. Tab Navigation
# ----------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "모의주식 거래 & 자산", 
    "포트폴리오 분석기",
    "기술적 분석 차트", 
    "AI 매매 신호", 
    "퀀트 리스크 분석", 
    "몬테카를로 AI 예측 (Pro)"
])

# ----------------------------------------------------
# TAB 1: 모의주식 거래 & 자산
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box"><b>가상 모의투자</b>: 가상 예수금으로 실시간 주가를 매수/매도하며 잔고와 수익률을 관리합니다.</div>', unsafe_allow_html=True)
    
    held_qty = st.session_state.portfolio.get(ticker, {}).get('qty', 0)
    avg_buy_p = st.session_state.portfolio.get(ticker, {}).get('avg_price', 0.0)
    
    eval_val = held_qty * curr_price
    buy_val = held_qty * avg_buy_p
    pnl = eval_val - buy_val
    pnl_pct = (pnl / buy_val * 100) if buy_val > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("보유 현금 예수금", f"₩{st.session_state.cash:,.0f}")
    c2.metric(f"보유 수량 ({ticker})", f"{held_qty:,} 주")
    c3.metric("평균 매수 단가", f"{unit}{avg_buy_p:,.2f}")
    c4.metric("평가 손익", f"{unit}{pnl:,.2f}", f"{pnl_pct:+.2f}%")

    st.markdown("---")
    
    col_trade, col_port = st.columns([1, 1])
    
    with col_trade:
        st.write(f"##### 매수/매도 주문 | {ticker} 현재가: {unit}{curr_price:,.2f}")
        
        st.caption("빠른 수량 선택")
        btn_q1, btn_q2, btn_q3, btn_q4 = st.columns(4)
        if btn_q1.button("+10주"): st.session_state.trade_qty_val += 10
        if btn_q2.button("+50주"): st.session_state.trade_qty_val += 50
        if btn_q3.button("+100주"): st.session_state.trade_qty_val += 100
        if btn_q4.button("전액 매수"):
            st.session_state.trade_qty_val = int(st.session_state.cash // curr_price) if curr_price > 0 else 1
            
        trade_qty = st.number_input("주문 수량(주)", min_value=1, value=max(1, st.session_state.trade_qty_val), step=1)
        total_cost = trade_qty * curr_price
        st.caption(f"총 주문 금액: {unit}{total_cost:,.2f}")
        
        btn_buy, btn_sell = st.columns(2)
        
        with btn_buy:
            if st.button("매수하기", type="primary", use_container_width=True):
                if st.session_state.cash < total_cost:
                    st.error("잔고가 부족합니다.")
                else:
                    st.session_state.cash -= total_cost
                    new_qty = held_qty + trade_qty
                    new_avg = ((held_qty * avg_buy_p) + total_cost) / new_qty
                    st.session_state.portfolio[ticker] = {'qty': new_qty, 'avg_price': new_avg}
                    
                    st.session_state.trade_history.append({
                        '시간': datetime.now().strftime('%H:%M:%S'),
                        '종목': ticker,
                        '구분': '매수',
                        '수량': trade_qty,
                        '체결가': f"{unit}{curr_price:,.2f}"
                    })
                    st.success(f"{ticker} {trade_qty}주 매수 완료!")
                    st.rerun()

        with btn_sell:
            if st.button("매도하기", use_container_width=True):
                if held_qty < trade_qty:
                    st.error("보유 수량이 부족합니다.")
                else:
                    st.session_state.cash += total_cost
                    new_qty = held_qty - trade_qty
                    if new_qty == 0:
                        del st.session_state.portfolio[ticker]
                    else:
                        st.session_state.portfolio[ticker]['qty'] = new_qty
                        
                    st.session_state.trade_history.append({
                        '시간': datetime.now().strftime('%H:%M:%S'),
                        '종목': ticker,
                        '구분': '매도',
                        '수량': trade_qty,
                        '체결가': f"{unit}{curr_price:,.2f}"
                    })
                    st.success(f"{ticker} {trade_qty}주 매도 완료!")
                    st.rerun()

    with col_port:
        st.write("##### 내 보유 포트폴리오")
        if not st.session_state.portfolio:
            st.info("현재 보유 중인 주식이 없습니다.")
        else:
            port_data = []
            for t_code, info in st.session_state.portfolio.items():
                p_unit = "₩" if t_code.endswith(".KS") else "$"
                port_data.append({
                    "종목": t_code,
                    "보유수량": f"{info['qty']}주",
                    "평균단가": f"{p_unit}{info['avg_price']:,.2f}",
                    "평가금액": f"{p_unit}{info['qty'] * curr_price:,.2f}"
                })
            st.table(pd.DataFrame(port_data))
            
    if st.session_state.trade_history:
        st.markdown("---")
        st.write("##### 최근 거래 내역")
        st.dataframe(pd.DataFrame(st.session_state.trade_history).iloc[::-1], use_container_width=True)

# ----------------------------------------------------
# TAB 2: 포트폴리오 분석기 (px.line 오류 수정 처리)
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box"><b>포트폴리오 분석</b>: 선택한 종목들의 과거 백테스팅, 상관관계 히트맵 및 리밸런싱 계산을 지원합니다.</div>', unsafe_allow_html=True)
    
    selected_port_tickers = st.multiselect(
        "분석할 포트폴리오 종목 선택", 
        list(POPULAR_STOCKS.values()),
        default=["AAPL", "NVDA", "SPY"]
    )
    
    if len(selected_port_tickers) >= 2:
        weights = {}
        st.write("##### 종목별 투자 비중 설정 (%)")
        cols = st.columns(len(selected_port_tickers))
        
        default_w = round(100.0 / len(selected_port_tickers), 2)
        for idx, t in enumerate(selected_port_tickers):
            with cols[idx]:
                weights[t] = st.number_input(f"{t} 비중", min_value=0.0, max_value=100.0, value=default_w, step=1.0, format="%.2f")
                
        tot_weight = round(sum(weights.values()), 2)
        if abs(tot_weight - 100.0) > 0.5:
            st.warning(f"비중 합계가 {tot_weight}%입니다. (100%에 맞춰주세요)")
        else:
            st.success(f"비중 합계: {tot_weight}% (정상)")
            
            df_port = fetch_multi_ticker_data(selected_port_tickers, str(start_date), str(end_date))
            if df_port is not None and not df_port.empty:
                daily_returns = df_port.pct_change().dropna()
                w_list = np.array([weights[t] for t in selected_port_tickers])
                w_list = w_list / np.sum(w_list)  # 자동 정규화
                
                port_returns = (daily_returns * w_list).sum(axis=1)
                cum_returns = (1 + port_returns).cumprod()
                
                sub_t1, sub_t2, sub_t3 = st.tabs(["과거 성과 백테스트", "상관계수 히트맵", "리밸런싱 계산기"])
                
                with sub_t1:
                    total_ret = (cum_returns.iloc[-1] - 1) * 100
                    cagr = ((cum_returns.iloc[-1]) ** (365 / len(cum_returns)) - 1) * 100
                    peak = cum_returns.cummax()
                    mdd = ((cum_returns - peak) / peak).min() * 100
                    
                    b1, b2, b3 = st.columns(3)
                    b1.metric("총 수익률", f"{total_ret:+.2f}%")
                    b2.metric("연평균 수익률 (CAGR)", f"{cagr:.2f}%")
                    b3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
                    
                    # Plotly Graph Objects로 안전하게 차트 생성
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(x=cum_returns.index, y=cum_returns.values, mode='lines', name='포트폴리오', line=dict(color='#38BDF8', width=2)))
                    fig_bt.update_layout(template="plotly_dark", height=350, title="포트폴리오 누적 성과 추이", yaxis_title="자산 가치 (1.0 기준)")
                    st.plotly_chart(fig_bt, use_container_width=True)

                with sub_t2:
                    corr_matrix = daily_returns.corr()
                    fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="Blues")
                    fig_corr.update_layout(template="plotly_dark", height=350)
                    st.plotly_chart(fig_corr, use_container_width=True)

                with sub_t3:
                    total_inv = st.number_input("현재 포트폴리오 총 평가금액 (원)", value=10000000, step=1000000)
                    rebal_data = []
                    for idx, t in enumerate(selected_port_tickers):
                        target_amt = total_inv * w_list[idx]
                        last_p = df_port[t].iloc[-1]
                        target_shares = target_amt / last_p
                        rebal_data.append({
                            "종목": t,
                            "목표 비중": f"{weights[t]:.2f}%",
                            "목표 금액": f"₩{target_amt:,.0f}",
                            "현재가": f"{last_p:,.2f}",
                            "필요 목표 주수": f"{target_shares:.2f} 주"
                        })
                    st.table(pd.DataFrame(rebal_data))

# ----------------------------------------------------
# TAB 3: 기술적 분석 차트
# ----------------------------------------------------
with tab3:
    st.markdown('<div class="guide-box"><b>기술적 차트</b>: 이동평균선(20/60일), 볼린저밴드, RSI 및 <b>AI 매매 신호 마커</b>를 조회합니다.</div>', unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], mode='lines', name='SMA 20', line=dict(color='#38BDF8', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA60'], mode='lines', name='SMA 60', line=dict(color='#F59E0B', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['UpperBB'], mode='lines', name='Upper BB', line=dict(color='rgba(255,255,255,0.3)', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['LowerBB'], mode='lines', name='Lower BB', line=dict(color='rgba(255,255,255,0.3)', dash='dash')), row=1, col=1)
    
    # AI 매수/매도 마커 (골든/데드크로스)
    buy_signals = df[(df['SMA20'] > df['SMA60']) & (df['SMA20'].shift(1) <= df['SMA60'].shift(1))]
    sell_signals = df[(df['SMA20'] < df['SMA60']) & (df['SMA20'].shift(1) >= df['SMA60'].shift(1))]
    
    fig.add_trace(go.Scatter(
        x=buy_signals.index, y=buy_signals['Low'] * 0.97, mode='markers',
        marker=dict(symbol='triangle-up', size=11, color='#10B981'), name='AI 매수 신호'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=sell_signals.index, y=sell_signals['High'] * 1.03, mode='markers',
        marker=dict(symbol='triangle-down', size=11, color='#EF4444'), name='AI 매도 신호'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI 14', line=dict(color='#EC4899', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# TAB 4: AI 매매 신호
# ----------------------------------------------------
with tab4:
    st.markdown('<div class="guide-box"><b>AI 매매 신호</b>: 이동평균선 및 RSI 기반 종합 매매 진단을 제공합니다.</div>', unsafe_allow_html=True)
    
    curr_rsi = df['RSI'].iloc[-1]
    curr_sma20 = df['SMA20'].iloc[-1]
    curr_sma60 = df['SMA60'].iloc[-1]
    
    signal_score = 0
    reasons = []
    
    if curr_sma20 > curr_sma60:
        signal_score += 1
        reasons.append("20일 이동평균선이 60일 이동평균선 위에 위치 (상승 추세)")
    else:
        signal_score -= 1
        reasons.append("20일 이동평균선이 60일 이동평균선 아래에 위치 (하락 추세)")
        
    if curr_rsi < 30:
        signal_score += 2
        reasons.append("RSI 30 이하로 과매도 구간 (반등 가능성 높음)")
    elif curr_rsi > 70:
        signal_score -= 2
        reasons.append("RSI 70 이상으로 과매수 구간 (단기 조정 가능성 높음)")
    else:
        reasons.append("RSI 중립 구간 (30 ~ 70)")
        
    col1, col2 = st.columns([1, 2])
    with col1:
        if signal_score >= 2: st.success("### AI 진단: **강력 매수 (Strong Buy)**")
        elif signal_score == 1: st.info("### AI 진단: **매수 (Buy)**")
        elif signal_score == 0: st.warning("### AI 진단: **관망 (Hold)**")
        else: st.error("### AI 진단: **매도/위험 (Sell)**")
            
    with col2:
        st.write("##### 판단 근거")
        for r in reasons: st.write(f"• {r}")

# ----------------------------------------------------
# TAB 5: 퀀트 리스크 분석
# ----------------------------------------------------
with tab5:
    st.markdown('<div class="guide-box"><b>위험도 분석</b>: 낙폭(MDD), Sharpe Ratio 및 일일 변동성 평가를 제공합니다.</div>', unsafe_allow_html=True)
    
    daily_ret = df['Close'].pct_change().dropna()
    annual_vol = daily_ret.std() * np.sqrt(252) * 100
    annual_return = daily_ret.mean() * 252 * 100
    sharpe_ratio = (annual_return - 3.5) / annual_vol if annual_vol != 0 else 0
    
    cum_ret = (1 + daily_ret).cumprod()
    peak = cum_ret.cummax()
    mdd = ((cum_ret - peak) / peak).min() * 100

    col_v1, col_v2, col_v3 = st.columns(3)
    col_v1.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
    col_v2.metric("연환산 변동성", f"{annual_vol:.2f}%")
    col_v3.metric("샤프 지수 (Sharpe)", f"{sharpe_ratio:.2f}")
    
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=df.index[1:], y=(cum_ret - peak)/peak * 100, fill='tozeroy', mode='lines', line=dict(color='#EF4444')))
    fig_dd.update_layout(template="plotly_dark", height=300, yaxis_title="낙폭 비율 (%)")
    st.plotly_chart(fig_dd, use_container_width=True)

# ----------------------------------------------------
# TAB 6: 몬테카를로 AI 예측 (Pro 전용 잠금)
# ----------------------------------------------------
with tab6:
    st.markdown('<div class="guide-box"><b>몬테카를로 확률 예측</b>: Pro 멤버십 전용 미래 주가 확률 시뮬레이션입니다.</div>', unsafe_allow_html=True)
    
    current_plan = st.session_state.user_plan
    
    if current_plan != "Pro":
        st.warning("🔒 **몬테카를로 AI 예측 기능은 Pro 멤버십 전용 기능입니다.**")
        st.markdown("""
        <div style="background-color: #1E293B; border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <b style="color: #38BDF8;">Pro 멤버십 혜택</b><br>
            • 복수 종목 분할 투자 포트폴리오 시뮬레이션<br>
            • 최대 10,000회 몬테카를로 난수 시뮬레이션 지원<br>
            • 상위/하위 10% 위험 자산 및 예상 수익률 분석
        </div>
        """, unsafe_allow_html=True)
        if st.button("Pro 멤버십으로 업그레이드하기", type="primary"):
            st.toast("결제 페이지로 이동합니다.")
    else:
        st.success("Pro 멤버십 혜택: 몬테카를로 확률 예측 시뮬레이션이 활성화되었습니다.")
        
        selected_mc_tickers = st.multiselect(
            "시뮬레이션할 포트폴리오 종목 구성", 
            list(POPULAR_STOCKS.values()),
            default=["AAPL", "NVDA"]
        )
        
        if len(selected_mc_tickers) > 1:
            mc_weights = {}
            cols = st.columns(len(selected_mc_tickers))
            def_w = round(100.0 / len(selected_mc_tickers), 2)
            for idx, t in enumerate(selected_mc_tickers):
                with cols[idx]:
                    mc_weights[t] = st.number_input(f"{t} 비중(%)", min_value=0.0, max_value=100.0, value=def_w, step=1.0, format="%.2f", key=f"mc_w_{t}")
        else:
            mc_weights = {selected_mc_tickers[0]: 100.0} if selected_mc_tickers else {}

        st.markdown("---")
        
        if selected_mc_tickers:
            col_m1, col_m2, col_m3 = st.columns([1.5, 1.5, 1])
            with col_m1: init_budget = st.number_input("투자 예산 (원금)", min_value=100000, value=10000000, step=1000000)
            with col_m2: pred_days = st.slider("예측 기간 (일수)", min_value=30, max_value=252, value=90, step=30)
            with col_m3:
                num_sims = 10000
                st.caption(f"시뮬레이션 횟수: **{num_sims:,}회 (Pro)**")
                
            df_mc = fetch_multi_ticker_data(selected_mc_tickers, str(start_date), str(end_date))
            
            if df_mc is not None and not df_mc.empty:
                daily_returns = df_mc.pct_change().dropna()
                
                if len(selected_mc_tickers) == 1:
                    port_daily_ret = daily_returns.iloc[:, 0]
                else:
                    w_arr = np.array([mc_weights[t] for t in selected_mc_tickers])
                    w_arr = w_arr / np.sum(w_arr)
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

                st.write(f"##### {init_budget:,.0f}원 투자 시 {pred_days}일 후 예상 자산 평가")
                r1, r2, r3, r4 = st.columns(4)
                r1.metric("예상 자산 (중앙값)", f"₩{a_50:,.0f}", f"{((a_50 - init_budget)/init_budget)*100:+.1f}%")
                r2.metric("상위 10% (Best)", f"₩{a_90:,.0f}", f"{((a_90 - init_budget)/init_budget)*100:+.1f}%")
                r3.metric("하위 10% (Worst)", f"₩{a_10:,.0f}", f"{((a_10 - init_budget)/init_budget)*100:+.1f}%")
                r4.metric("원금 보존/수익 확률", f"{profit_prob:.1f}%")

                fig_mc = go.Figure()
                sample_paths = asset_paths[:, :100]
                for i in range(sample_paths.shape[1]):
                    fig_mc.add_trace(go.Scatter(y=sample_paths[:, i], mode='lines', line=dict(width=0.5, color='rgba(56, 189, 248, 0.1)'), showlegend=False))
                fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 90, axis=1), name="상위 10%", line=dict(color='#10B981', width=2)))
                fig_mc.add_trace(go.Scatter(y=np.median(asset_paths, axis=1), name="중앙값 (50%)", line=dict(color='#F59E0B', width=2.5)))
                fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 10, axis=1), name="하위 10%", line=dict(color='#EF4444', width=2)))
                fig_mc.update_layout(template="plotly_dark", height=380, xaxis=dict(title="경과 일수 (Day)"), yaxis=dict(title="예상 평가액 (₩)"))
                
                st.plotly_chart(fig_mc, use_container_width=True)
