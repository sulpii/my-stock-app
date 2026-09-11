        # TAB 5: 와튼 대회 보고서 자동 생성
        with tab5:
            st.markdown("### 📝 Wharton Competition Executive Summary Generator")
            st.caption("탭 2에서 설정한 자산 비중과 백테스트 결과를 바탕으로 제출용 보고서 요약문을 자동 생성합니다.")
            
            if 'total_weight' in locals() and total_weight > 0:
                lang = st.radio("보고서 언어 선택", ["한국어", "English"])
                
                weight_summary = ", ".join([f"{t}: {w}%" for t, w in zip(valid_tickers, weights) if w > 0])
                
                # Series/단일값 호환 처리
                display_vol = ann_vol.iloc[0] if isinstance(ann_vol, (pd.Series, np.ndarray)) else ann_vol
                display_sharpe = sharpe.iloc[0] if isinstance(sharpe, (pd.Series, np.ndarray)) else sharpe
                
                if lang == "한국어":
                    report_text = f"""
### 📄 와튼 대회 포트폴리오 전략 요약서

**1. 자산 배분 구조 (Asset Allocation)**
본 포트폴리오는 위험 분산과 안정적 수익 달성을 위해 다음과 같이 자산을 배분하였습니다:
- **구성 종목 및 비중:** {weight_summary}

**2. 백테스팅 성과 및 위험 분석 (Performance & Risk)**
- **포트폴리오 총 수익률:** {tot_return:.2f}%
- **연간 변동성(위험도):** {display_vol:.2f}%
- **샤프 지수 (Sharpe Ratio):** {display_sharpe:.2f} (무위험 수익률 4% 기준)
- **최대 낙폭 (MDD):** {mdd:.2f}%

**3. 투자 핵심 논리 (Investment Thesis)**
본 포트폴리오는 {valid_tickers[0]} 등의 성장 자산을 통해 수익성을 확보하는 동시에, 자산 간 상관관계를 고려하여 최대 낙폭({mdd:.2f}%)을 효과적으로 통제하도록 설계되었습니다. 특히 샤프 지수 {display_sharpe:.2f}를 기록하며 위험 대비 우수한 수익 효율성을 입증하였습니다.
                    """
                else:
                    report_text = f"""
### 📄 Wharton Investment Strategy Executive Summary

**1. Asset Allocation Breakdown**
To optimize risk-adjusted returns, the portfolio is allocated as follows:
- **Target Allocation:** {weight_summary}

**2. Historical Performance & Risk Metrics**
- **Total Portfolio Return:** {tot_return:.2f}%
- **Annualized Volatility:** {display_vol:.2f}%
- **Sharpe Ratio:** {display_sharpe:.2f} (Assumed Risk-Free Rate: 4.0%)
- **Maximum Drawdown (MDD):** {mdd:.2f}%

**3. Investment Thesis**
This strategy strikes a balance between capital growth and risk mitigation. By combining growth assets with defensive instruments, the portfolio successfully controlled maximum drawdown to {mdd:.2f}% while maintaining a robust Sharpe ratio of {display_sharpe:.2f}.
                    """
                
                st.markdown(report_text)
                st.text_area("텍스트 복사용 상자", report_text, height=200)
            else:
                st.warning("탭 2(포트폴리오 시뮬레이터)에서 종목 비중을 설정해 주세요.")
