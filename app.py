import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ----------------------------------------------------
# 1. Page Config & CSS UI Style
# ----------------------------------------------------
st.set_page_config(
    page_title="ProTradr AI - Quant Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .stMetric {
        background-color: #1E293B;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #334155;
    }
    .stMetric label { color: #94A3B8 !important; font-size: 0.9rem !important; }
    .stMetric div[data-testid="stMetricValue"] { color: #F8FAFC !important; font-weight: 700; }
    .plan-card {
        background-color: #1E293B;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 10px;
    }
    .plan-title { font-size: 1.1rem; font-weight: bold; color: #38BDF8; }
    .guide-box {
        background-color: #1E293B;
        border-left: 4px solid #38BDF8;
        padding: 12px 16px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.95rem;
        color: #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Session State Initialize (모의투자 잔고)
# ----------------------------------------------------
if 'cash' not in st.session_state:
    st.session_state.cash = 100000.0  # 초기 가상 현금 $100,000
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = {}  # {'AAPL': {'qty': 10, 'avg_price': 150.0}}
if 'trade_history' not in st.session_state:
    st.session_state.trade_history = []

# ----------------------------------------------------
# 3. Data Fetching & Caching
# ----------------------------------------------------
POPULAR_STOCKS = {
    "애플 (AAPL)": "AAPL",
    "엔비디아 (NVDA)": "NVDA",
    "테슬라 (TSLA)": "TSLA",
    "마이크로소프트 (MSFT)": "MSFT",
    "아마존 (AMZN)": "AMZN",
    "구글 (GOOGL)": "GOOGL",
    "메타 (META)": "META",
    "S&P500 ETF (SPY)": "SPY",
    "나스닥100 ETF (QQQ)": "QQQ",
    "삼성전자 (005930.KS)": "005930.KS"
}

@st.cache_data(ttl=3600)
def fetch_stock_data(ticker, start_date, end_date):
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception as e:
        st.error(f"데이터 로드 실패 ({ticker}): {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_multi_ticker_data(tickers, start_date, end_date):
    try:
        df = yf.download(tickers, start=start_date, end=end_date, progress=False)['Close']
        if df.empty:
            return None
        return df
    except Exception as e:
        st.error(f"다중 데이터 로드 실패: {e}")
        return None

# ----------------------------------------------------
# 4. Sidebar Setup & Pricing Tier
# ----------------------------------------------------
with st.sidebar:
    st.title("📈 ProTradr AI")
    st.caption("Quant Trading & Monte Carlo AI Dashboard")
    st.markdown("---")
    
    st.subheader("💳 멤버십 요금제 선택")
    current_plan = st.radio(
        "플랜 선택",
        ["Free (일반)", "Lite (라이트)", "Pro (프로)"],
        index=0
    )
    
    if current_plan == "Free (일반)":
        current_plan = "Free"
        st.markdown("""
        <div class="plan-card">
            <div class="plan-title">Free Plan</div>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:5px;">기본 차트 및 모의 주식 거래 가능</p>
        </div>
        """, unsafe_allow_html=True)
    elif current_plan == "Lite (라이트)":
        current_plan = "Lite"
        st.markdown("""
        <div class="plan-card">
            <div class="plan-title" style="color:#F59E0B;">Lite Plan (₩9,900/월)</div>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:5px;">다중 전략 백테스팅 & AI 신호 분석</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        current_plan = "Pro"
        st.markdown("""
        <div class="plan-card">
            <div class="plan-title" style="color:#10B981;">Pro Plan (₩29,900/월)</div>
            <p style="font-size:0.8rem; color:#94A3B8; margin-top:5px;">몬테카를로 AI 확률 예측 & 고급 백테스팅 포함</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🔍 분석 자산 설정")
    
    selected_name = st.selectbox("주요 종목 선택", list(POPULAR_STOCKS.keys()))
    custom_ticker = st.text_input("직접 Ticker 입력 (선택)", value="").strip().upper()
    
    ticker = custom_ticker if custom_ticker else POPULAR_STOCKS[selected_name]
    
    today = datetime.today()
    start_default = today - timedelta(days=365)
    
    start_date = st.date_input("시작일", start_default)
    end_date = st.date_input("종료일", today)
    
    st.markdown("---")
    st.caption("Powered by Streamlit & yfinance")

# ----------------------------------------------------
# 5. Main Body & Data Fetching
# ----------------------------------------------------
st.title(f"📊 {ticker} 퀀트 분석 & 모의주식 Dashboard")

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
avg_vol = df['Volume'].mean()

m1, m2, m3, m4 = st.columns(4)
m1.metric("현재가", f"${curr_price:,.2f}", f"{price_chg_pct:+.2f}%")
m2.metric("52주 최고가", f"${high_52:,.2f}")
m3.metric("52주 최저가", f"${low_52:,.2f}")
m4.metric("평균 거래량", f"{avg_vol:,.0f}")

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------
# 7. Tab Navigation (모의주식 탭 추가)
# ----------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 기술적 분석 차트", 
    "🤖 AI 매매 신호", 
    "💵 모의주식 거래",
    "⚙️ 백테스팅 엔진", 
    "📊 변동성/위험 분석", 
    "🔮 몬테카를로 AI 예측 (Pro)"
])

# ----------------------------------------------------
# TAB 1: 차트 분석
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box"><b>기술적 차트</b>: 캔들차트, 이동평균선(20일/60일), 볼린저밴드 및 RSI 지표를 실시간 조회합니다.</div>', unsafe_allow_html=True)
    
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
    
    # 캔들차트
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='주가'
    ), row=1, col=1)
    
    # 이동평균선 & 볼린저밴드
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA20'], mode='lines', name='SMA 20', line=dict(color='#38BDF8', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA60'], mode='lines', name='SMA 60', line=dict(color='#F59E0B', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['UpperBB'], mode='lines', name='Upper BB', line=dict(color='rgba(255,255,255,0.3)', dash='dash')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['LowerBB'], mode='lines', name='Lower BB', line=dict(color='rgba(255,255,255,0.3)', dash='dash')), row=1, col=1)
    
    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI 14', line=dict(color='#EC4899', width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        height=550,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_rangeslider_visible=False
    )
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# TAB 2: AI 매매 신호
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box"><b>AI 매매 신호</b>: 이동평균선 골든/데드크로스 및 RSI 과매수/과매도 기반 종합 진단을 제공합니다.</div>', unsafe_allow_html=True)
    
    curr_rsi = df['RSI'].iloc[-1]
    curr_sma20 = df['SMA20'].iloc[-1]
    curr_sma60 = df['SMA60'].iloc[-1]
    
    signal_score = 0
    reasons = []
    
    if curr_sma20 > curr_sma60:
        signal_score += 1
        reasons.append("✅ 20일 이동평균선이 60일 이동평균선 위에 위치 (상승 추세)")
    else:
        signal_score -= 1
        reasons.append("⚠️ 20일 이동평균선이 60일 이동평균선 아래에 위치 (하락 추세)")
        
    if curr_rsi < 30:
        signal_score += 2
        reasons.append("✅ RSI 30 이하로 강력한 **과매도 구간** (반등 가능성 높음)")
    elif curr_rsi > 70:
        signal_score -= 2
        reasons.append("⚠️ RSI 70 이상으로 **과매수 구간** (단기 조정 가능성 높음)")
    else:
        reasons.append("ℹ️ RSI 중립 구간 (30 ~ 70)")
        
    col1, col2 = st.columns([1, 2])
    with col1:
        if signal_score >= 2:
            st.success("### AI 진단: **강력 매수 (Strong Buy)**")
        elif signal_score == 1:
            st.info("### AI 진단: **매수 (Buy)**")
        elif signal_score == 0:
            st.warning("### AI 진단: **관망 (Hold)**")
        else:
            st.error("### AI 진단: **매도/위험 (Sell)**")
            
    with col2:
        st.write("#### 📌 판단 근거")
        for r in reasons:
            st.write(r)

# ----------------------------------------------------
# TAB 3: 모의주식 거래 (복원 및 신규 장착)
# ----------------------------------------------------
with tab3:
    st.markdown('<div class="guide-box"><b>🎮 모의주식 투자</b>: 가상 예수금으로 실시간 주가를 매수/매도하며 잔고와 수익률을 관리합니다.</div>', unsafe_allow_html=True)
    
    # 상단 요약 정보
    held_qty = st.session_state.portfolio.get(ticker, {}).get('qty', 0)
    avg_buy_p = st.session_state.portfolio.get(ticker, {}).get('avg_price', 0.0)
    
    eval_val = held_qty * curr_price
    buy_val = held_qty * avg_buy_p
    pnl = eval_val - buy_val
    pnl_pct = (pnl / buy_val * 100) if buy_val > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("보유 예수금", f"${st.session_state.cash:,.2f}")
    c2.metric(f"보유 수량 ({ticker})", f"{held_qty:,} 주")
    c3.metric("평균 단가", f"${avg_buy_p:,.2f}")
    c4.metric("평가 손익", f"${pnl:,.2f}", f"{pnl_pct:+.2f}%")

    st.markdown("---")
    
    col_trade, col_port = st.columns([1, 1])
    
    # 주문 실행 폼
    with col_trade:
        st.subheader("🛒 주문하기")
        st.write(f"현재 **{ticker}** 시장가: **${curr_price:,.2f}**")
        
        trade_qty = st.number_input("주문 수량(주)", min_value=1, value=10, step=1)
        total_cost = trade_qty * curr_price
        st.caption(f"총 주문 금액: **${total_cost:,.2f}**")
        
        btn_buy, btn_sell = st.columns(2)
        
        with btn_buy:
            if st.button("🔴 매수 (Buy)", type="primary", use_container_width=True):
                if st.session_state.cash < total_cost:
                    st.error("예수금이 부족합니다.")
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
                        '체결가': f"${curr_price:,.2f}"
                    })
                    st.success(f"{ticker} {trade_qty}주 매수 완료!")
                    st.rerun()

        with btn_sell:
            if st.button("🔵 매도 (Sell)", use_container_width=True):
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
                        '체결가': f"${curr_price:,.2f}"
                    })
                    st.success(f"{ticker} {trade_qty}주 매도 완료!")
                    st.rerun()

    # 보유 포트폴리오 현황
    with col_port:
        st.subheader("📋 내 보유 포트폴리오")
        if not st.session_state.portfolio:
            st.info("현재 보유 중인 주식이 없습니다.")
        else:
            port_data = []
            for t_code, info in st.session_state.portfolio.items():
                port_data.append({
                    "종목": t_code,
                    "보유수량": f"{info['qty']}주",
                    "평균단가": f"${info['avg_price']:,.2f}",
                    "평가금액": f"${info['qty'] * curr_price:,.2f}"
                })
            st.table(pd.DataFrame(port_data))
            
    # 체결 내역
    if st.session_state.trade_history:
        st.markdown("---")
        st.subheader("📜 최근 거래 내역")
        st.dataframe(pd.DataFrame(st.session_state.trade_history).iloc[::-1], use_container_width=True)

