# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional
from streamlit_option_menu import option_menu

# 백엔드 모듈 임포트
from api.supabase_client import SupabasePOSClient
from core.analyzer import SalesAnalyzer

# --- 1. CONFIG & STYLING ---

st.set_page_config(
    page_title="Smart POS Insight Reporter", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css(file_name: str):
    """지정된 CSS 파일을 로드하고 <style> 태그로 감싸 반환합니다."""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f"<style>{f.read()}</style>"
    except FileNotFoundError:
        return "<style>body {color: red; font-size: 24px;}</style>" # 에러 표시

# 커스텀 CSS 파일 적용
css_file = "src/style.css"
st.markdown(load_css(css_file), unsafe_allow_html=True)


# --- 2. DATA LOADING & CACHING ---

@st.cache_data
def load_and_analyze_data() -> Optional[SalesAnalyzer]:
    """
    데이터를 로드하고 분석기를 생성하는 전체 과정을 수행합니다.
    Streamlit의 캐싱 기능을 활용하여 이 함수의 결과는 한 번만 실행되고 캐시에 저장됩니다.
    """
    try:
        client = SupabasePOSClient()
        sales_data = client.fetch_weekly_sales_data()
        if not sales_data:
            st.error("매출 데이터를 불러오는 데 실패했습니다. Supabase 연결 및 데이터 유무를 확인하세요.")
            return None
        analyzer = SalesAnalyzer(sales_data)
        if analyzer.df is None:
            st.error("데이터 분석기 초기화에 실패했습니다. 데이터 형식을 확인해주세요.")
            return None
        return analyzer
    except Exception as e:
        st.error(f"처리 중 예기치 않은 오류가 발생했습니다: {e}")
        return None

# --- 3. UI DISPLAY FUNCTIONS ---

def display_dow_analysis(analyzer: SalesAnalyzer):
    """요일별 분석 결과를 대시보드에 표시합니다."""
    st.header("요일별 매출 동향")
    st.write("요일에 따른 매출액과 거래 건수의 변화를 확인하여, 요일별 프로모션이나 인력 배치의 근거로 활용할 수 있습니다.")
    st.markdown("---")
    
    dow_result = analyzer.aggregate_sales_by_dow()
    
    if dow_result is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("총 매출액 (원)")
            fig_sales = px.bar(
                dow_result,
                x=dow_result.index,
                y='total_sales',
                labels={'x': '요일', 'total_sales': '총 매출액'},
                template='plotly_dark',
                text_auto=True
            )
            fig_sales.update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_sales.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#02ab21')
            st.plotly_chart(fig_sales, use_container_width=True)
        
        with col2:
            st.subheader("거래 건수")
            fig_trans = px.bar(
                dow_result,
                x=dow_result.index,
                y='transaction_count',
                labels={'x': '요일', 'transaction_count': '거래 건수'},
                template='plotly_dark',
                text_auto=True
            )
            fig_trans.update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_trans.update_traces(texttemplate='%{y:,}', textposition='outside', marker_color='#1c83e1')
            st.plotly_chart(fig_trans, use_container_width=True)

        with st.expander("요일별 상세 데이터 보기"):
            st.dataframe(dow_result.style.format({
                "total_sales": "{:,.0f}원",
                "transaction_count": "{:,}건"
            }))
    else:
        st.warning("요일별 분석 데이터를 생성할 수 없습니다.")

def display_menu_analysis(analyzer: SalesAnalyzer):
    """메뉴별 분석 결과를 대시보드에 표시합니다."""
    st.header("메뉴별 판매 순위")
    st.write("가장 인기 있는 메뉴와 각 메뉴의 판매 실적을 확인하여, 재고 관리 및 메뉴판 구성에 활용할 수 있습니다.")
    st.markdown("---")
    
    menu_result = analyzer.aggregate_sales_by_menu()

    if menu_result is not None:
        st.dataframe(menu_result.style.format({
            "total_quantity": "{:,}개",
            "total_sales": "{:,.0f}원"
        }))
    else:
        st.warning("메뉴별 분석 데이터를 생성할 수 없습니다.")

# --- 4. MAIN APP LAYOUT ---

def main():
    """메인 애플리케이션 실행 함수"""
    analyzer = load_and_analyze_data()

    with st.sidebar:
        st.title("📈 Smart POS Reporter")
        st.write("데이터 기반 매장 관리 솔루션")
        st.markdown("---")
        if analyzer:
            with st.expander("전체 거래 데이터 원본 보기", expanded=False):
                st.dataframe(analyzer.df)
        st.markdown("---")
        st.info("© 2026 Gemini Solutions. All Rights Reserved.")

    if analyzer:
        selected = option_menu(
            menu_title=None,
            options=["요일별 분석", "메뉴별 분석"],
            icons=["bar-chart-line-fill", "cup-hot-fill"],
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#FFF", "font-size": "20px"},
                "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px 5px", "padding":"15px 20px", "--hover-color": "#444"},
                "nav-link-selected": {"background-color": "#1c83e1", "color": "#FFFFFF", "border-radius": "8px"},
            }
        )

        if selected == "요일별 분석":
            display_dow_analysis(analyzer)
        elif selected == "메뉴별 분석":
            display_menu_analysis(analyzer)

if __name__ == "__main__":
    main()