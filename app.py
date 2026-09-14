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

# Custom CSS (모던 핀테크 다크 스타일 & 픽토그램 제거)
st.markdown("""
    <style>
    .stApp { background-color: #0B0E14; color: #E2E8F0; font-family: 'Pretendard', sans-serif; }
    .main-header { font-size: 2.0rem; font-weight: 800; color: #38BDF8; margin-bottom: 2px; }
    .sub-header { font-size: 0.95rem; color: #94A3B8; margin-bottom: 20px; }
    .version-tag {
        background-color: #1E293B; color: #38BDF8; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 700; border: 1px solid #334155;
    }
    .kpi-card {
        background-color: #1E293B; border: 1px solid #334155; border-radius: 10px; padding: 14px 16px;
    }
    .kpi-title { font-size: 0.85rem; color: #94A3B8; font-weight: 600; }
    .kpi-value { font-size: 1.3rem; color: #F8FAFC; font-weight: 700; margin: 4px 0; }
    .kpi-pos { color: #10B981; } .kpi-neg { color: #EF4444; }
    
    .guide-box {
        background-color: #1E293B; border-left: 4px solid #38BDF8; padding: 12px 16px;
        border-radius: 4px; font-size: 0.9rem; color: #CBD5E1; margin-bottom: 15px;
    }
    
    .pro-report-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #38BDF8; border-radius: 12px; padding: 24px; margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# 🌐 다국어 및 디스플레이 정의
LANG_DICT = {
    "한국어": {
        "title": "StockLab",
        "subtitle": "초보자를 위한 쉬운 주식 분석 및 모의투자 시뮬레이터",
        "market_select": "시장 선택",
        "currency_select": "표시 통화",
        "ver_select": "서비스 모드",
        "tab_sim": "모의투자",
        "tab_calc": "포트폴리오 계산기",
        "tab_tech": "종합 지표 진단",
        "tab_risk": "리스크 분석",
        "tab_pro": "프로 진단 보고서",
        "calc_btn": "포트폴리오 분석하기",
        "pro_lock": "Pro 전용 기능입니다. 왼쪽 사이드바에서 Pro 모드로 전환해주세요.",
        "buy_btn": "매수하기",
        "sell_btn": "매도하기"
    },
    "English": {
        "title": "StockLab",
        "subtitle": "Easy Stock Analytics & Paper Trading for Beginners",
        "market_select": "Market",
        "currency_select": "Currency",
        "ver_select": "Mode",
        "tab_sim": "Paper Trading",
        "tab_calc": "Portfolio Calculator",
        "tab_tech": "Indicator Check",
        "tab_risk": "Risk Analysis",
        "tab_pro": "Pro Report",
        "calc_btn": "Analyze Portfolio",
        "pro_lock": "Pro feature only. Switch to Pro mode in the sidebar.",
        "buy_btn": "Buy",
        "sell_btn": "Sell"
    },
    "日本語": {
        "title": "StockLab",
        "subtitle": "初心者のための株式分析＆ペ파트レード",
        "market_select": "市場選択",
        "currency_select": "表示通貨",
        "ver_select": "モード選択",
        "tab_sim": "模擬投資",
        "tab_calc": "ポートフォリオ計算機",
        "tab_tech": "総合指標診断",
        "tab_risk": "リスク分析",
        "tab_pro": "Pro 診断レポート",
        "calc_btn": "ポートフォリオを分析",
        "pro_lock": "Pro専用機能です。Proモードに切り替えてください。",
        "buy_btn": "買い",
        "sell_btn": "売り"
    },
    "中文": {
        "title": "StockLab",
        "subtitle": "面向初学者的简易股票分析与模拟交易",
        "market_select": "选择市场",
        "currency_select": "显示货币",
        "ver_select": "模式选择",
        "tab_sim": "模拟交易",
        "tab_calc": "组合计算器",
        "tab_tech": "综合指标诊断",
        "tab_risk": "风险分析",
        "tab_pro": "Pro 诊断报告",
        "calc_btn": "分析投资组合",
        "pro_lock": "此功能仅限 Pro 用户。请切换至 Pro 模式。",
        "buy_btn": "买入",
        "sell_btn": "卖出"
    }
}

# 시장별 대표 종목 데이터 정의
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

# 국내 종목 번역 사전
KR_TRANSLATIONS = {
    "English": {"삼성전자": "Samsung Electronics", "SK하이닉스": "SK Hynix", "NAVER": "NAVER", "카카오": "Kakao", "현대차": "Hyundai Motor", "KODEX 200": "KODEX 200"},
    "日本語": {"삼성전자": "サムスン電子", "SK하이닉스": "SKハイニックス", "NAVER": "NAVER", "카카오": "カカオ", "현대차": "現代自動車", "KODEX 200": "KODEX 200"},
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

# 모의투자 세션 초기화
if 'cash' not in st.session_state:
    st.session_state['cash'] = 10000000.0  # 초기 1,000만 원
if 'portfolio' not in st.session_state:
    st.session_state['portfolio'] = {}  # {ticker: quantity}

# Sidebar UI
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

# 종목 리스트 구성
target_stocks = {}
if market_choice == "미국 주식 (US Market)":
    target_stocks = STOCKS["미국 주식 (US Market)"]
elif market_choice == "국내 주식 (KR Market)":
    target_stocks = STOCKS["국내 주식 (KR Market)"]
else:
    target_stocks = {**STOCKS["미국 주식 (US Market)"], **STOCKS["국내 주식 (KR Market)"]}

# 종목 이름 표기 변환 함수
def get_disp_name(name, symbol):
    if symbol.endswith(".KS"): # 국내 주식
        translated = KR_TRANSLATIONS.get(selected_lang, {}).get(name, name)
        return translated
    else: # 해외 주식 (영문 고정)
        return name

# Header
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f'<p class="main-header">{L["title"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub-header">{L["subtitle"]}</p>', unsafe_allow_html=True)
with col_h2:
    tag_name = "Pro Version" if is_pro else "Free Version"
    st.markdown(f'<div style="text-align:right; margin-top:10px;"><span class="version-tag">{tag_name}</span></div>', unsafe_allow_html=True)

# 데이터 로딩
today = datetime.today()
start_date = today - timedelta(days=365)
tickers = list(target_stocks.values())

with st.spinner('Real-time Data Syncing...'):
    data = fetch_stock_data(tickers, str(start_date.strftime('%Y-%m-%d')), str(today.strftime('%Y-%m-%d')))

def update_chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=360
    )

if not data.empty:
    valid_tickers = [t for t in tickers if t in data.columns and not data[t].dropna().empty]
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        L["tab_sim"], L["tab_calc"], L["tab_tech"], L["tab_risk"], L["tab_pro"]
    ])

    # TAB 1: 모의투자 (Paper Trading)
    with tab1:
        st.markdown('<div class="guide-box">💡 <b>초보자를 위한 가상 매매</b>: 가상 자산 1,000만 원으로 위험 없이 실제 주식을 사고팔며 연습해보세요.</div>', unsafe_allow_html=True)
        
        # 잔고 표시
        m1, m2 = st.columns(2)
        m1.metric("보유 가상 현금", f"{curr_symbol}{st.session_state['cash'] * (fx_rate if curr_key!='KRW' else 1):,.0f}")
        
        selected_disp = st.selectbox("거래할 종목 선택", list(target_stocks.keys()), format_func=lambda x: get_disp_name(x, target_stocks[x]))
        sel_symbol = target_stocks[selected_disp]
        
        if sel_symbol in data.columns:
            curr_price_krw = data[sel_symbol].iloc[-1]
            if not sel_symbol.endswith(".KS"): # 해외주식 원화 환산
                rates_tmp = get_exchange_rates()
                curr_price_krw = curr_price_krw * rates_tmp["KRW"][0]
            
            disp_price = curr_price_krw * (fx_rate / rates["KRW"][0] if curr_key != "KRW" else 1.0)
            
            st.write(f"현재가: **{curr_symbol}{disp_price:,.0f}**")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                buy_qty = st.number_input("매수 수량", min_value=1, value=1, key="buy_q")
                if st.button(L["buy_btn"], use_container_width=True):
                    total_cost = curr_price_krw * buy_qty
                    if st.session_state['cash'] >= total_cost:
                        st.session_state['cash'] -= total_cost
                        st.session_state['portfolio'][sel_symbol] = st.session_state['portfolio'].get(sel_symbol, 0) + buy_qty
                        st.success(f"{get_disp_name(selected_disp, sel_symbol)} {buy_qty}주 매수 완료!")
                        st.rerun()
                    else:
                        st.error("가상 현금이 부족합니다.")
            
            with col_b2:
                sell_qty = st.number_input("매도 수량", min_value=1, value=1, key="sell_q")
                if st.button(L["sell_btn"], use_container_width=True):
                    curr_qty = st.session_state['portfolio'].get(sel_symbol, 0)
                    if curr_qty >= sell_qty:
                        st.session_state['cash'] += curr_price_krw * sell_qty
                        st.session_state['portfolio'][sel_symbol] -= sell_qty
                        st.success(f"{get_disp_name(selected_disp, sel_symbol)} {sell_qty}주 매도 완료!")
                        st.rerun()
                    else:
                        st.error("보유 수량이 부족합니다.")

    # TAB 2: 쉬운 포트폴리오 계산기
    with tab2:
        st.markdown('<div class="guide-box">💡 <b>쉬운 투자 비중 계산</b>: 각 주식을 얼마씩 담으면 안전하고 수익이 날지 슬라이더로 조절해보세요.</div>', unsafe_allow_html=True)
        
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
            fig_calc.add_trace(go.Scatter(x=port_cum.index, y=port_cum, mode='lines', name='내 포트폴리오', line=dict(color='#38BDF8', width=3)))
            update_chart_layout(fig_calc)
            st.plotly_chart(fig_calc, use_container_width=True)
            
            st.session_state['port_res'] = {'tot_ret': port_cum.iloc[-1] - 100, 'daily_ret': port_ret}

    # TAB 3: 종합 지표 진단 (쉬운 신호등 개념)
    with tab3:
        st.markdown('<div class="guide-box">💡 <b>초보자용 지표 진단</b>: 어려운 용어 대신 신호등 상태로 현재 주가의 위치를 진단해드립니다.</div>', unsafe_allow_html=True)
        
        sel_name = st.selectbox("진단할 종목 선택", list(target_stocks.keys()), format_func=lambda x: get_disp_name(x, target_stocks[x]))
        sel_t = target_stocks[sel_name]
        
        if sel_t in data.columns:
            s_data = data[sel_t].dropna()
            curr_p = s_data.iloc[-1]
            ma50 = s_data.rolling(50).mean().iloc[-1]
            
            # 신호등 로직
            status_color = "🟢 안전 (상승 추세)" if curr_p > ma50 else "🟡 주의 (조정 구간)"
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                st.markdown(f"### 추세 진단: **{status_color}**")
                st.write(f"* **현재 주가**: {curr_symbol}{curr_p * fx_rate:,.1f}")
                st.write(f"* **50일 평균가**: {curr_symbol}{ma50 * fx_rate:,.1f}")
                st.caption("주가가 50일 평균선 위에 있으면 활발하게 상승 중이라는 의미입니다.")
            
            with col_t2:
                fig_t = go.Figure()
                fig_t.add_trace(go.Scatter(x=s_data.index, y=s_data * fx_rate, name="주가", line=dict(color='#38BDF8')))
                fig_t.add_trace(go.Scatter(x=s_data.index, y=s_data.rolling(50).mean() * fx_rate, name="50일 평균선", line=dict(color='#F59E0B')))
                update_chart_layout(fig_t)
                st.plotly_chart(fig_t, use_container_width=True)

    # TAB 4: 리스크 분석 (초보자용 비유 추가)
    with tab4:
        st.markdown('<div class="guide-box">💡 <b>위험도 한눈에 보기</b>: 주식이 급락할 때 내 자산이 얼마나 깎일 수 있는지(최대 낙폭) 알려드립니다.</div>', unsafe_allow_html=True)
        
        r_cols = st.columns(2)
        with r_cols[0]:
            st.markdown("##### 종목별 최고점 대비 최대 하락폭 (MDD)")
            mdd_list = {}
            for t in valid_tickers[:5]:
                name = [k for k, v in target_stocks.items() if v == t][0]
                s = data[t]
                drawdown = (s - s.cummax()) / s.cummax()
                mdd_list[get_disp_name(name, t)] = drawdown.min() * 100
            
            mdd_df = pd.DataFrame(list(mdd_list.items()), columns=['종목', '최대 하락폭 (%)'])
            fig_mdd = px.bar(mdd_df, x='종목', y='최대 하락폭 (%)', color='최대 하락폭 (%)', color_continuous_scale='Reds_r')
            update_chart_layout(fig_mdd)
            st.plotly_chart(fig_mdd, use_container_width=True)

        with r_cols[1]:
            st.markdown("##### 💡 리스크 관리 가이드")
            st.markdown("""
            * **최대 하락폭이란?**: 과거에 주식을 가장 안 좋은 타이밍에 샀을 때 경험할 수 있었던 최대 손실 비율입니다.
            * **초보자 팁**: 하락폭이 -30% 이상으로 큰 종목은 비중을 20% 미만으로 낮게 유지하는 것이 마인드 관리에 유리합니다.
            """)

    # TAB 5: 프로 진단 보고서 (화면 대시보드 출력)
    with tab5:
        if not is_pro:
            st.warning(L["pro_lock"])
        else:
            p_res = st.session_state.get('port_res', None)
            if p_res:
                tot_ret = p_res['tot_ret']
                sign = "+" if tot_ret >= 0 else ""
                cls_color = "#10B981" if tot_ret >= 0 else "#EF4444"
                
                st.markdown(f"""
                <div class="pro-report-card">
                    <div style="font-size: 1.3rem; font-weight: 800; color: #38BDF8;">👑 StockLab Pro 포트폴리오 진단서</div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 12px;">진단 일자: {datetime.now().strftime("%Y-%m-%d")}</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: {cls_color};">
                        예상 수익률: {sign}{tot_ret:.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("##### 🛡️ 종합 투자 처방전")
                st.markdown(f"""
                1. **수익률 평가**: 최근 1년 성과 기준 **{sign}{tot_ret:.1f}%** 성과를 기록했습니다.
                2. **개선 제안**: 단일 종목 올인보다는 국장/미장 ETF를 20% 이상 혼합하면 하락장 방어력이 높아집니다.
                """)
            else:
                st.info("Tab 2 (포트폴리오 계산기)에서 분석을 진행해 주세요.")

st.sidebar.markdown("---")
st.sidebar.code("Contact: aseui995@gmail.com", language="text")
