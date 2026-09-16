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
    
    /* 타이틀 스타일 */
    .sidebar-title { font-size: 1.5rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .sidebar-subtitle { font-size: 0.8rem; color: #94A3B8; margin-bottom: 15px; }
    .main-title { font-size: 2.2rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .main-subtitle { font-size: 1rem; color: #94A3B8; margin-bottom: 20px; }
    
    .badge-free { background-color: #334155; color: #94A3B8; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-lite { background-color: #0284C7; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .badge-pro { background: linear-gradient(135deg, #6366F1 0%, #A855F7 100%); color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .guide-box { background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 12px 16px; border-radius: 6px; font-size: 0.9rem; color: #CBD5E1; margin-bottom: 15px; }
    
    /* 업그레이드 카드 스타일 */
    .upgrade-card {
        background: linear-gradient(135deg, #1E1B4B 0%, #0F172A 100%);
        border: 1px solid #6366F1;
        border-radius: 12px;
        padding: 16px;
        margin-top: 15px;
        margin-bottom: 15px;
    }
    .upgrade-title { font-size: 1rem; font-weight: 700; color: #F43F5E; margin-bottom: 6px; }
    .upgrade-desc { font-size: 0.8rem; color: #94A3B8; margin-bottom: 10px; line-height: 1.4; }
    .version-tag { font-size: 0.75rem; color: #64748B; text-align: center; margin-top: 20px; }
    </style>
""", unsafe_allow_html=True)

# 2. 다국어 사전
LANG_DICT = {
    "한국어": {
        "title": "StockLab", "subtitle": "주식 모의투자 & AI 시뮬레이터",
        "tab_sim": "모의투자 & 자산", "tab_calc": "포트폴리오 분석기",
        "tab_tech": "기술적 분석 차트", "tab_risk": "퀀트 & 리스크 분석", "tab_predict": "몬테카를로 AI 예측",
        "buy_btn": "매수하기", "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab", "subtitle": "Paper Trading & AI Simulator",
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

APP_VERSION = "v1.5.0 Pro"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, period="1y"):
    try:
        df = yf.Ticker(ticker).history(period=period)
        return df if not df.empty else None
    except Exception:
        return None

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
if 'user_plan' not in st.session_state: st.session_state['user_plan'] = "Free"

# ====================================================
# 사이드바 (최상단 제목 포함)
# ====================================================
st.sidebar.markdown('<h2 class="sidebar-title">StockLab</h2>', unsafe_allow_html=True)
st.sidebar.markdown('<p class="sidebar-subtitle">주식 모의투자 & AI 시뮬레이터</p>', unsafe_allow_html=True)
st.sidebar.markdown("---")

selected_lang = st.sidebar.selectbox("Language", ["한국어", "English"], index=0)
L = LANG_DICT.get(selected_lang, LANG_DICT["한국어"])

current_plan = st.session_state['user_plan']
st.sidebar.markdown("##### 나의 멤버십 현황")

plan_col1, plan_col2 = st.sidebar.columns([2, 1])
with plan_col1:
    if current_plan == "Free": st.markdown('<span class="badge-free">Free 모드</span>', unsafe_allow_html=True)
    elif current_plan == "Lite": st.markdown('<span class="badge-lite">⚡ Lite 모드</span>', unsafe_allow_html=True)
    else: st.markdown('<span class="badge-pro">👑 Pro 모드</span>', unsafe_allow_html=True)

with plan_col2:
    new_plan = st.selectbox("플랜(테스트)", ["Free", "Lite", "Pro"], index=["Free", "Lite", "Pro"].index(current_plan), label_visibility="collapsed")
    if new_plan != current_plan:
        st.session_state['user_plan'] = new_plan
        st.rerun()

# 멤버십 업그레이드 안내
if current_plan == "Free":
    st.sidebar.markdown("""
        <div class="upgrade-card">
            <div class="upgrade-title">멤버십 업그레이드</div>
            <div class="upgrade-desc">
                • <b>Lite</b>: 복수 종목 분할 시뮬레이션 (3천회)<br>
                • <b>Pro</b>: 1만 회 시뮬레이션 + 백테스트 & 리밸런싱
            </div>
        </div>
    """, unsafe_allow_html=True)
    if st.sidebar.button("Lite / Pro 구매하기", use_container_width=True, type="primary"):
        st.toast("결제 페이지로 이동합니다. (테스트용 기능)")

# 서비스 버전 정보
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div class="version-tag">StockLab Version: <b>{APP_VERSION}</b></div>', unsafe_allow_html=True)

# ====================================================
# 메인 화면 영역 (최상단 타이틀 배치)
# ====================================================
st.markdown(f'<h1 class="main-title">{L["title"]}</h1>', unsafe_allow_html=True)
st.markdown(f'<p class="main-subtitle">{L["subtitle"]}</p>', unsafe_allow_html=True)

st.markdown("### 기준 종목 선택")
col_s1, col_s2 = st.columns([2, 3])
with col_s1:
    quick_choice = st.selectbox("인기 추천 종목 퀵 선택", ["선택 안함"] + list(POPULAR_STOCKS.keys()))
    if quick_choice != "선택 안함": st.session_state['search_ticker'] = POPULAR_STOCKS[quick_choice]

with col_s2:
    input_ticker = st.text_input("직접 티커 입력 (예: AAPL, TSLA, 005930.KS)", value=st.session_state['search_ticker'])
    if input_ticker: st.session_state['search_ticker'] = input_ticker.strip().upper()

current_ticker = st.session_state['search_ticker']
df_current = fetch_stock_data(current_ticker, period="1y")

# 메인 탭 5개 (이모지 제거)
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    L['tab_sim'], 
    L['tab_calc'], 
    L['tab_tech'], 
    L['tab_risk'], 
    L['tab_predict']
])

# ----------------------------------------------------
# TAB 1: 모의투자 & 보유 자산
# ----------------------------------------------------
with tab1:
    st.markdown('<div class="guide-box"><b>가상 모의투자</b>: 현재 선택한 종목을 매수/매도하며 자산을 운용해보세요.</div>', unsafe_allow_html=True)
    
    if df_current is not None:
        latest_price = df_current['Close'].iloc[-1]
        
        c1, c2, c3 = st.columns(3)
        c1.metric("보유 현금 잔고", f"₩{st.session_state['cash']:,.0f}")
        c2.metric(f"{current_ticker} 현재가", f"${latest_price:,.2f}" if not current_ticker.endswith(".KS") else f"₩{latest_price:,.0f}")
        
        held_qty = st.session_state['portfolio'].get(current_ticker, {}).get('qty', 0)
        c3.metric(f"{current_ticker} 보유 수량", f"{held_qty:,} 주")
        
        st.markdown("---")
        st.markdown("##### 매수 및 매도 주문")
        trade_col1, trade_col2 = st.columns(2)
        
        with trade_col1:
            buy_qty = st.number_input("매수 수량", min_value=1, value=10, key="buy_q")
            if st.button(L['buy_btn'], use_container_width=True, type="primary"):
                total_cost = buy_qty * latest_price
                if st.session_state['cash'] >= total_cost:
                    st.session_state['cash'] -= total_cost
                    prev_qty = st.session_state['portfolio'].get(current_ticker, {}).get('qty', 0)
                    st.session_state['portfolio'][current_ticker] = {'qty': prev_qty + buy_qty, 'avg_price': latest_price}
                    st.success(f"{current_ticker} {buy_qty}주 매수 완료!")
                    st.rerun()
                else:
                    st.error("잔고가 부족합니다.")

        with trade_col2:
            sell_qty = st.number_input("매도 수량", min_value=1, value=10, key="sell_q")
            if st.button(L['sell_btn'], use_container_width=True):
                if held_qty >= sell_qty:
                    st.session_state['cash'] += sell_qty * latest_price
                    st.session_state['portfolio'][current_ticker]['qty'] -= sell_qty
                    if st.session_state['portfolio'][current_ticker]['qty'] == 0:
                        del st.session_state['portfolio'][current_ticker]
                    st.success(f"{current_ticker} {sell_qty}주 매도 완료!")
                    st.rerun()
                else:
                    st.error("보유 수량이 부족합니다.")
    else:
        st.error("종목 데이터를 불러올 수 없습니다.")

# ----------------------------------------------------
# TAB 2: 포트폴리오 분석기
# ----------------------------------------------------
with tab2:
    st.markdown('<div class="guide-box"><b>포트폴리오 통합 분석</b>: 선택한 종목들의 과거 백테스팅, 종목 간 상관관계, 리밸런싱 계산을 지원합니다.</div>', unsafe_allow_html=True)
    
    selected_port_tickers = st.multiselect(
        "분석할 포트폴리오 종목 선택", 
        list(POPULAR_STOCKS.values()) + ["GOOGL", "AMZN", "MSFT"],
        default=["AAPL", "NVDA", "SPY"]
    )
    
    if len(selected_port_tickers) >= 2:
        weights = {}
        st.markdown("##### 종목별 투자 비중 설정 (%)")
        cols = st.columns(len(selected_port_tickers))
        
        default_w = round(100.0 / len(selected_port_tickers), 2)
        
        for idx, t in enumerate(selected_port_tickers):
            with cols[idx]:
                weights[t] = st.number_input(f"{t} 비중", min_value=0.0, max_value=100.0, value=default_w, step=1.0, format="%.2f")
                
        tot_weight = round(sum(weights.values()), 2)
        
        if abs(tot_weight - 100.0) > 0.5:
            st.warning(f"비중 합계가 {tot_weight}%입니다. (합계 100%로 맞춰주세요)")
        else:
            st.success(f"비중 합계: {tot_weight}% (정상)")
            
            today = datetime.today()
            start_2y = today - timedelta(days=365*2)
            df_port = fetch_multi_ticker_data(selected_port_tickers, str(start_2y.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))
            
            if df_port is not None and not df_port.empty:
                daily_returns = df_port.pct_change().dropna()
                
                w_list = np.array([weights[t] for t in selected_port_tickers])
                w_list = w_list / np.sum(w_list)
                
                port_returns = (daily_returns * w_list).sum(axis=1)
                cum_returns = (1 + port_returns).cumprod()
                
                st.markdown("---")
                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["과거 성과 백테스트", "상관계수 히트맵", "리밸런싱 계산기"])
                
                with sub_tab1:
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
                    st.markdown("##### 종목 간 상관계수 (Correlation)")
                    corr_matrix = daily_returns.corr()
                    fig_corr = px.imshow(corr_matrix, text_auto=".2f", color_continuous_scale="Blues", aspect="auto")
                    fig_corr.update_layout(template="plotly_dark", height=350)
                    st.plotly_chart(fig_corr, use_container_width=True)

                with sub_tab3:
                    st.markdown("##### 목표 비중 맞춤 리밸런싱 주문 계산")
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
    else:
        st.info("포트폴리오 분석을 위해 최소 2개 이상의 종목을 선택해 주세요.")

# ----------------------------------------------------
# TAB 3: 기술적 분석 차트
# ----------------------------------------------------
with tab3:
    st.markdown('<div class="guide-box"><b>기술적 차트 분석</b>: 이동평균선(MA20, MA60) 및 거래량 지표를 제공합니다.</div>', unsafe_allow_html=True)
    
    if df_current is not None:
        df_current['MA20'] = df_current['Close'].rolling(window=20).mean()
        df_current['MA60'] = df_current['Close'].rolling(window=60).mean()
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
        
        fig.add_trace(go.Scatter(x=df_current.index, y=df_current['Close'], name='종가', line=dict(color='#38BDF8', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_current.index, y=df_current['MA20'], name='20일 이동평균', line=dict(color='#F59E0B', width=1.5)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_current.index, y=df_current['MA60'], name='60일 이동평균', line=dict(color='#EC4899', width=1.5)), row=1, col=1)
        
        fig.add_trace(go.Bar(x=df_current.index, y=df_current['Volume'], name='거래량', marker_color='#64748B'), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", height=500, title=f"{current_ticker} 주가 및 이동평균선 추이", showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("차트 데이터를 불러올 수 없습니다.")

# ----------------------------------------------------
# TAB 4: 퀀트 & 리스크 분석
# ----------------------------------------------------
with tab4:
    st.markdown('<div class="guide-box"><b>퀀트 리스크 분석</b>: Sharpe Ratio, 변동성, MDD 및 위험 평가 지표입니다.</div>', unsafe_allow_html=True)
    
    if df_current is not None:
        daily_ret = df_current['Close'].pct_change().dropna()
        
        annual_vol = daily_ret.std() * np.sqrt(252) * 100
        annual_return = daily_ret.mean() * 252 * 100
        sharpe_ratio = (annual_return - 3.5) / annual_vol if annual_vol != 0 else 0
        
        cum = (1 + daily_ret).cumprod()
        peak = cum.cummax()
        mdd = ((cum - peak) / peak).min() * 100
        var_95 = np.percentile(daily_ret, 5) * 100

        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        col_q1.metric("연화 변동성 (Risk)", f"{annual_vol:.2f}%")
        col_q2.metric("샤프 지수 (Sharpe)", f"{sharpe_ratio:.2f}")
        col_q3.metric("최대 낙폭 (MDD)", f"{mdd:.2f}%")
        col_q4.metric("일일 95% VaR", f"{var_95:.2f}%")

        st.markdown("---")
        st.markdown("##### 일일 수익률 분포 히스토그램")
        fig_hist = px.histogram(daily_ret, nbins=50, title="수익률 변동성 분포", labels={'value': '일일 수익률'})
        fig_hist.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig_hist, use_container_width=True)

# ----------------------------------------------------
# TAB 5: 몬테카를로 AI 예측
# ----------------------------------------------------
with tab5:
    st.markdown('<div class="guide-box"><b>몬테카를로 확률 예측</b>: 유료 플랜(Lite/Pro)에서는 복수 종목 분할 투자 시뮬레이션을 지원합니다.</div>', unsafe_allow_html=True)
    
    if current_plan == "Free":
        st.info("Free 플랜 사용 중: 단일 종목 시뮬레이션만 이용 가능합니다.")
        st.warning("Lite 및 Pro 멤버십으로 업그레이드하시면 여러 종목을 분할 투자한 포트폴리오 몬테카를로 시뮬레이션을 이용할 수 있습니다!")
        
        selected_mc_tickers = [current_ticker]
        mc_weights = {current_ticker: 100.0}
    else:
        st.success(f"{current_plan} 멤버십 혜택: 복수 종목 분할 투자 시뮬레이션 모드가 활성화되었습니다!")
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
            num_sims = 1000 if current_plan == "Free" else (3000 if current_plan == "Lite" else 10000)
            st.caption(f"시뮬레이션 횟수: {num_sims:,}회")
            
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
            sample_paths = asset_paths[:, :min(100, num_sims)]
            for i in range(sample_paths.shape[1]):
                fig_mc.add_trace(go.Scatter(y=sample_paths[:, i], mode='lines', line=dict(width=0.5, color='rgba(56, 189, 248, 0.1)'), showlegend=False))
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 90, axis=1), name="상위 10%", line=dict(color='#10B981', width=2)))
            fig_mc.add_trace(go.Scatter(y=np.median(asset_paths, axis=1), name="중앙값 (50%)", line=dict(color='#F59E0B', width=2.5)))
            fig_mc.add_trace(go.Scatter(y=np.percentile(asset_paths, 10, axis=1), name="하위 10%", line=dict(color='#EF4444', width=2)))
            fig_mc.update_layout(template="plotly_dark", height=380, xaxis=dict(title="경과 일수 (Day)"), yaxis=dict(title="예상 평가액 (₩)"))
            
            st.plotly_chart(fig_mc, use_container_width=True)
