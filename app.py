import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from supabase import create_client, Client

# ==========================================
# 0. PAGE CONFIGURATION & CUSTOM STYLES
# ==========================================
st.set_page_config(
    page_title="StockLab - Quant & AI Paper Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase DB Settings (Streamlit Secrets 우선 참조, 미설정 시 기본값/안내)
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", "https://aenomakwawdfikftscer.supabase.co")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
except Exception:
    SUPABASE_URL = "https://aenomakwawdfikftscer.supabase.co"
    SUPABASE_KEY = ""

@st.cache_resource
def init_supabase():
    try:
        if SUPABASE_KEY and SUPABASE_KEY.strip() and SUPABASE_KEY != "여기에_Publishable_키를_입력하세요":
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        return None
    except Exception:
        return None

supabase: Client = init_supabase()

st.markdown("""
<style>
    .stMetric {
        background-color: #1E222D;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #2A2E39;
    }
    .stMetric label {
        font-size: 0.85rem !important;
        color: #787B86 !important;
    }
    .stMetric div[data-testid="stMetricValue"] {
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    .badge-pro {
        background-color: #FF4654;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .badge-lite {
        background-color: #2962FF;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .badge-free {
        background-color: #787B86;
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: bold;
    }
    .disclaimer-box {
        background-color: #2A2E39;
        border-left: 4px solid #FF9800;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.82rem;
        color: #B2B5BE;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = "Guest"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free"
if "cash_balance" not in st.session_state:
    st.session_state.cash_balance = 100000.0
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []
if "order_qty_input" not in st.session_state:
    st.session_state.order_qty_input = 1

# Helper: Sync to Supabase
def save_user_data_to_db():
    if st.session_state.authenticated and st.session_state.user_id and supabase:
        try:
            data = {
                "user_id": st.session_state.user_id,
                "tier": st.session_state.user_tier,
                "cash_balance": float(st.session_state.cash_balance),
                "portfolio": st.session_state.portfolio,
                "trade_history": st.session_state.trade_history
            }
            supabase.table("user_data").upsert(data).execute()
        except Exception:
            pass

def load_user_data_from_db(user_id):
    if supabase:
        try:
            res = supabase.table("user_data").select("*").eq("user_id", user_id).execute()
            if res.data and len(res.data) > 0:
                row = res.data[0]
                st.session_state.user_tier = row.get("tier", "Free")
                st.session_state.cash_balance = float(row.get("cash_balance", 100000.0))
                st.session_state.portfolio = row.get("portfolio", {})
                st.session_state.trade_history = row.get("trade_history", [])
        except Exception:
            pass

# Callback helpers for order quantity buttons
def set_order_qty(val: int):
    st.session_state.order_qty_input = max(1, int(val))

def set_max_order_qty(balance: float, price: float):
    if price > 0:
        st.session_state.order_qty_input = max(1, int(balance // price))

# ==========================================
# 1. SIDEBAR & AUTHENTICATION
# ==========================================
with st.sidebar:
    st.title("StockLab")
    
    tier_badge = f'<span class="badge-{st.session_state.user_tier.lower()}">{st.session_state.user_tier}</span>'
    st.markdown(f"**현재 계정:** {st.session_state.user_email} {tier_badge}", unsafe_allow_html=True)
    
    # 간편 서비스 모드/플랜 전환 (프로토타입 테스트용)
    selected_tier = st.selectbox(
        "⚡ 서비스 모드 전환", 
        ["Free", "Lite", "Pro"], 
        index=["Free", "Lite", "Pro"].index(st.session_state.user_tier)
    )
    if selected_tier != st.session_state.user_tier:
        st.session_state.user_tier = selected_tier
        save_user_data_to_db()
        st.rerun()

    st.divider()
    
    st.subheader("🔐 계정 관리")
    if not supabase:
        st.caption("⚠️ Supabase 미연결 상태입니다. (로컬 메모리 모드로 동작 중)")
    
    auth_mode = st.radio("인증 선택", ["로그인", "회원가입"], key="auth_mode_radio")
    
    email_input = st.text_input("이메일 주소", key="auth_email")
    password_input = st.text_input("비밀번호", type="password", key="auth_password")
    
    if auth_mode == "회원가입":
        if st.button("회원가입 실행", use_container_width=True):
            if not email_input or not password_input:
                st.error("이메일과 비밀번호를 모두 입력해 주세요.")
            elif not supabase:
                st.error("Supabase API 키 설정이 올바르지 않습니다. Secrets를 확인해 주세요.")
            else:
                try:
                    res = supabase.auth.sign_up({"email": email_input, "password": password_input})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_email = res.user.email
                        st.session_state.user_id = res.user.id
                        save_user_data_to_db()
                        st.success("회원가입 완료 및 로그인 성공!")
                        st.rerun()
                    else:
                        st.error("회원가입 처리 중 오류가 발생했습니다.")
                except Exception as e:
                    st.error(f"회원가입 실패: {str(e)}")

    elif auth_mode == "로그인":
        if st.button("로그인 실행", use_container_width=True):
            if not email_input or not password_input:
                st.error("이메일과 비밀번호를 입력해 주세요.")
            elif not supabase:
                st.error("Supabase API 키 설정이 올바르지 않습니다. Secrets를 확인해 주세요.")
            else:
                try:
                    res = supabase.auth.sign_in_with_password({"email": email_input, "password": password_input})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_email = res.user.email
                        st.session_state.user_id = res.user.id
                        load_user_data_from_db(res.user.id)
                        st.success("로그인 성공!")
                        st.rerun()
                    else:
                        st.error("이메일 또는 비밀번호가 올바르지 않습니다.")
                except Exception as e:
                    st.error(f"로그인 실패: {str(e)}")

    if st.session_state.authenticated:
        if st.button("로그아웃", use_container_width=True):
            if supabase:
                try:
                    supabase.auth.sign_out()
                except Exception:
                    pass
            st.session_state.authenticated = False
            st.session_state.user_email = "Guest"
            st.session_state.user_id = None
            st.session_state.user_tier = "Free"
            st.session_state.cash_balance = 100000.0
            st.session_state.portfolio = {}
            st.session_state.trade_history = []
            st.rerun()

    st.divider()
    
    st.subheader("⚙️ 종목 선택")
    popular_tickers = {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "NVIDIA (NVDA)": "NVDA",
        "Tesla (TSLA)": "TSLA",
        "ProShares 3x QQQ (TQQQ)": "TQQQ",
        "Direxion 3x Semiconductor (SOXL)": "SOXL",
        "Bitcoin USD (BTC-USD)": "BTC-USD",
        "삼성전자 (005930.KS)": "005930.KS"
    }
    
    selected_name = st.selectbox("인기 종목 바로선택", list(popular_tickers.keys()))
    symbol = st.text_input("티커 직접 입력", popular_tickers[selected_name]).upper().strip()
    
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    st.caption("ℹ️ 최근 1년 데이터로 자동 분석됩니다.")

# Fetch Data
@st.cache_data(ttl=3600)
def load_stock_data(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except Exception:
        return None

df_stock = load_stock_data(symbol, start_date, end_date)

# ==========================================
# 2. MAIN HEADER & SUMMARY METRICS
# ==========================================
st.title("StockLab Quant & Paper Trading Platform")

if df_stock is not None and not df_stock.empty:
    current_price = float(df_stock['Close'].iloc[-1])
    prev_price = float(df_stock['Close'].iloc[-2]) if len(df_stock) > 1 else current_price
    price_change = current_price - prev_price
    pct_change = (price_change / prev_price) * 100

    # Calculate Portfolio Valuation
    total_stock_val = 0.0
    for t_sym, qty in st.session_state.portfolio.items():
        if qty > 0:
            t_df = load_stock_data(t_sym, datetime.date.today() - datetime.timedelta(days=7), datetime.date.today())
            if t_df is not None and not t_df.empty:
                total_stock_val += float(t_df['Close'].iloc[-1]) * qty

    total_asset = st.session_state.cash_balance + total_stock_val
    profit_loss = total_asset - 100000.0
    profit_loss_pct = (profit_loss / 100000.0) * 100

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(f"선택 종목 ({symbol})", f"${current_price:,.2f}", f"{price_change:+,.2f} ({pct_change:+.2f}%)")
    m2.metric("보유 예수금 (Cash)", f"${st.session_state.cash_balance:,.2f}")
    m3.metric("총 평가 자산 (Total)", f"${total_asset:,.2f}")
    m4.metric("누적 수익률 (P&L)", f"${profit_loss:+,.2f}", f"{profit_loss_pct:+.2f}%")
else:
    current_price = 0.0
    st.warning(f"'{symbol}' 종목 데이터를 불러올 수 없습니다. 티커를 확인해 주세요.")

st.divider()

# ==========================================
# 3. MAIN TABS
# ==========================================
t1, t2, t3, t4, t5, t6 = st.tabs([
    "💰 모의주식 거래", 
    "📊 포트폴리오 분석", 
    "📈 기술적 차트", 
    "🤖 AI 매매 마커", 
    "⚡ 퀀트 리스크", 
    "🔮 몬테카를로 (Pro)"
])

# ------------------------------------------
# TAB 1: Paper Trading
# ------------------------------------------
with t1:
    st.subheader("모의주식 매수 / 매도")
    if df_stock is not None and not df_stock.empty:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"**현재가:** `${current_price:,.2f}`")
            
            b1, b2, b3, b4 = st.columns(4)
            b1.button("+10주", on_click=set_order_qty, args=(10,), use_container_width=True)
            b2.button("+50주", on_click=set_order_qty, args=(50,), use_container_width=True)
            b3.button("+100주", on_click=set_order_qty, args=(100,), use_container_width=True)
            b4.button("전액매수", on_click=set_max_order_qty, args=(st.session_state.cash_balance, current_price), use_container_width=True)

            order_qty = st.number_input("주문 수량 (주)", min_value=1, step=1, key="order_qty_input")

            total_cost = order_qty * current_price
            st.caption(f"예상 거래 금액: `${total_cost:,.2f}`")
            
            btn_buy, btn_sell = st.columns(2)
            if btn_buy.button("🟢 매수 실행", use_container_width=True):
                if st.session_state.cash_balance >= total_cost:
                    st.session_state.cash_balance -= total_cost
                    st.session_state.portfolio[symbol] = st.session_state.portfolio.get(symbol, 0) + order_qty
                    st.session_state.trade_history.append({
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "BUY",
                        "symbol": symbol,
                        "qty": order_qty,
                        "price": current_price,
                        "total": total_cost
                    })
                    save_user_data_to_db()
                    st.success(f"{symbol} {order_qty}주 매수 완료!")
                    st.rerun()
                else:
                    st.error("예수금이 부족합니다.")
            
            if btn_sell.button("🔴 매도 실행", use_container_width=True):
                current_qty = st.session_state.portfolio.get(symbol, 0)
                if current_qty >= order_qty:
                    st.session_state.cash_balance += total_cost
                    st.session_state.portfolio[symbol] -= order_qty
                    if st.session_state.portfolio[symbol] == 0:
                        del st.session_state.portfolio[symbol]
                    st.session_state.trade_history.append({
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "SELL",
                        "symbol": symbol,
                        "qty": order_qty,
                        "price": current_price,
                        "total": total_cost
                    })
                    save_user_data_to_db()
                    st.success(f"{symbol} {order_qty}주 매도 완료!")
                    st.rerun()
                else:
                    st.error("보유 수량이 부족합니다.")

        with c2:
            st.markdown("### 💼 현재 보유 포트폴리오")
            if st.session_state.portfolio:
                pf_data = []
                for sym, qty in st.session_state.portfolio.items():
                    pf_data.append({"종목": sym, "보유 수량": f"{qty} 주"})
                st.dataframe(pd.DataFrame(pf_data), use_container_width=True)
            else:
                st.info("현재 보유 중인 주식이 없습니다.")

            st.markdown("### 📜 최근 거래 내역")
            if st.session_state.trade_history:
                st.dataframe(pd.DataFrame(st.session_state.trade_history).iloc[::-1], use_container_width=True)
            else:
                st.info("거래 내역이 없습니다.")

# ------------------------------------------
# TAB 2: Portfolio Analyzer
# ------------------------------------------
with t2:
    st.subheader("포트폴리오 비중 분석 & 예산 설계")
    
    symbols_input = st.text_input("분석할 티커 목록 (쉼표 구분)", "AAPL, MSFT, NVDA, TSLA")
    tickers_list = [t.strip().upper() for t in symbols_input.split(",") if t.strip()]

    total_budget = st.number_input("총 투자 예산 ($)", min_value=100.0, value=10000.0, step=500.0)

    if len(tickers_list) >= 2:
        raw_weights = []
        st.write("각 종목 비중 입력 (%)")
        cols = st.columns(len(tickers_list))
        default_w = round(100.0 / len(tickers_list), 2)
        for i, t_name in enumerate(tickers_list):
            w = cols[i].number_input(f"{t_name} (%)", value=default_w, min_value=0.0, max_value=100.0, step=1.0)
            raw_weights.append(w)

        sum_w = sum(raw_weights)
        if sum_w <= 0:
            st.error("비중의 합은 0보다 커야 합니다.")
        else:
            norm_weights = [w / sum_w for w in raw_weights]
            
            # 종목별 구매 금액 및 수량 자동 계산
            raw_multi = yf.download(tickers_list, start=start_date, end=end_date)
            if isinstance(raw_multi, pd.DataFrame) and not raw_multi.empty:
                if 'Close' in raw_multi.columns:
                    df_multi = raw_multi['Close']
                else:
                    df_multi = raw_multi
                
                # MultiIndex 정리
                if isinstance(df_multi.columns, pd.MultiIndex):
                    df_multi.columns = df_multi.columns.get_level_values(0)

                st.markdown("### 💵 종목별 추천 매수 금액 및 주식 수")
                allocation_data = []
                for i, t_name in enumerate(tickers_list):
                    allocated_money = total_budget * norm_weights[i]
                    last_price = float(df_multi[t_name].dropna().iloc[-1]) if t_name in df_multi.columns and not df_multi[t_name].dropna().empty else 0.0
                    estimated_shares = int(allocated_money // last_price) if last_price > 0 else 0
                    
                    allocation_data.append({
                        "종목": t_name,
                        "비중 (%)": f"{norm_weights[i]*100:.1f}%",
                        "현재가 ($)": f"${last_price:,.2f}",
                        "배정 금액 ($)": f"${allocated_money:,.2f}",
                        "매수 가능 수량": f"{estimated_shares:,} 주"
                    })
                st.dataframe(pd.DataFrame(allocation_data), use_container_width=True)

                # 백테스트 차트
                df_returns = df_multi.pct_change().dropna()
                portfolio_return = (df_returns * norm_weights).sum(axis=1)
                cum_return = (1 + portfolio_return).cumprod()

                fig_pf = go.Figure()
                fig_pf.add_trace(go.Scatter(x=cum_return.index, y=cum_return.values, mode='lines', name='포트폴리오 성과'))
                fig_pf.update_layout(title="포트폴리오 백테스트 (1년 누적 성과)", xaxis_title="날짜", yaxis_title="배수 (1.0 = 원금)")
                st.plotly_chart(fig_pf, use_container_width=True)

                st.subheader("상관관계 히트맵")
                corr = df_returns.corr()
                fig_corr = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, colorscale='Viridis'))
                st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("포트폴리오 분석을 위해 최소 2개 이상의 종목을 입력해 주세요.")

# ------------------------------------------
# TAB 3: Technical Chart
# ------------------------------------------
with t3:
    st.subheader(f"{symbol} 기술적 분석 차트")
    if df_stock is not None and not df_stock.empty:
        df_tc = df_stock.copy()
        df_tc['MA20'] = df_tc['Close'].rolling(window=20).mean()
        df_tc['MA60'] = df_tc['Close'].rolling(window=60).mean()
        df_tc['STD20'] = df_tc['Close'].rolling(window=20).std()
        df_tc['Upper'] = df_tc['MA20'] + (df_tc['STD20'] * 2)
        df_tc['Lower'] = df_tc['MA20'] - (df_tc['STD20'] * 2)

        fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_tech.add_trace(go.Candlestick(x=df_tc.index, open=df_tc['Open'], high=df_tc['High'], low=df_tc['Low'], close=df_tc['Close'], name='주가'), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['MA20'], mode='lines', name='MA 20', line=dict(color='orange')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['MA60'], mode='lines', name='MA 60', line=dict(color='blue')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['Upper'], mode='lines', name='볼린저 상한', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['Lower'], mode='lines', name='볼린저 하한', line=dict(color='gray', dash='dash')), row=1, col=1)

        fig_tech.add_trace(go.Bar(x=df_tc.index, y=df_tc['Volume'], name='거래량', marker_color='teal'), row=2, col=1)
        fig_tech.update_layout(xaxis_rangeslider_visible=False, height=600)
        st.plotly_chart(fig_tech, use_container_width=True)

# ------------------------------------------
# TAB 4: AI Signal Markers
# ------------------------------------------
with t4:
    st.subheader("🤖 AI 이동평균 골든/데드크로스 매매 시그널")
    
    st.markdown("""
    <div class="disclaimer-box">
        ⚠️ <b>법적 안내 및 면책 공지</b><br>
        본 AI 매매 시그널은 가상 알고리즘 및 기술적 분석 지표에 기초한 모의투자 참고용 데이터이며, 특정 종목에 대한 투자 권유나 수익을 보장하지 않습니다. 모든 투자 판단에 대한 책임은 본인에게 있습니다.
    </div>
    """, unsafe_allow_html=True)

    if df_stock is not None and not df_stock.empty:
        df_ai = df_stock.copy()
        df_ai['MA20'] = df_ai['Close'].rolling(window=20).mean()
        df_ai['MA60'] = df_ai['Close'].rolling(window=60).mean()
        
        buy_signals = (df_ai['MA20'] > df_ai['MA60']) & (df_ai['MA20'].shift(1) <= df_ai['MA60'].shift(1))
        sell_signals = (df_ai['MA20'] < df_ai['MA60']) & (df_ai['MA20'].shift(1) >= df_ai['MA60'].shift(1))

        fig_ai = go.Figure()
        fig_ai.add_trace(go.Scatter(x=df_ai.index, y=df_ai['Close'], mode='lines', name='종가', line=dict(color='gray')))
        fig_ai.add_trace(go.Scatter(x=df_ai.index, y=df_ai['MA20'], mode='lines', name='MA20', line=dict(color='orange')))
        fig_ai.add_trace(go.Scatter(x=df_ai.index, y=df_ai['MA60'], mode='lines', name='MA60', line=dict(color='blue')))

        fig_ai.add_trace(go.Scatter(
            x=df_ai[buy_signals].index, y=df_ai[buy_signals]['Close'],
            mode='markers', name='▲ AI 매수 시그널',
            marker=dict(symbol='triangle-up', size=12, color='green')
        ))
        fig_ai.add_trace(go.Scatter(
            x=df_ai[sell_signals].index, y=df_ai[sell_signals]['Close'],
            mode='markers', name='▼ AI 매도 시그널',
            marker=dict(symbol='triangle-down', size=12, color='red')
        ))
        fig_ai.update_layout(height=500, title=f"{symbol} 최근 1년 AI 매매 시그널")
        st.plotly_chart(fig_ai, use_container_width=True)

# ------------------------------------------
# TAB 5: Quant Risk Analysis
# ------------------------------------------
with t5:
    st.subheader("퀀트 리스크 & 지표 분석")
    if df_stock is not None and not df_stock.empty:
        df_q = df_stock.copy()
        df_q['Return'] = df_q['Close'].pct_change()
        
        cum_ret = (1 + df_q['Return']).cumprod()
        peak = cum_ret.cummax()
        dd = (cum_ret - peak) / peak
        mdd = dd.min() * 100

        vol = df_q['Return'].std() * np.sqrt(252) * 100
        sharpe = (df_q['Return'].mean() * 252) / (df_q['Return'].std() * np.sqrt(252)) if df_q['Return'].std() != 0 else 0

        q1, q2, q3 = st.columns(3)
        q1.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
        q2.metric("연환산 변동성", f"{vol:.2f}%")
        q3.metric("샤프 지수 (Sharpe Ratio)", f"{sharpe:.2f}")

        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=dd.index, y=dd * 100, mode='lines', name='Drawdown (%)', fill='tozeroy', line=dict(color='red')))
        fig_dd.update_layout(title="Drawdown (낙폭) 차트", yaxis_title="낙폭 (%)", height=350)
        st.plotly_chart(fig_dd, use_container_width=True)

# ------------------------------------------
# TAB 6: Monte Carlo (Pro)
# ------------------------------------------
with t6:
    st.subheader("🔮 몬테카를로 시뮬레이션 (Pro 전용)")
    if st.session_state.user_tier != "Pro":
        st.warning("⚠️ 몬테카를로 시뮬레이션 기능은 **Pro 요금제** 전용 기능입니다.")
        st.info("왼쪽 사이드바의 '서비스 모드 전환'에서 **Pro** 선택 시 즉시 사용해 보실 수 있습니다.")
    else:
        if df_stock is not None and not df_stock.empty:
            st.success("Pro 회원 인증 완료: 몬테카를로 200회 시뮬레이션을 실행합니다.")
            returns = df_stock['Close'].pct_change().dropna()
            mu = returns.mean()
            sigma = returns.std()
            last_price = float(df_stock['Close'].iloc[-1])

            days = 252
            sims = 200
            
            # Vectorized Monte Carlo generation for optimal performance
            daily_returns = np.exp((mu - 0.5 * sigma**2) + sigma * np.random.normal(size=(days, sims)))
            price_paths = np.zeros((days + 1, sims))
            price_paths[0] = last_price
            for d in range(days):
                price_paths[d + 1] = price_paths[d] * daily_returns[d]

            fig_mc = go.Figure()
            # Plot up to 50 paths to maintain fluid rendering
            for col in range(min(50, sims)):
                fig_mc.add_trace(go.Scatter(y=price_paths[:, col], mode='lines', line=dict(width=1), showlegend=False))
            fig_mc.update_layout(title=f"{symbol} 향후 1년 주가 예측 (200개 시나리오)", xaxis_title="경과 일수", yaxis_title="예측 주가 ($)")
            st.plotly_chart(fig_mc, use_container_width=True)
