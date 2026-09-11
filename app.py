import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="스톡랩 (StockLab) - 미국 주식 포트폴리오 실험실", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; }
    .main-header { font-size: 2.1rem; font-weight: 800; color: #38BDF8; margin-bottom: 0px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; }
    .version-tag {
        background-color: #1E293B; color: #38BDF8; padding: 4px 10px;
        border-radius: 6px; font-size: 0.85rem; font-weight: 700; border: 1px solid #334155;
    }
    .pro-badge {
        background: linear-gradient(135deg, #F59E0B, #D97706); color: white;
        padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-left: 8px;
    }
    .kpi-card {
        background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 12px 16px;
    }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; }
    .kpi-value { font-size: 1.4rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-pos { color: #10B981; } .kpi-neg { color: #EF4444; }
    </style>
""", unsafe_allow_html=True)

# 초보자를 위한 티커 <-> 한글 풀네임 매핑 사전
TICKER_NAMES = {
    "NVDA": "엔비디아", "AAPL": "애플", "MSFT": "마이크로소프트", "AVGO": "브로드컴",
    "AMD": "AMD", "TSM": "TSMC", "ASML": "ASML", "INTC": "인텔",
    "GOOGL": "알파벳(구글)", "META": "메타", "NFLX": "넷플릭스", "DIS": "디즈니",
    "TMUS": "T모바일", "VZ": "버라이즌", "AMZN": "아마존", "TSLA": "테슬라",
    "HD": "홈디포", "NKE": "나이키", "MCD": "맥도날드", "SBUX": "스타벅스",
    "PG": "P&G", "KO": "코카콜라", "PEP": "펩시코", "WMT": "월마트", "COST": "코스트코",
    "LLY": "일라이릴리", "UNH": "유나이티드헬스", "JNJ": "존슨앤존슨", "MRK": "머크",
    "ABBV": "애브비", "PFE": "화이자", "BRK-B": "버크셔해서웨이", "JPM": "JP모건",
    "V": "비자", "MA": "마스터카드", "BAC": "뱅크오브아메리카", "GS": "골드만삭스",
    "SPY": "S&P 500 ETF", "QQQ": "나스닥 100 ETF", "DIA": "다우존스 ETF", 
    "IWM": "러셀2000 ETF", "TLT": "미국 장기채 ETF", "SCHD": "슈드 배당 ETF"
}

def get_disp_name(ticker):
    return f"{TICKER_NAMES.get(ticker, ticker)} ({ticker})"

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

# Sidebar Setup
st.sidebar.markdown("### 📌 서비스 버전")
current_version = "1.0"
st.sidebar.selectbox("버전 선택", ["1.0 (상용 버전)"], index=0)

st.sidebar.markdown("### 👑 계정 요금제")
dev_pro = st.sidebar.toggle("🔑 개발자 Pro 권한 사용", value=True)
is_pro = dev_pro

st.sidebar.markdown("---")

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown('<p class="main-header">🧪 스톡랩 (StockLab)</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">초보자도 3초 만에 끝내는 미국 주식 시뮬레이터</p>', unsafe_allow_html=True)
with col_h2:
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">v{current_version}</span></div>', unsafe_allow_html=True)

# Sector Database
SECTOR_DATABASE = {
    "🇺🇸 IT & 반도체": ["NVDA", "AAPL", "MSFT", "AVGO", "AMD", "TSM"],
    "🌐 인터넷 & 미디어": ["GOOGL", "META", "NFLX", "DIS"],
    "🛍️ 쇼핑 & 전기차": ["AMZN", "TSLA", "NKE", "SBUX"],
    "🛒 일상 생활용품": ["KO", "PEP", "WMT", "COST"],
    "🏦 은행 & 대표 ETF": ["BRK-B", "JPM", "SPY", "QQQ"]
}

st.sidebar.markdown("### 🗂️ 1. 투자 분야 선택")
selected_sector = st.sidebar.radio("분야", list(SECTOR_DATABASE.keys()), index=0, label_visibility="collapsed")
default_pool = SECTOR_DATABASE[selected_sector]

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 2. 포함할 종목 선택")
selected_tickers = []
for ticker in default_pool:
    disp = get_disp_name(ticker)
    if st.sidebar.checkbox(f"✅ {disp}", value=(ticker in default_pool[:3]), key=f"chk_v14_{ticker}"):
        selected_tickers.append(ticker)

st.sidebar.markdown("---")
today = datetime.today()
start_date = today - timedelta(days=365)
analysis_tickers = list(set(selected_tickers + ["SPY"]))

if selected_tickers:
    with st.spinner('실시간 데이터 불러오는 중...'):
        data = fetch_stock_data(tuple(sorted(analysis_tickers)), str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

    valid_tickers = [t for t in selected_tickers if t in data.columns and not data[t].dropna().empty]

    if valid_tickers:
        valid_data = data[valid_tickers].dropna()
        spy_data = data['SPY'].dropna() if 'SPY' in data.columns else None

        # Real-time Stock Cards
        st.markdown("##### 📌 선택한 종목 현재가")
        metric_cols = st.columns(min(len(valid_tickers), 4))
        for idx, ticker in enumerate(valid_tickers):
            col_target = metric_cols[idx % 4]
            series = valid_data[ticker]
            if len(series) >= 2:
                curr_p = series.iloc[-1]
                prev_p = series.iloc[-2]
                chg = ((curr_p - prev_p) / prev_p) * 100
                cls_style = "kpi-pos" if chg >= 0 else "kpi-neg"
                sign = "+" if chg >= 0 else ""
                
                col_target.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">{get_disp_name(ticker)}</div>
                    <div class="kpi-value">${curr_p:.2f}</div>
                    <div class="kpi-sub {cls_style}">{sign}{chg:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 종목별 수익률 비교", 
            "🎯 포트폴리오 수익률 계산기", 
            "🔮 내 예산으로 1년 후 자산 예측 (몬테카를로) 👑",
            "🔍 종목 상세 지표"
        ])

        # TAB 1: Toss Style Smooth Plotly Chart
        with tab1:
            st.markdown("### 📈 토스 스타일 유동적 성과 비교 그래프")
            st.caption("그래프에 마우스를 올리면 날짜별 상세 금액이 부드럽게 표시됩니다.")
            
            norm_df = (valid_data / valid_data.iloc[0]) * 100
            
            fig = go.Figure()
            for t in valid_tickers:
                fig.add_trace(go.Scatter(
                    x=norm_df.index, y=norm_df[t],
                    mode='lines', name=get_disp_name(t),
                    hovertemplate="%{x|%Y-%m-%d}<br><b>" + get_disp_name(t) + "</b>: %{y:.1f}pt"
                ))
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                margin=dict(l=10, r=10, t=10, b=10),
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # TAB 2
        with tab2:
            st.markdown("### 🎯 내 맘대로 투자 비중 조절")
            with st.form("portfolio_form_v14"):
                weights = []
                slider_cols = st.columns(min(len(valid_tickers), 4))
                for i, ticker in enumerate(valid_tickers):
                    with slider_cols[i % 4]:
                        default_w = int(100 / len(valid_tickers))
                        val = st.number_input(f"{TICKER_NAMES.get(ticker, ticker)} (%)", 0, 100, default_w, step=1)
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

                fig_port = go.Figure()
                fig_port.add_trace(go.Scatter(x=port_cum_ret.index, y=port_cum_ret, mode='lines', name='내 포트폴리오', line=dict(color='#38BDF8', width=3)))
                fig_port.add_trace(go.Scatter(x=spy_cum_ret.index, y=spy_cum_ret, mode='lines', name='S&P 500 시장평균', line=dict(color='#94A3B8', dash='dash')))
                fig_port.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", hovermode="x unified", height=380)
                st.plotly_chart(fig_port, use_container_width=True)

                st.session_state['summary_data'] = {
                    'valid_tickers': valid_tickers,
                    'weights': weights,
                    'port_daily_ret': port_daily_ret
                }

        # TAB 3: Custom Budget Monte Carlo Simulation
        with tab3:
            st.markdown("### 🔮 내 실제 예산 기반 1년 후 자산 예측 시뮬레이션 <span class='pro-badge'>PRO</span>", unsafe_allow_html=True)
            
            sum_data = st.session_state.get('summary_data', None)
            if sum_data:
                col_mc1, col_mc2 = st.columns([2, 1])
                with col_mc1:
                    user_budget = st.number_input("💵 총 투자할 예산을 입력하세요 ($ 달러 기준)", min_value=100, max_value=10000000, value=10000, step=500)
                with col_mc2:
                    sim_runs = st.selectbox("시뮬레이션 횟수", [1000, 5000, 10000], index=0)

                port_daily_ret = sum_data['port_daily_ret']
                T = 252 
                sim_results = np.zeros((T, sim_runs))
                sim_results[0] = user_budget

                np.random.seed(42) 
                mean_d = port_daily_ret.mean()
                std_d = port_daily_ret.std()

                for t in range(1, T):
                    rand_shocks = np.random.normal(mean_d, std_d, sim_runs)
                    sim_results[t] = sim_results[t-1] * (1 + rand_shocks)

                # Smooth Plotly Monte Carlo Simulation Chart
                fig_mc = go.Figure()
                for i in range(min(sim_runs, 40)): # 40개 대표 경로 렌더링
                    fig_mc.add_trace(go.Scatter(y=sim_results[:, i], mode='lines', line=dict(width=1), opacity=0.3, showlegend=False))
                
                fig_mc.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380, title=f"${user_budget:,.0f} 투자 시 1년 후 예상 경로 시나리오")
                st.plotly_chart(fig_mc, use_container_width=True)

                p5 = np.percentile(sim_results[-1], 5)
                p50 = np.percentile(sim_results[-1], 50)
                p95 = np.percentile(sim_results[-1], 95)

                st.markdown(f"#### 📊 1년 후 예상 자산 결과 (초기 예산: **${user_budget:,.0f}**)")
                m1, m2, m3 = st.columns(3)
                m1.metric("최악의 하위 5% 시나리오", f"${p5:,.0f}", delta=f"{((p5-user_budget)/user_budget)*100:.1f}%")
                m2.metric("중간 평균 50% 시나리오", f"${p50:,.0f}", delta=f"{((p50-user_budget)/user_budget)*100:.1f}%")
                m3.metric("최선의 상위 5% 시나리오", f"${p95:,.0f}", delta=f"{((p95-user_budget)/user_budget)*100:.1f}%")
            else:
                st.warning("탭 2에서 비중을 설정하고 [🚀 계산 반영하기]를 먼저 눌러주세요.")

        # TAB 4
        with tab4:
            st.markdown("### 🔍 종목 상세 분석")
            selected_ticker = st.selectbox("종목 선택", options=valid_tickers, format_func=get_disp_name, index=0)
            stock_series = valid_data[selected_ticker]
            
            fig_detail = go.Figure()
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series, mode='lines', name='주가', line=dict(color='#38BDF8')))
            fig_detail.add_trace(go.Scatter(x=stock_series.index, y=stock_series.rolling(50).mean(), mode='lines', name='50일 이동평균선'))
            fig_detail.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=380)
            st.plotly_chart(fig_detail, use_container_width=True)

        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🤝 서비스 문의")
        st.sidebar.code("aseui995@gmail.com", language="text")
