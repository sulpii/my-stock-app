import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# 1. Page Configuration
st.set_page_config(
    page_title="스톡랩 (StockLab)", 
    page_icon="🧪", 
    layout="wide"
)

# Custom CSS (모던 핀테크 다크 스타일)
st.markdown("""
    <style>
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

# 2. 다국어 사전 정의
LANG_DICT = {
    "한국어": {
        "title": "StockLab",
        "subtitle": "주식 초보를 위한 모의투자 & 시뮬레이션 플랫폼",
        "market_select": "시장 선택",
        "currency_select": "표시 통화",
        "ver_select": "서비스 모드",
        "tab_sim": "모의투자 및 보유자산",
        "tab_calc": "포트폴리오 계산기",
        "tab_tech": "기술적 분석 & 뉴스",
        "tab_risk": "퀀트 & 리스크 분석",
        "tab_pro": "프로 진단 보고서",
        "buy_btn": "매수하기",
        "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab",
        "subtitle": "Paper Trading & Simulation Platform for Beginners",
        "market_select": "Market",
        "currency_select": "Currency",
        "ver_select": "Mode",
        "tab_sim": "Paper Trading & Holdings",
        "tab_calc": "Portfolio Calculator",
        "tab_tech": "Technical Analysis & News",
        "tab_risk": "Quant & Risk Analysis",
        "tab_pro": "Pro Report",
        "buy_btn": "Buy",
        "sell_btn": "Sell"
    },
    "日本語": {
        "title": "StockLab",
        "subtitle": "初心者のための模擬投資＆シミュレーションプラットフォーム",
        "market_select": "市場選択",
        "currency_select": "表示通貨",
        "ver_select": "モード選択",
        "tab_sim": "模擬投資＆保有資産",
        "tab_calc": "ポートフォリオ計算機",
        "tab_tech": "テクニカル分析＆ニュース",
        "tab_risk": "クオンツ＆リスク分析",
        "tab_pro": "Pro 診断レポート",
        "buy_btn": "買い",
        "sell_btn": "売り"
    },
    "中文": {
        "title": "StockLab",
        "subtitle": "面向初学者的模拟交易与分析平台",
        "market_select": "选择市场",
        "currency_select": "显示货币",
        "ver_select": "模式选择",
        "tab_sim": "模拟交易与持仓",
        "tab_calc": "组合计算器",
        "tab_tech": "技术分析与新闻",
        "tab_risk": "量化与风险分析",
        "tab_pro": "Pro 诊断报告",
        "buy_btn": "买入",
        "sell_btn": "卖出"
    }
}

STOCKS = {
    "미국 주식 (US Market)": {
        "Apple": "AAPL", "NVIDIA": "NVDA", "Microsoft": "MSFT", 
        "Amazon": "AMZN", "Tesla": "TSLA", "S&P 500 ETF": "SPY"
    },
    "국내 주식 (KR Market)": {
        "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NAVER": "035420.KS", 
        "카카오": "035720.KS", "현대차": "005380.KS", "KODEX 200": "069500.KS"
    }
}

KR_TRANSLATIONS = {
    "English": {"삼성전자": "Samsung Electronics", "SK하이닉스": "SK Hynix", "NAVER": "NAVER", "카카오": "Kakao", "현대차": "Hyundai Motor", "KODEX 200": "KODEX 200"},
    "日本語": {"삼성전자": "サムスン電子", "SKハイニックス": "SKハイニックス", "NAVER": "NAVER", "카카오": "カカオ", "현대차": "現代自動車", "KODEX 200": "KODEX 200"},
    "中文": {"삼성전자": "三星电子", "SK하이닉스": "SK海力士", "NAVER": "NAVER", "카카오": "Kakao", "현대차": "现代汽车", "KODEX 200": "KODEX 200"}
}

@st.cache_data(ttl=3600, show_spinner=False)
def get_exchange_rates():
    try:
        krw = yf.Ticker("KRW=X").history(period="1d")['Close'].iloc[-1]
        jpy = yf.Ticker("JPY=X").history(period="1d")['Close'].iloc[-1]
        return {"USD": (1.0, "$"), "KRW": (krw, "₩"), "JPY": (jpy, "¥")}
    except Exception:
        return {"USD": (1.0, "$"), "KRW": (1350.0, "₩"), "JPY": (150.0, "¥")}

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(tickers, start, end):
    try:
        raw = yf.download(list(tickers), start=start, end=end, progress=False)
        data = raw['Close'] if 'Close' in raw else raw
        if isinstance(data, pd.Series):
            data = data.to_frame()
        return data.dropna(how='all', axis=1)
    except Exception:
        return pd.DataFrame()

# 세션 초기화
if 'cash' not in st.session_state:
    st.session_state['cash'] = 10000000.0
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {}

# 사이드바 설정
st.sidebar.markdown("### Settings")
selected_lang = st.sidebar.selectbox("Language", ["한국어", "English", "日本語", "中文"], index=0)
L = LANG_DICT[selected_lang]

rates = get_exchange_rates()
curr_choice = st.sidebar.selectbox(L['currency_select'], ["KRW (₩)", "USD ($)", "JPY (¥)"], index=0)
curr_key = curr_choice.split(" ")[0]
fx_rate, curr_symbol = rates[curr_key]

st.sidebar.markdown("---")
market_choice = st.sidebar.radio(L['market_select'], ["미국 주식 (US Market)", "국내 주식 (KR Market)", "통합 (All Market)"])

st.sidebar.markdown("---")
mode_choice = st.sidebar.selectbox(L['ver_select'], ["Free (기본 모드)", "Pro (전문가 모드)"], index=1)
is_pro = "Pro" in mode_choice

# Pro 모드 픽토그램/아이콘 헬퍼 함수
def p_icon(icon_str):
    return f"{icon_str} " if is_pro else ""

# 종목 리스트 구성
if market_choice == "미국 주식 (US Market)":
    target_stocks = STOCKS["미국 주식 (US Market)"]
elif market_choice == "국내 주식 (KR Market)":
    target_stocks = STOCKS["국내 주식 (KR Market)"]
else:
    target_stocks = {**STOCKS["미국 주식 (US Market)"], **STOCKS["국내 주식 (KR Market)"]}

def get_disp_name(name, symbol):
    if symbol.endswith(".KS"):
        return KR_TRANSLATIONS.get(selected_lang, {}).get(name, name)
    return name

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f'<p class="main-header">{p_icon("🧪")}{L["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{L["subtitle"]}</p>', unsafe_allow_html=True)
with col_h2:
    if is_pro:
        st.markdown('<div style="text-align:right; margin-top:10px;"><span class="pro-tag">👑 Pro Version</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:right; margin-top:10px;"><span class="version-tag">Free Version</span></div>', unsafe_allow_html=True)

# 데이터 로딩
today = datetime.today()
start_date = today - timedelta(days=365)
tickers = list(target_stocks.values())

with st.spinner('Real-time Market Data Syncing...'):
    data = fetch_stock_data(tickers, str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

def update_chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380
    )

if not data.empty:
    valid_tickers = [t for t in tickers if t in data.columns and not data[t].dropna().empty]
    
    # 탭 이름에 Pro 모드에서만 픽토그램 추가
    tab_sim_title = f"{p_icon('💵')}{L['tab_sim']}"
    tab_calc_title = f"{p_icon('🧮')}{L['tab_calc']}"
    tab_tech_title = f"{p_icon('📈')}{L['tab_tech']}"
    tab_risk_title = f"{p_icon('📊')}{L['tab_risk']}"
    tab_pro_title = f"{p_icon('👑')}{L['tab_pro']}"

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        tab_sim_title, tab_calc_title, tab_tech_title, tab_risk_title, tab_pro_title
    ])

    # ----------------------------------------------------
    # TAB 1: 모의투자 및 내 보유 자산
    # ----------------------------------------------------
    with tab1:
        guide_icon = p_icon('💡')
        st.markdown(f'<div class="guide-box">{guide_icon}<b>가상 모의투자</b>: 부담 없이 실시간 시세로 매수/매도하고, 내 잔고와 평가 손익을 실시간으로 확인해보세요.</div>', unsafe_allow_html=True)
        
        c_krw = rates["KRW"][0]
        disp_scale = (fx_rate / c_krw) if curr_key != "KRW" else 1.0
        
        eval_stock_val = 0.0
        portfolio_rows = []
        
        for t, holdings in st.session_state['portfolio'].items():
            qty = holdings['qty']
            if qty > 0 and t in data.columns:
                p_krw = data[t].iloc[-1] if t.endswith(".KS") else data[t].iloc[-1] * c_krw
                current_val = p_krw * qty
                eval_stock_val += current_val
                
                avg_p = holdings['avg_price']
                profit_krw = (p_krw - avg_p) * qty
                profit_rate = ((p_krw - avg_p) / avg_p) * 100 if avg_p > 0 else 0
                
                disp_name = [k for k, v in target_stocks.items() if v == t]
                name_str = get_disp_name(disp_name[0], t) if disp_name else t
                
                portfolio_rows.append({
                    "종목명": name_str,
                    "보유수량": f"{qty:,}주",
                    "평균단가": f"{curr_symbol}{avg_p * disp_scale:,.0f}",
                    "현재가": f"{curr_symbol}{p_krw * disp_scale:,.0f}",
                    "평가금액": f"{curr_symbol}{current_val * disp_scale:,.0f}",
                    "평가손익": f"{curr_symbol}{profit_krw * disp_scale:,.0f} ({profit_rate:+.2f}%)"
                })

        total_asset_krw = st.session_state['cash'] + eval_stock_val
        
        k1, k2, k3 = st.columns(3)
        k1.metric(f"{p_icon('💰')}총 보유 자산", f"{curr_symbol}{total_asset_krw * disp_scale:,.0f}")
        k2.metric(f"{p_icon('💳')}보유 현금", f"{curr_symbol}{st.session_state['cash'] * disp_scale:,.0f}")
        k3.metric(f"{p_icon('🏢')}주식 평가금액", f"{curr_symbol}{eval_stock_val * disp_scale:,.0f}")

        st.markdown("---")
        
        col_trade, col_hold = st.columns([1, 1])
        with col_trade:
            st.markdown(f"##### {p_icon('🛒')}주식 주문하기")
            selected_disp = st.selectbox("거래할 종목 선택", list(target_stocks.keys()), format_func=lambda x: get_disp_name(x, target_stocks[x]))
            sel_symbol = target_stocks[selected_disp]
            
            if sel_symbol in data.columns:
                p_krw = data[sel_symbol].iloc[-1] if sel_symbol.endswith(".KS") else data[sel_symbol].iloc[-1] * c_krw
                st.write(f"현재가: **{curr_symbol}{p_krw * disp_scale:,.0f}**")
                
                tb1, tb2 = st.columns(2)
                with tb1:
                    buy_qty = st.number_input("매수 수량", min_value=1, value=1, key="b_q")
                    if st.button(f"{p_icon('🟢')}{L['buy_btn']}", use_container_width=True):
                        cost = p_krw * buy_qty
                        if st.session_state['cash'] >= cost:
                            st.session_state['cash'] -= cost
                            old_info = st.session_state['portfolio'].get(sel_symbol, {'qty': 0, 'avg_price': 0})
                            new_qty = old_info['qty'] + buy_qty
                            new_avg = ((old_info['qty'] * old_info['avg_price']) + cost) / new_qty
                            st.session_state['portfolio'][sel_symbol] = {'qty': new_qty, 'avg_price': new_avg}
                            st.success(f"{buy_qty}주 매수 체결!")
                            st.rerun()
                        else:
                            st.error("현금이 부족합니다.")
                
                with tb2:
                    sell_qty = st.number_input("매도 수량", min_value=1, value=1, key="s_q")
                    if st.button(f"{p_icon('🔴')}{L['sell_btn']}", use_container_width=True):
                        old_info = st.session_state['portfolio'].get(sel_symbol, {'qty': 0, 'avg_price': 0})
                        if old_info['qty'] >= sell_qty:
                            st.session_state['cash'] += p_krw * sell_qty
                            old_info['qty'] -= sell_qty
                            st.session_state['portfolio'][sel_symbol] = old_info
                            st.success(f"{sell_qty}주 매도 체결!")
                            st.rerun()
                        else:
                            st.error("보유 수량이 부족합니다.")

        with col_hold:
            st.markdown(f"##### {p_icon('📋')}내 보유 종목 내역")
            if portfolio_rows:
                st.dataframe(pd.DataFrame(portfolio_rows), use_container_width=True, hide_index=True)
            else:
                st.info("현재 보유 중인 주식이 없습니다.")

    # ----------------------------------------------------
    # TAB 2: 포트폴리오 계산기
    # ----------------------------------------------------
    with tab2:
        st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>포트폴리오 리밸런싱 시뮬레이션</b>: 종목별 투자 비중을 조절하여 기대 수익률 및 자산 합산을 확인해보세요.</div>', unsafe_allow_html=True)
        
        calc_tickers = valid_tickers[:4]
        weights = []
        c_cols = st.columns(len(calc_tickers))
        for idx, t in enumerate(calc_tickers):
            name = [k for k, v in target_stocks.items() if v == t][0]
            with c_cols[idx]:
                w = st.slider(get_disp_name(name, t), 0, 100, int(100/len(calc_tickers)), step=5)
                weights.append(w)
        
        tot_w = sum(weights)
        if tot_w > 0:
            norm_w = np.array(weights) / tot_w
            daily_ret = data[calc_tickers].pct_change().dropna()
            port_ret = (daily_ret * norm_w).sum(axis=1)
            port_cum = (1 + port_ret).cumprod() * 100
            
            fig_calc = go.Figure()
            fig_calc.add_trace(go.Scatter(x=port_cum.index, y=port_cum, mode='lines', name='포트폴리오', line=dict(color='#38BDF8', width=3)))
            update_chart_layout(fig_calc)
            st.plotly_chart(fig_calc, use_container_width=True)
            
            st.session_state['port_res'] = {'tot_ret': port_cum.iloc[-1] - 100, 'daily_ret': port_ret}

    # ----------------------------------------------------
    # TAB 3: 상세 기술적 분석 & 뉴스
    # ----------------------------------------------------
    with tab3:
        st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>기술적 지표 & 차트 분석</b>: 주가의 이동평균선, RSI, 볼린저 밴드, MACD 지표를 차트로 정밀하게 분석합니다.</div>', unsafe_allow_html=True)
        
        sel_name = st.selectbox("분석할 종목 선택", list(target_stocks.keys()), format_func=lambda x: get_disp_name(x, target_stocks[x]), key="tech_sel")
        sel_t = target_stocks[sel_name]
        
        if sel_t in data.columns:
            df_t = pd.DataFrame(data[sel_t].dropna())
            df_t.columns = ['Close']
            
            df_t['MA20'] = df_t['Close'].rolling(20).mean()
            df_t['MA60'] = df_t['Close'].rolling(60).mean()
            
            delta = df_t['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df_t['RSI'] = 100 - (100 / (1 + rs))
            
            std = df_t['Close'].rolling(20).std()
            df_t['Upper'] = df_t['MA20'] + (std * 2)
            df_t['Lower'] = df_t['MA20'] - (std * 2)

            fig_tech = go.Figure()
            fig_tech.add_trace(go.Scatter(x=df_t.index, y=df_t['Close']*fx_rate, name="주가", line=dict(color='#38BDF8', width=2)))
            fig_tech.add_trace(go.Scatter(x=df_t.index, y=df_t['MA20']*fx_rate, name="20일 이평선", line=dict(color='#F59E0B')))
            fig_tech.add_trace(go.Scatter(x=df_t.index, y=df_t['Upper']*fx_rate, name="볼린저 상단", line=dict(color='#6366F1', dash='dot')))
            fig_tech.add_trace(go.Scatter(x=df_t.index, y=df_t['Lower']*fx_rate, name="볼린저 하단", line=dict(color='#6366F1', dash='dot')))
            update_chart_layout(fig_tech)
            st.plotly_chart(fig_tech, use_container_width=True)

            curr_rsi = df_t['RSI'].iloc[-1]
            rsi_status = f"{p_icon('🟢')}과매도 (매수 우위 가능성)" if curr_rsi < 30 else (f"{p_icon('🔴')}과매수 (매도 주의)" if curr_rsi > 70 else f"{p_icon('🟡')}중립")
            
            st.markdown(f"##### {p_icon('📌')}지표 진단 요약")
            c_i1, c_i2 = st.columns(2)
            c_i1.metric("현재 RSI 지표", f"{curr_rsi:.1f}", rsi_status)
            c_i2.caption("RSI가 30 이하이면 너무 많이 떨어졌다는 뜻이며, 70 이상이면 단기 과열을 의미합니다.")

            st.markdown("---")
            st.markdown(f"##### {p_icon('📰')}최신 뉴스 & 기업 소식")
            try:
                t_obj = yf.Ticker(sel_t)
                news = t_obj.news
                if news:
                    for n in news[:3]:
                        st.markdown(f"* [{n.get('title')}]({n.get('link')}) - *{n.get('publisher')}*")
                else:
                    st.write("관련 최신 뉴스가 없습니다.")
            except Exception:
                st.write("뉴스를 불러오는 중 오류가 발생했습니다.")

    # ----------------------------------------------------
    # TAB 4: 퀀트 & 리스크 분석
    # ----------------------------------------------------
    with tab4:
        st.markdown(f'<div class="guide-box">{p_icon("💡")}<b>퀀트 리스크 분석</b>: 변동성, 샤프 지수, MDD(최대 하락폭) 등 전문적인 위험 지표를 분석합니다.</div>', unsafe_allow_html=True)
        
        q_rows = []
        for t in valid_tickers[:6]:
            name = [k for k, v in target_stocks.items() if v == t][0]
            s = data[t].pct_change().dropna()
            
            ann_ret = s.mean() * 252 * 100
            ann_vol = s.std() * np.sqrt(252) * 100
            sharpe = (ann_ret - 2.0) / ann_vol if ann_vol > 0 else 0
            
            price_s = data[t]
            mdd = ((price_s - price_s.cummax()) / price_s.cummax()).min() * 100
            
            q_rows.append({
                "종목명": get_disp_name(name, t),
                "연환산 수익률 (%)": f"{ann_ret:+.2f}%",
                "연 변동성 (%)": f"{ann_vol:.2f}%",
                "샤프 지수 (위험대비수익)": f"{sharpe:.2f}",
                "최대 낙폭 (MDD)": f"{mdd:.2f}%"
            })
            
        st.dataframe(pd.DataFrame(q_rows), use_container_width=True, hide_index=True)

        st.markdown("""
        * **샤프 지수(Sharpe Ratio)**: 1.0 이상이면 위험 대비 수익률이 뛰어난 양호한 종목입니다.
        * **연 변동성**: 숫자가 크면 주가가 위아래로 심하게 요동친다는 뜻입니다.
        """)

    # ----------------------------------------------------
    # TAB 5: 프로 진단 보고서 (Free 안내 vs Pro 리포트)
    # ----------------------------------------------------
    with tab5:
        if not is_pro:
            st.markdown("""
            <div class="pro-report-card" style="border-color: #6366F1;">
                <h3 style="color: #6366F1; margin-top:0;">👑 Pro 모드란 무엇인가요?</h3>
                <p style="color: #CBD5E1; font-size: 0.95rem;">
                    Pro 모드는 주식 초보가 전문가 수준의 포트폴리오 관리를 경험할 수 있도록 <b>AI 포트폴리오 진단서</b> 및 <b>맞춤형 리밸런싱 처방전</b>을 제공하는 프리미엄 기능입니다.
                </p>
                <hr style="border-color: #334155; margin: 15px 0;">
                <h5 style="color: #F8FAFC;">✨ Pro 전용 제공 혜택:</h5>
                <ul style="color: #94A3B8; font-size: 0.9rem; line-height: 1.8;">
                    <li><b>💎 시각적 픽토그램 UI</b>: 모든 메뉴 및 지표에 차별화된 고급 이모지 아이콘 적용</li>
                    <li><b>📜 종합 포트폴리오 진단서</b>: 내 자산의 예상 수익률과 과거 1년 성과 종합 평가</li>
                    <li><b>🛡️ 맞춤형 리밸런싱 처방전</b>: 손실 위험을 줄이기 위한 최적의 국장/미장 비중 추천</li>
                </ul>
                <div style="background-color: #0F172A; padding: 10px 14px; border-radius: 6px; margin-top: 15px; border: 1px solid #1E293B;">
                    💡 <b>사용 방법</b>: 왼쪽 사이드바의 <b>[서비스 모드]</b> 설정에서 <b>Pro (전문가 모드)</b>를 선택하시면 즉시 모든 기능을 체험해보실 수 있습니다!
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            p_res = st.session_state.get('port_res', None)
            if p_res:
                tot_ret = p_res['tot_ret']
                sign = "+" if tot_ret >= 0 else ""
                cls_color = "#10B981" if tot_ret >= 0 else "#EF4444"
                
                st.markdown(f"""
                <div class="pro-report-card">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8;">👑 StockLab Pro 포트폴리오 진단 리포트</div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 12px;">진단 일자: {datetime.now().strftime("%Y-%m-%d")}</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: {cls_color};">
                        예상 수익률: {sign}{tot_ret:.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("##### 🛡️ 종합 처방전")
                st.markdown(f"""
                1. **수익률 종합 평가**: 선택하신 포트폴리오의 과거 1년 추정 수익률은 **{sign}{tot_ret:.1f}%**입니다.
                2. **포트폴리오 개선 가이드**: 고변동성 개별주 위주로 구성된 경우, KODEX 200이나 S&P 500 ETF를 30% 이상 섞어 위험을 분산하는 것을 권장합니다.
                """)
            else:
                st.info("Tab 2 (포트폴리오 계산기)에서 먼저 분석을 실행해주세요.")

st.sidebar.markdown("---")
st.sidebar.code("Contact: aseui995@gmail.com", language="text")
