# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import holidays
from typing import List, Dict, Any, Optional
import random

class SalesAnalyzer:
    """
    Supabase 평면 데이터 구조와 날씨/공휴일 데이터를 연동하는 통합 분석 클래스.
    """
    def __init__(self, sales_data: List[Dict[str, Any]], year: int = 2025):
        self.raw_data = sales_data
        self.year = year
        self.df: Optional[pd.DataFrame] = self._prepare_dataframe()

        if self.df is not None:
            # 데이터 보강 파이프라인
            self.df = self._add_holiday_flag(self.df)
            self.df = self._generate_and_merge_weather_data(self.df)

    def _prepare_dataframe(self) -> Optional[pd.DataFrame]:
        """실제 DB의 평면 구조(total_amount, created_at)를 판다스 형식으로 변환"""
        if not self.raw_data:
            return None
        try:
            # Supabase의 평면 리스트를 바로 데이터프레임으로 변환
            df = pd.DataFrame(self.raw_data)
            
            # 날짜 및 숫자 형식 변환
            df['timestamp'] = pd.to_datetime(df['created_at'])
            # 'total_amount' 컬럼이 없는 경우를 대비해 예외 처리 및 0 채우기
            amt_col = 'total_amount' if 'total_amount' in df.columns else 'amount'
            df['total_sales'] = pd.to_numeric(df[amt_col]).fillna(0)
            
            # 메뉴 분석을 위한 기본값 설정 (항목 데이터가 따로 없을 경우)
            if 'item_name' not in df.columns:
                df['item_name'] = '기본 결제'
            if 'quantity' not in df.columns:
                df['quantity'] = 1
                
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            return df
        except Exception as e:
            print(f"데이터 전처리 중 오류: {e}")
            return None

    def _add_holiday_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """대한민국 공휴일 정보 추가"""
        kr_holidays = holidays.KR(years=self.year)
        df['date'] = df['timestamp'].dt.date
        df['is_holiday'] = df['date'].apply(lambda x: x in kr_holidays)
        return df

    def _generate_and_merge_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """데이터가 존재하는 2025년 전체 기간에 대한 가상 날씨 생성 및 결합"""
        # 데이터의 실제 날짜 범위를 추출하여 날씨 생성
        start_date = f'{self.year}-01-01'
        end_date = f'{self.year}-12-31'
        dates = pd.to_datetime(pd.date_range(start_date, end_date))
        
        weather_conditions = ['맑음', '비', '눈']
        weather_data = [random.choices(weather_conditions, weights=[0.7, 0.2, 0.1], k=1)[0] for _ in dates]
        temp_data = np.random.uniform(-10, 30, size=len(dates)) # 연간 기온 분포 (-10~30도)
        
        weather_df = pd.DataFrame({
            'date': dates.date,
            'weather': weather_data,
            'avg_temp': temp_data
        })
        
        return pd.merge(df, weather_df, on='date', how='left')

    def aggregate_sales_by_dow(self) -> Optional[pd.DataFrame]:
        if self.df is None: return None
        dow_analysis = self.df.groupby('day_of_week').agg(
            total_sales=('total_sales', 'sum'),
            transaction_count=('id', 'nunique')
        ).sort_index()
        day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        dow_analysis.index = dow_analysis.index.map(day_map)
        return dow_analysis

    def analyze_holiday_impact(self) -> Optional[pd.DataFrame]:
        if self.df is None: return None
        daily_sales = self.df.groupby(['date', 'is_holiday'])['total_sales'].sum().reset_index()
        impact = daily_sales.groupby('is_holiday')['total_sales'].mean().reset_index()
        impact['is_holiday'] = impact['is_holiday'].map({True: '공휴일', False: '평일'})
        impact.rename(columns={'total_sales': 'avg_daily_sales'}, inplace=True)
        return impact

    def analyze_weather_impact(self) -> Optional[Dict[str, Any]]:
        if self.df is None or 'weather' not in self.df.columns: return None
        
        daily_weather = self.df.groupby('date').agg(
            daily_total_sales=('total_sales', 'sum'),
            avg_temp=('avg_temp', 'first'),
            weather=('weather', 'first')
        ).reset_index()

        rainy_avg = daily_weather[daily_weather['weather'] == '비']['daily_total_sales'].mean()
        # 데이터가 부족할 경우 nan 대신 0 처리
        correlation = daily_weather['avg_temp'].corr(daily_weather['daily_total_sales'])
        
        return {
            'rainy_day_avg_sales': 0 if np.isnan(rainy_avg) else rainy_avg,
            'temp_sales_correlation': 0 if np.isnan(correlation) else correlation
        }