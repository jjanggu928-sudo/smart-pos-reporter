# -*- coding: utf-8 -*-
"""
Smart POS Insight Reporter - 메인 대시보드

이 애플리케이션은 Streamlit을 사용하여 POS 매출 데이터를 분석하고 시각화합니다.
`pos_client`를 통해 데이터를 로드하고, `SalesAnalyzer`로 분석한 결과를
사용자 친화적인 대시보드 형태로 제공합니다.

주요 기능:
- 데이터 캐싱: `@st.cache_data`를 사용하여 데이터 로딩 및 전처리 과정을 캐싱함으로써,
  UI 상호작용 시 불필요한 재연산을 방지하고 앱 반응 속도를 최적화합니다.
- 데이터 시각화: Streamlit의 내장 차트(`st.bar_chart`)와 데이터프레임 표시(`st.dataframe`) 기능을
  활용하여 분석 결과를 직관적으로 전달합니다.
- 모듈화된 구조: 데이터 로딩, 분석, UI 표시 로직을 각각 함수로 분리하여
  코드의 가독성과 유지보수성을 높입니다.

실행 방법:
- 프로젝트 루트 디렉터리에서 `streamlit run src/main.py` 명령어를 실행합니다.
"""
import streamlit as st
import pandas as pd
from typing import Optional

# 백엔드 모듈 임포트
from api.pos_client import MockPOSClient
from core.analyzer import SalesAnalyzer

@st.cache_data
def load_and_analyze_data() -> Optional[SalesAnalyzer]:
    """
    데이터를 로드하고 분석기를 생성하는 전체 과정을 수행합니다.
    Streamlit의 캐싱 기능을 활용하여 이 함수의 결과는 한 번만 실행되고 캐시에 저장됩니다.
    
    Returns:
        Optional[SalesAnalyzer]: 데이터 분석이 완료된 SalesAnalyzer 객체.
                                 데이터 로딩 또는 분석 실패 시 None을 반환합니다.
    """
    try:
        client = MockPOSClient()
        sales_data = client.fetch_weekly_sales_data()
        if not sales_data:
            st.error("매출 데이터를 불러오는 데 실패했습니다. 원본 데이터 파일을 확인해주세요.")
            return None
        
        analyzer = SalesAnalyzer(sales_data)
        if analyzer.df is None:
            st.error("데이터 분석기 초기화에 실패했습니다. 데이터 형식을 확인해주세요.")
            return None
            
        return analyzer
    except Exception as e:
        st.error(f"처리 중 예기치 않은 오류가 발생했습니다: {e}")
        return None

def display_dow_analysis(analyzer: SalesAnalyzer):
    """요일별 분석 결과를 대시보드에 표시합니다."""
    st.header("📊 요일별 매출 분석")
    dow_result = analyzer.aggregate_sales_by_dow()
    
    if dow_result is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("총 매출액 (원)")
            # Streamlit은 인덱스를 x축으로, 컬럼을 y축으로 자동으로 인식합니다.
            st.bar_chart(dow_result['total_sales'])
        
        with col2:
            st.subheader("거래 건수")
            st.bar_chart(dow_result['transaction_count'])

        with st.expander("요일별 상세 데이터 보기"):
            st.dataframe(dow_result.style.format({
                "total_sales": "{:,.0f}원",
                "transaction_count": "{:,}건"
            }))
    else:
        st.warning("요일별 분석 데이터를 생성할 수 없습니다.")

def display_menu_analysis(analyzer: SalesAnalyzer):
    """메뉴별 분석 결과를 대시보드에 표시합니다."""
    st.header("🍕 메뉴별 판매 분석")
    menu_result = analyzer.aggregate_sales_by_menu()

    if menu_result is not None:
        st.dataframe(menu_result.style.format({
            "total_quantity": "{:,}개",
            "total_sales": "{:,.0f}원"
        }))
    else:
        st.warning("메뉴별 분석 데이터를 생성할 수 없습니다.")

def main():
    """메인 애플리케이션 실행 함수"""
    st.set_page_config(page_title="Smart POS Insight Reporter", layout="wide")
    st.title("📈 Smart POS Insight Reporter")
    st.write("가상 POS 데이터를 분석하여 요일별, 메뉴별 판매 현황에 대한 인사이트를 제공합니다.")

    # 데이터 로드 및 분석
    analyzer = load_and_analyze_data()

    if analyzer:
        # 분석 결과 표시
        display_dow_analysis(analyzer)
        st.divider()
        display_menu_analysis(analyzer)

        # 원본 데이터 표시
        with st.expander("전체 거래 데이터 원본 보기"):
            st.dataframe(analyzer.df)

if __name__ == "__main__":
    main()
