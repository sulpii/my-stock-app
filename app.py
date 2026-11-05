import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from zoneinfo import ZoneInfo
from supabase import create_client, Client

# ==========================================
# 0. PAGE CONFIGURATION & RESPONSIVE STYLES
# ==========================================
st.set_page_config(
    page_title="StockLab - Quant & Paper Trading",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Supabase DB Settings (Streamlit Secrets 우선 참조, 미설정 시 메모리 모드로 안전 동작)
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

# 모바일 반응형 및 다크 테마 커스텀 CSS
st.markdown("""
<style>
    /* 메트릭 카드 스타일 */
    .stMetric {
        background-color: #1E222D;
        padding: 12px 16px;
        border-radius: 8px;
        border: 1px solid #2A2E39;
        margin-bottom: 8px;
    }
    .stMetric label {
        font-size: 0.82rem !important;
        color: #787B86 !important;
    }
    .stMetric div[data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }

    /* 티어 배지 */
    .badge-pro { background-color: #FF4654; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-lite { background-color: #2962FF; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }
    .badge-free { background-color: #787B86; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; }

    /* 장 상태 배지 */
    .badge-market-open { background-color: #089981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
    .badge-market-closed { background-color: #5D606B; color: white; padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }

    /* 면책 공지 박스 */
    .disclaimer-box {
        background-color: #2A2E39;
        border-left: 4px solid #FF9800;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.82rem;
        color: #B2B5BE;
        margin-bottom: 15px;
    }

    /* 모바일 반응형 그리드 조정 */
    @media (max-width: 768px) {
        .stMetric div[data-testid="stMetricValue"] {
            font-size: 1.05rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------
# Session State Initialization
# ------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = "Guest"
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_tier" not in st.session_state:
    st.session_state.user_tier = "Free"
if "cash_balance" not in st.session_state:
    st.session_state.cash_balance = 100000.0  # 초기 모의 시드: $100,000
if "portfolio" not in st.session_state:
    st.session_state.portfolio = {}  # {symbol: {"qty": int, "avg_price": float}}
if "trade_history" not in st.session_state:
    st.session_state.trade_history = []
if "order_qty_input" not in st.session_state:
    st.session_state.order_qty_input = 1

# 거래 수수료율 (증권사 표준 유관기관 수수료 포함: 0.1%)
TRADING_FEE_RATE = 0.001

# ------------------------------------------
# DB & State Helper Functions
# ------------------------------------------
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

def set_order_qty(val: int):
    st.session_state.order_qty_input = max(1, int(val))

def set_max_order_qty(balance: float, price: float):
    if price > 0:
        effective_price = price * (1 + TRADING_FEE_RATE)
        st.session_state.order_qty_input = max(1, int(balance // effective_price))

def check_us_market_status():
    """미국 정규 주식 시장(09:30~16:00 EST, 월~금) 운영 상태 판정"""
    try:
        now_ny = datetime.datetime.now(ZoneInfo("America/New_York"))
        if now_ny.weekday() < 5:  # 월~금
            market_open = now_ny.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now_ny.replace(hour=16, minute=0, second=0, microsecond=0)
            if market_open <= now_ny <= market_close:
                return True, now_ny.strftime("%H:%M ET")
        return False, now_ny.strftime("%H:%M ET")
    except Exception:
        return False, "Closed"

# ==========================================
# 1. SIDEBAR & AUTHENTICATION
# ==========================================
with st.sidebar:
    st.title("StockLab")
    
    tier_badge = f'<span class="badge-{st.session_state.user_tier.lower()}">{st.session_state.user_tier}</span>'
    st.markdown(f"**현재 계정:** {st.session_state.user_email} {tier_badge}", unsafe_allow_html=True)
    
    # 서비스 모드 전환
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
        st.caption("ℹ️ Supabase 미연결 (로컬 메모리 모드로 정상 동작 중)")
    
    auth_mode = st.radio("인증 선택", ["로그인", "회원가입"], key="auth_mode_radio")
    email_input = st.text_input("이메일 주소", key="auth_email")
    password_input = st.text_input("비밀번호", type="password", key="auth_password")
    
    if auth_mode == "회원가입":
        if st.button("회원가입 실행", use_container_width=True):
            if not email_input or not password_input:
                st.error("이메일과 비밀번호를 입력해 주세요.")
            elif not supabase:
                st.warning("Supabase Secrets 설정 후 계정이 영구 보존됩니다.")
            else:
                try:
                    res = supabase.auth.sign_up({"email": email_input, "password": password_input})
                    if res.user:
                        st.session_state.authenticated = True
                        st.session_state.user_email = res.user.email
                        st.session_state.user_id = res.user.id
                        save_user_data_to_db()
                        st.success("회원가입 및 로그인 완료!")
                        st.rerun()
                except Exception as e:
                    st.error(f"회원가입 오류: {str(e)}")

    elif auth_mode == "로그인":
        if st.button("로그인 실행", use_container_width=True):
            if not email_input or not password_input:
                st.error("이메일과 비밀번호를 입력해 주세요.")
            elif not supabase:
                st.warning("Supabase Secrets가 설정되지 않아 게스트 모드로 동작합니다.")
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
    
    if st.button("🔄 시세 데이터 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption("ℹ️ 시세 캐시 주기: 15분 (지연 최소화 & 안정적 무료 데이터)")

# ------------------------------------------
# Fetch Stock Data (15-min TTL Cache)
# ------------------------------------------
@st.cache_data(ttl=900)
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
is_market_open, market_time_str = check_us_market_status()
market_badge = '<span class="badge-market-open">🟢 정규장 진행 중</span>' if is_market_open else f'<span class="badge-market-closed">⚪ 정규장 마감 ({market_time_str})</span>'

st.title("StockLab Quant & Paper Trading")
st.markdown(f"**시장 상태:** {market_badge} | 거래 수수료: `0.1% 반영`", unsafe_allow_html=True)

if df_stock is not None and not df_stock.empty:
    current_price = float(df_stock['Close'].iloc[-1])
    prev_price = float(df_stock['Close'].iloc[-2]) if len(df_stock) > 1 else current_price
    price_change = current_price - prev_price
    pct_change = (price_change / prev_price) * 100

    # 포트폴리오 평가액 및 손익 계산
    total_stock_val = 0.0
    for t_sym, item in st.session_state.portfolio.items():
        qty = item.get("qty", 0) if isinstance(item, dict) else item
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
    m4.metric("누적 모의 수익률 (P&L)", f"${profit_loss:+,.2f}", f"{profit_loss_pct:+.2f}%")
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
    "⚡ 퀀트 전략 시그널", 
    "🛡️ 퀀트 리스크", 
    "🔮 몬테카를로 (Pro)"
])

# ------------------------------------------
# TAB 1: Paper Trading (수수료 및 현실적 체결 모델)
# ------------------------------------------
with t1:
    st.subheader("모의주식 매수 / 매도")
    if not is_market_open:
        st.info("ℹ️ 현재는 정규장 외 시간입니다. 모의 주문은 전일 종가 기준으로 가상 체결됩니다.")

    if df_stock is not None and not df_stock.empty:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown(f"**현재 기준가:** `${current_price:,.2f}`")
            
            b1, b2, b3, b4 = st.columns(4)
            b1.button("+10주", on_click=set_order_qty, args=(10,), use_container_width=True)
            b2.button("+50주", on_click=set_order_qty, args=(50,), use_container_width=True)
            b3.button("+100주", on_click=set_order_qty, args=(100,), use_container_width=True)
            b4.button("전액매수", on_click=set_max_order_qty, args=(st.session_state.cash_balance, current_price), use_container_width=True)

            order_qty = st.number_input("주문 수량 (주)", min_value=1, step=1, key="order_qty_input")

            # 수수료 계산
            stock_amount = order_qty * current_price
            est_fee = stock_amount * TRADING_FEE_RATE
            total_buy_cost = stock_amount + est_fee
            total_sell_proceeds = max(0.0, stock_amount - est_fee)

            st.caption(f"주식 금액: `${stock_amount:,.2f}` | 증권 수수료 (0.1%): `${est_fee:,.2f}`")
            st.markdown(f"**최종 결제 예상액:** 매수 시 `${total_buy_cost:,.2f}` / 매도 시 `${total_sell_proceeds:,.2f}`")

            btn_buy, btn_sell = st.columns(2)
            if btn_buy.button("🟢 매수 실행", use_container_width=True):
                if st.session_state.cash_balance >= total_buy_cost:
                    st.session_state.cash_balance -= total_buy_cost
                    
                    # 포트폴리오 평단가 관리
                    current_holding = st.session_state.portfolio.get(symbol, {"qty": 0, "avg_price": 0.0})
                    if isinstance(current_holding, int):
                        current_holding = {"qty": current_holding, "avg_price": current_price}
                    
                    old_qty = current_holding.get("qty", 0)
                    old_avg = current_holding.get("avg_price", current_price)
                    new_qty = old_qty + order_qty
                    new_avg = ((old_qty * old_avg) + (order_qty * current_price)) / new_qty if new_qty > 0 else current_price
                    
                    st.session_state.portfolio[symbol] = {"qty": new_qty, "avg_price": new_avg}
                    st.session_state.trade_history.append({
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "BUY",
                        "symbol": symbol,
                        "qty": order_qty,
                        "price": current_price,
                        "fee": est_fee,
                        "total": total_buy_cost
                    })
                    save_user_data_to_db()
                    st.success(f"{symbol} {order_qty}주 매수 완료! (수수료 ${est_fee:,.2f} 차감)")
                    st.rerun()
                else:
                    st.error("예수금이 부족합니다. (수수료 포함 금액을 확인해 주세요)")

            if btn_sell.button("🔴 매도 실행", use_container_width=True):
                current_holding = st.session_state.portfolio.get(symbol, {"qty": 0, "avg_price": 0.0})
                current_qty = current_holding.get("qty", 0) if isinstance(current_holding, dict) else current_holding
                
                if current_qty >= order_qty:
                    st.session_state.cash_balance += total_sell_proceeds
                    new_qty = current_qty - order_qty
                    if new_qty == 0:
                        del st.session_state.portfolio[symbol]
                    else:
                        avg_p = current_holding.get("avg_price", current_price) if isinstance(current_holding, dict) else current_price
                        st.session_state.portfolio[symbol] = {"qty": new_qty, "avg_price": avg_p}

                    st.session_state.trade_history.append({
                        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "SELL",
                        "symbol": symbol,
                        "qty": order_qty,
                        "price": current_price,
                        "fee": est_fee,
                        "total": total_sell_proceeds
                    })
                    save_user_data_to_db()
                    st.success(f"{symbol} {order_qty}주 매도 완료! (수수료 ${est_fee:,.2f} 공제 후 입금)")
                    st.rerun()
                else:
                    st.error("보유 수량이 부족합니다.")

        with c2:
            st.markdown("### 💼 현재 보유 포트폴리오")
            if st.session_state.portfolio:
                pf_data = []
                for sym, item in st.session_state.portfolio.items():
                    qty = item.get("qty", 0) if isinstance(item, dict) else item
                    avg_p = item.get("avg_price", 0.0) if isinstance(item, dict) else 0.0
                    pf_data.append({
                        "종목": sym, 
                        "보유 수량": f"{qty:,} 주",
                        "매수 평단가": f"${avg_p:,.2f}" if avg_p > 0 else "-"
                    })
                st.dataframe(pd.DataFrame(pf_data), use_container_width=True)
            else:
                st.info("현재 보유 중인 주식이 없습니다.")

            st.markdown("### 📜 최근 거래 내역")
            if st.session_state.trade_history:
                st.dataframe(pd.DataFrame(st.session_state.trade_history).iloc[::-1], use_container_width=True)
            else:
                st.info("거래 내역이 없습니다.")

# ------------------------------------------
# TAB 2: Portfolio Analyzer & S&P 500 Benchmark
# ------------------------------------------
with t2:
    st.subheader("포트폴리오 비중 분석 & 시장 벤치마크 비교")
    
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
            
            # 종목 및 시장 벤치마크(SPY) 동시 다운로드
            all_tickers = tickers_list + ["SPY"]
            raw_multi = yf.download(all_tickers, start=start_date, end=end_date)
            
            if isinstance(raw_multi, pd.DataFrame) and not raw_multi.empty:
                df_multi = raw_multi['Close'] if 'Close' in raw_multi.columns else raw_multi
                if isinstance(df_multi.columns, pd.MultiIndex):
                    df_multi.columns = df_multi.columns.get_level_values(0)

                st.markdown("### 💵 종목별 추천 매수 예산 배정")
                allocation_data = []
                for i, t_name in enumerate(tickers_list):
                    allocated_money = total_budget * norm_weights[i]
                    last_price = float(df_multi[t_name].dropna().iloc[-1]) if t_name in df_multi.columns and not df_multi[t_name].dropna().empty else 0.0
                    estimated_shares = int(allocated_money // last_price) if last_price > 0 else 0
                    
                    allocation_data.append({
                        "종목": t_name,
                        "설정 비중": f"{norm_weights[i]*100:.1f}%",
                        "현재가": f"${last_price:,.2f}",
                        "배정 금액": f"${allocated_money:,.2f}",
                        "매수 수량": f"{estimated_shares:,} 주"
                    })
                st.dataframe(pd.DataFrame(allocation_data), use_container_width=True)

                # 포트폴리오 vs S&P 500(SPY) 수익률 비교
                df_returns = df_multi[tickers_list].pct_change().dropna()
                portfolio_return = (df_returns * norm_weights).sum(axis=1)
                cum_portfolio = (1 + portfolio_return).cumprod()

                fig_pf = go.Figure()
                fig_pf.add_trace(go.Scatter(x=cum_portfolio.index, y=cum_portfolio.values, mode='lines', name='내 포트폴리오', line=dict(color='#2962FF', width=2.5)))
                
                if "SPY" in df_multi.columns:
                    spy_return = df_multi["SPY"].pct_change().dropna()
                    cum_spy = (1 + spy_return).cumprod()
                    fig_pf.add_trace(go.Scatter(x=cum_spy.index, y=cum_spy.values, mode='lines', name='시장 벤치마크 (S&P 500 - SPY)', line=dict(color='gray', dash='dash')))

                fig_pf.update_layout(title="포트폴리오 vs S&P 500 1년 성과 백테스트", xaxis_title="날짜", yaxis_title="배수 (1.0 = 원금)", height=450)
                st.plotly_chart(fig_pf, use_container_width=True)

                st.subheader("종목 간 상관관계 히트맵")
                corr = df_returns.corr()
                fig_corr = go.Figure(data=go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, colorscale='Viridis'))
                fig_corr.update_layout(height=380)
                st.plotly_chart(fig_corr, use_container_width=True)
    else:
        st.warning("포트폴리오 분석을 위해 최소 2개 이상의 종목을 입력해 주세요.")

# ------------------------------------------
# TAB 3: Technical Chart
# ------------------------------------------
with t3:
    st.subheader(f"{symbol} 볼린저 밴드 및 거래량 차트")
    if df_stock is not None and not df_stock.empty:
        df_tc = df_stock.copy()
        df_tc['MA20'] = df_tc['Close'].rolling(window=20).mean()
        df_tc['MA60'] = df_tc['Close'].rolling(window=60).mean()
        df_tc['STD20'] = df_tc['Close'].rolling(window=20).std()
        df_tc['Upper'] = df_tc['MA20'] + (df_tc['STD20'] * 2)
        df_tc['Lower'] = df_tc['MA20'] - (df_tc['STD20'] * 2)

        fig_tech = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        fig_tech.add_trace(go.Candlestick(x=df_tc.index, open=df_tc['Open'], high=df_tc['High'], low=df_tc['Low'], close=df_tc['Close'], name='주가'), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['MA20'], mode='lines', name='MA 20 (단기)', line=dict(color='orange')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['MA60'], mode='lines', name='MA 60 (중기)', line=dict(color='blue')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['Upper'], mode='lines', name='볼린저 상한', line=dict(color='gray', dash='dash')), row=1, col=1)
        fig_tech.add_trace(go.Scatter(x=df_tc.index, y=df_tc['Lower'], mode='lines', name='볼린저 하한', line=dict(color='gray', dash='dash')), row=1, col=1)

        fig_tech.add_trace(go.Bar(x=df_tc.index, y=df_tc['Volume'], name='거래량', marker_color='#26A69A'), row=2, col=1)
        fig_tech.update_layout(xaxis_rangeslider_visible=False, height=580)
        st.plotly_chart(fig_tech, use_container_width=True)

# ------------------------------------------
# TAB 4: Quant Strategy Signals (MA + RSI 복합 시그널)
# ------------------------------------------
with t4:
    st.subheader("⚡ 퀀트 듀얼 전략 시그널 (이동평균 크로스 + RSI 모멘텀)")
    
    st.markdown("""
    <div class="disclaimer-box">
        ⚠️ <b>학습 및 모의투자 면책 공지</b><br>
        본 전략 시그널은 과거 통계 지표(MA20/60 교차 및 14일 RSI 과매수·과매도)를 기반으로 자동 산출되는 가상 참고 데이터입니다. 특정 종목의 매매 권유나 미래 수익을 보장하지 않으며, 투자에 대한 모든 책임은 사용자 본인에게 있습니다.
    </div>
    """, unsafe_allow_html=True)

    if df_stock is not None and not df_stock.empty:
        df_sig = df_stock.copy()
        
        # 1) 이동평균
        df_sig['MA20'] = df_sig['Close'].rolling(window=20).mean()
        df_sig['MA60'] = df_sig['Close'].rolling(window=60).mean()
        
        # 2) RSI (14일)
        delta = df_sig['Close'].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        df_sig['RSI'] = 100 - (100 / (1 + rs))

        # 복합 시그널: 골든크로스 + RSI < 70 (과열되지 않은 상태의 돌파)
        buy_signals = (df_sig['MA20'] > df_sig['MA60']) & (df_sig['MA20'].shift(1) <= df_sig['MA60'].shift(1)) & (df_sig['RSI'] < 70)
        # 데드크로스 + RSI > 30 (투매가 아닌 상태의 이탈)
        sell_signals = (df_sig['MA20'] < df_sig['MA60']) & (df_sig['MA20'].shift(1) >= df_sig['MA60'].shift(1))

        current_rsi = float(df_sig['RSI'].dropna().iloc[-1]) if not df_sig['RSI'].dropna().empty else 50.0
        rsi_status = "과매수 (과열)" if current_rsi >= 70 else ("과매도 (반등 관심)" if current_rsi <= 30 else "중립 구간")

        sc1, sc2 = st.columns(2)
        sc1.metric(f"{symbol} 현재 RSI (14일)", f"{current_rsi:.1f}", rsi_status)
        ma_cross_status = "단기 상승 추세 (MA20 > MA60)" if df_sig['MA20'].iloc[-1] > df_sig['MA60'].iloc[-1] else "단기 하락 추세 (MA20 < MA60)"
        sc2.metric("이동평균 추세", ma_cross_status)

        fig_sig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.7, 0.3])
        fig_sig.add_trace(go.Scatter(x=df_sig.index, y=df_sig['Close'], mode='lines', name='종가', line=dict(color='gray')), row=1, col=1)
        fig_sig.add_trace(go.Scatter(x=df_sig.index, y=df_sig['MA20'], mode='lines', name='MA20', line=dict(color='orange')), row=1, col=1)
        fig_sig.add_trace(go.Scatter(x=df_sig.index, y=df_sig['MA60'], mode='lines', name='MA60', line=dict(color='blue')), row=1, col=1)

        fig_sig.add_trace(go.Scatter(
            x=df_sig[buy_signals].index, y=df_sig[buy_signals]['Close'],
            mode='markers', name='▲ 퀀트 매수 시그널',
            marker=dict(symbol='triangle-up', size=13, color='#089981')
        ), row=1, col=1)
        fig_sig.add_trace(go.Scatter(
            x=df_sig[sell_signals].index, y=df_sig[sell_signals]['Close'],
            mode='markers', name='▼ 퀀트 매도 시그널',
            marker=dict(symbol='triangle-down', size=13, color='#F23645')
        ), row=1, col=1)

        # 하단 RSI 지표 차트
        fig_sig.add_trace(go.Scatter(x=df_sig.index, y=df_sig['RSI'], mode='lines', name='RSI(14)', line=dict(color='#AB47BC')), row=2, col=1)
        fig_sig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig_sig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
        fig_sig.update_layout(height=560, title=f"{symbol} 퀀트 전략 백테스트 시그널")
        st.plotly_chart(fig_sig, use_container_width=True)

# ------------------------------------------
# TAB 5: Quant Risk Analysis
# ------------------------------------------
with t5:
    st.subheader("퀀트 리스크 & 투자 지표 분석")
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
        fig_dd.add_trace(go.Scatter(x=dd.index, y=dd * 100, mode='lines', name='Drawdown (%)', fill='tozeroy', line=dict(color='#F23645')))
        fig_dd.update_layout(title="Drawdown (낙폭) 위험 분석 차트", yaxis_title="낙폭 (%)", height=350)
        st.plotly_chart(fig_dd, use_container_width=True)

# ------------------------------------------
# TAB 6: Monte Carlo (Pro)
# ------------------------------------------
with t6:
    st.subheader("🔮 몬테카를로 시뮬레이션 (Pro 전용)")
    if st.session_state.user_tier != "Pro":
        st.warning("⚠️ 몬테카를로 시뮬레이션 기능은 **Pro 요금제** 전용 기능입니다.")
        st.info("왼쪽 사이드바의 '서비스 모드 전환'에서 **Pro** 선택 시 즉시 무료로 테스트해 보실 수 있습니다.")
    else:
        if df_stock is not None and not df_stock.empty:
            st.success("Pro 회원 인증 완료: 향후 252 거래일(1년) 주가 시나리오 200회를 시뮬레이션합니다.")
            returns = df_stock['Close'].pct_change().dropna()
            mu = returns.mean()
            sigma = returns.std()
            last_price = float(df_stock['Close'].iloc[-1])

            days = 252
            sims = 200
            
            daily_returns = np.exp((mu - 0.5 * sigma**2) + sigma * np.random.normal(size=(days, sims)))
            price_paths = np.zeros((days + 1, sims))
            price_paths[0] = last_price
            for d in range(days):
                price_paths[d + 1] = price_paths[d] * daily_returns[d]

            final_prices = price_paths[-1]
            p10 = np.percentile(final_prices, 10)
            p50 = np.percentile(final_prices, 50)
            p90 = np.percentile(final_prices, 90)

            c_mc1, c_mc2, c_mc3 = st.columns(3)
            c_mc1.metric("하위 10% 비관 시나리오", f"${p10:,.2f}")
            c_mc2.metric("중간값 (50% 기대값)", f"${p50:,.2f}")
            c_mc3.metric("상위 10% 낙관 시나리오", f"${p90:,.2f}")

            fig_mc = go.Figure()
            for col in range(min(50, sims)):
                fig_mc.add_trace(go.Scatter(y=price_paths[:, col], mode='lines', line=dict(width=1), showlegend=False))
            fig_mc.update_layout(title=f"{symbol} 1년 후 주가 시뮬레이션 (상위 50개 패스 시각화)", xaxis_title="거래일수", yaxis_title="예측 주가 ($)", height=450)
            st.plotly_chart(fig_mc, use_container_width=True)