# ----------------------------------------------------
# TAB 4: 백테스팅
# ----------------------------------------------------
with tab4:
    st.markdown('<div class="guide-box"><b>전략 백테스팅</b>: SMA 크로스오버 전략으로 과거 데이터 기반의 수익률을 시뮬레이션합니다.</div>', unsafe_allow_html=True)
    
    if current_plan == "Free":
        st.caption("🔒 Free 요금제에서는 기본 전략 매개변수(20/60일)로 백테스팅이 제한됩니다.")
        short_w = 20
        long_w = 60
    else:
        c1, c2 = st.columns(2)
        with c1:
            short_w = st.slider("단기 이동평균선 (일)", 5, 50, 20)
        with c2:
            long_w = st.slider("장기 이동평균선 (일)", 20, 200, 60)
            
    bt_df = df.copy()
    bt_df['Short_MA'] = bt_df['Close'].rolling(window=short_w).mean()
    bt_df['Long_MA'] = bt_df['Close'].rolling(window=long_w).mean()
    
    bt_df['Signal'] = 0
    bt_df.loc[bt_df['Short_MA'] > bt_df['Long_MA'], 'Signal'] = 1
    bt_df['Position'] = bt_df['Signal'].shift(1)
    
    bt_df['Market_Return'] = bt_df['Close'].pct_change()
    bt_df['Strategy_Return'] = bt_df['Market_Return'] * bt_df['Position']
    
    cum_market = (1 + bt_df['Market_Return']).cumprod()
    cum_strategy = (1 + bt_df['Strategy_Return']).cumprod()
    
    fig_bt = go.Figure()
    fig_bt.add_trace(go.Scatter(x=bt_df.index, y=cum_market, mode='lines', name='단순 보유 (Buy & Hold)', line=dict(color='#94A3B8')))
    fig_bt.add_trace(go.Scatter(x=bt_df.index, y=cum_strategy, mode='lines', name='SMA 전략 수익률', line=dict(color='#10B981', width=2)))
    fig_bt.update_layout(template="plotly_dark", height=400, yaxis_title="누적 수익률 배수")
    st.plotly_chart(fig_bt, use_container_width=True)

