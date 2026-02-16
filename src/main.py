# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Optional, Any, Dict
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
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            return f"<style>{f.read()}</style>"
    except FileNotFoundError:
        return ""

st.markdown(load_css("src/style.css"), unsafe_allow_html=True)


# --- 2. DATA LOADING & CACHING ---

@st.cache_data
def load_and_analyze_data() -> Optional[SalesAnalyzer]:
    try:
        client = SupabasePOSClient()
        sales_data = client.fetch_weekly_sales_data()
        if not sales_data:
            st.error("매출 데이터를 불러오는 데 실패했습니다. Supabase 연결 및 데이터 유무를 확인하세요.")
            return None
        # 데이터 보강 분석을 위해 SalesAnalyzer 초기화
        analyzer = SalesAnalyzer(sales_data, year=2026)
        if analyzer.df is None:
            st.error("데이터 분석기 초기화에 실패했습니다. 데이터 형식을 확인해주세요.")
            return None
        return analyzer
    except Exception as e:
        st.error(f"처리 중 예기치 않은 오류가 발생했습니다: {e}")
        return None

# --- 3. UI DISPLAY FUNCTIONS ---

def display_dow_analysis(analyzer: SalesAnalyzer):
    # ... (기존과 동일, 변경 없음) ...
    st.header("요일별 매출 동향")
    st.write("요일에 따른 매출액과 거래 건수의 변화를 확인하여, 요일별 프로모션이나 인력 배치의 근거로 활용할 수 있습니다.")
    st.markdown("---")
    dow_result = analyzer.aggregate_sales_by_dow()
    if dow_result is not None:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("총 매출액 (원)")
            fig_sales = px.bar(dow_result, x=dow_result.index, y='total_sales', template='plotly_dark', text_auto=True)
            fig_sales.update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_sales.update_traces(texttemplate='%{y:,.0f}', textposition='outside', marker_color='#02ab21')
            st.plotly_chart(fig_sales, use_container_width=True)
        with col2:
            st.subheader("거래 건수")
            fig_trans = px.bar(dow_result, x=dow_result.index, y='transaction_count', template='plotly_dark', text_auto=True)
            fig_trans.update_layout(yaxis_title=None, xaxis_title=None, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            fig_trans.update_traces(texttemplate='%{y:,}', textposition='outside', marker_color='#1c83e1')
            st.plotly_chart(fig_trans, use_container_width=True)
        with st.expander("요일별 상세 데이터 보기"):
            st.dataframe(dow_result.style.format({"total_sales": "{:,.0f}원", "transaction_count": "{:,}건"}))
    else:
        st.warning("요일별 분석 데이터를 생성할 수 없습니다.")

def display_menu_analysis(analyzer: SalesAnalyzer):
    # ... (기존과 동일, 변경 없음) ...
    st.header("메뉴별 판매 순위")
    st.write("가장 인기 있는 메뉴와 각 메뉴의 판매 실적을 확인하여, 재고 관리 및 메뉴판 구성에 활용할 수 있습니다.")
    st.markdown("---")
    menu_result = analyzer.aggregate_sales_by_menu()
    if menu_result is not None:
        st.dataframe(menu_result.style.format({"total_quantity": "{:,}개", "total_sales": "{:,.0f}원"}))
    else:
        st.warning("메뉴별 분석 데이터를 생성할 수 없습니다.")

def display_external_factor_analysis(analyzer: SalesAnalyzer):
    """외부요인(공휴일, 날씨) 분석 결과를 대시보드에 표시합니다."""
    st.header("외부 요인과 매출의 상관관계")
    st.write("공휴일, 날씨 등 외부 환경 요인이 매출에 미치는 영향을 분석하여, 보다 정교한 수요 예측 및 프로모션 전략을 수립합니다.")
    st.markdown("---")

    # 1. 공휴일 영향 분석
    st.subheader("🗓️ 공휴일/평일 매출 비교")
    holiday_impact = analyzer.analyze_holiday_impact()
    if holiday_impact is not None and not holiday_impact.empty:
        fig_holiday = px.bar(
            holiday_impact,
            x='is_holiday', y='avg_daily_sales',
            labels={'is_holiday': '유형', 'avg_daily_sales': '평균 일 매출'},
            template='plotly_dark', text_auto=True,
            color='is_holiday', color_discrete_map={'공휴일': '#ff6347', '평일': '#1c83e1'}
        )
        fig_holiday.update_layout(yaxis_title="매출액 (원)", xaxis_title=None, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        fig_holiday.update_traces(texttemplate='%{y:,.0f}원', textposition='outside')
        st.plotly_chart(fig_holiday, use_container_width=True)
    else:
        st.warning("공휴일 영향 분석 데이터를 생성할 수 없습니다.")
    
    st.markdown("<br>", unsafe_allow_html=True) 

    # 2. 날씨 영향 분석
    st.subheader("🌦️ 날씨-매출 연관성 분석")
    weather_impact = analyzer.analyze_weather_impact()
    if weather_impact:
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="☂️ 우천 시 평균 일 매출", value=f"{weather_impact.get('rainy_day_avg_sales', 0):,.0f} 원")
        with col2:
            correlation = weather_impact.get('temp_sales_correlation', 0)
            st.metric(
                label="🌡️ 기온-매출 상관계수",
                value=f"{correlation:.2f}",
                help="1에 가까울수록 기온이 오를 때 매출이 오르며, -1에 가까울수록 기온이 오를 때 매출이 떨어집니다."
            )
            # 상관계수 강도 설명
            corr_abs = abs(correlation)
            if corr_abs >= 0.7: st.success("매우 강한 상관관계")
            elif corr_abs >= 0.4: st.info("뚜렷한 상관관계")
            elif corr_abs >= 0.2: st.warning("약한 상관관계")
            else: st.error("상관관계 거의 없음")
    else:
        st.warning("날씨 영향 분석 데이터를 생성할 수 없습니다.")

# --- 4. MAIN APP LAYOUT ---

def main():
    analyzer = load_and_analyze_data()
    with st.sidebar:
        st.title("📈 Smart POS Reporter")
        st.write("데이터 기반 매장 관리 솔루션")
        st.markdown("---")
        if analyzer and analyzer.df is not None:
            with st.expander("데이터 원본 및 보강 결과 보기", expanded=False):
                # 날씨/공휴일 정보가 포함된 df를 보여줌
                display_df = analyzer.df[['timestamp', 'item_name', 'price', 'quantity', 'total_sales', 'is_holiday', 'weather', 'avg_temp']].copy()
                display_df['is_holiday'] = display_df['is_holiday'].map({True: 'O', False: 'X'})
                st.dataframe(display_df)
        st.markdown("---")
        st.info("© 2026 Gemini Solutions.")

    if analyzer:
        selected = option_menu(
            menu_title=None,
            options=["요일별 분석", "메뉴별 분석", "외부요인 분석"],
            icons=["bar-chart-line-fill", "cup-hot-fill", "cloud-sun-fill"],
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
        elif selected == "외부요인 분석":
            display_external_factor_analysis(analyzer)

if __name__ == "__main__":
    main()