# ----------------------------------------------------
# TAB 5: 변동성 및 위험 분석
# ----------------------------------------------------
with tab5:
    st.markdown('<div class="guide-box"><b>위험도 분석</b>: 낙폭(Drawdown) 및 일일 수익률 분포를 통한 손실 리스크 평가를 제공합니다.</div>', unsafe_allow_html=True)
    
    daily_ret = df['Close'].pct_change().dropna()
    cum_ret = (1 + daily_ret).cumprod()
    peak = cum_ret.cummax()
    drawdown = (cum_ret - peak) / peak
    
    mdd = drawdown.min() * 100
    volatility = daily_ret.std() * np.sqrt(252) * 100
    
    col_v1, col_v2 = st.columns(2)
    col_v1.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
    col_v2.metric("연환산 변동성", f"{volatility:.2f}%")
    
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(x=drawdown.index, y=drawdown * 100, fill='tozeroy', mode='lines', line=dict(color='#EF4444')))
    fig_dd.update_layout(template="plotly_dark", height=300, yaxis_title="낙폭 비율 (%)")
    st.plotly_chart(fig_dd, use_container_width=True)

# ----------------------------------------------------
# TAB 6: 몬테카를로 AI 예측 (Pro 전용 잠금)
# ----------------------------------------------------
with tab6:
    st.markdown('<div class="guide-box"><b>몬테카를로 확률 예측</b>: 미래 주가 확률 분포 및 포트폴리오 시뮬레이션을 제공합니다.</div>', unsafe_allow_html=True)
    
    # Pro 모드가 아닌 경우 (Free, Lite) 기능 잠금 처리
    if current_plan != "Pro":
        st.warning("🔒 **몬테카를로 AI 예측 기능은 Pro 멤버십 전용 기능입니다.**")
        
        st.markdown("""
        <div style="background-color: #1E293B; border: 1px solid #334155; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
            <b style="color: #38BDF8;">👑 Pro 멤버십 혜택</b><br>
            • 복수 종목 분할 투자 포트폴리오 시뮬레이션<br>
            • 최대 10,000회 몬테카를로 난수 시뮬레이션 지원<br>
            • 상위/하위 10% 위험 자산 및 예상 수익률 분석
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("👑 Pro 멤버십으로 업그레이드하기", type="primary"):
            st.toast("결제 페이지로 이동합니다. (테스트용 기능)")
    else:
        st.success("👑 **Pro 멤버십 혜택**: 몬테카를로 확률 예측 시뮬레이션이 활성화되었습니다.")
        
        selected_mc_tickers = st.multiselect(
            "시뮬레이션할 포트폴리오 종목 구성", 
            list(POPULAR_STOCKS.values()) + ["GOOGL", "AMZN", "MSFT"],
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
            with col_m1:
                init_budget = st.number_input("투자 예산 (원금)", min_value=100000, value=10000000, step=1000000)
            with col_m2:
                pred_days = st.slider("예측 기간 (일수)", min_value=30, max_value=252, value=90, step=30)
            with col_m3:
                num_sims = 10000  # Pro 전용 10,000회 고정
                st.caption(f"시뮬레이션 횟수: **{num_sims:,}회 (Pro)**")
                
            today = datetime.today()
            start_1y = today - timedelta(days=365)
            df_mc = fetch_multi_ticker_data(selected_mc_tickers, str(start_1y.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))
            
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

                st.markdown(f"##### {init_budget:,.0f}원 투자 시 {pred_days}일 후 예상 자산 평가")
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
