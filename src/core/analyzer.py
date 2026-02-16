# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import holidays
from typing import List, Dict, Any, Optional
import random

class SalesAnalyzer:
    """
    매출 및 외부 요인(날씨, 공휴일)을 종합적으로 분석하는 클래스.
    단순 매출 집계를 넘어, 데이터 보강(Data Enrichment)을 통해
    매출에 영향을 미치는 잠재적 변수를 함께 분석하여 데이터 기반 의사결정의 질을 높입니다.
    """
    def __init__(self, sales_data: List[Dict[str, Any]], year: int = 2026):
        self.raw_data = sales_data
        self.year = year
        self.df: Optional[pd.DataFrame] = self._prepare_dataframe()

        if self.df is not None:
            # --- 데이터 보강(Data Enrichment) 파이프라인 ---
            # 기술 증빙: 초기 데이터프레임 생성 후, 비즈니스에 영향을 줄 수 있는
            # 외부 데이터를 순차적으로 병합합니다. 이 파이프라인은 데이터의 가치를
            # 증대시키는 핵심 과정입니다.
            self.df = self._add_holiday_flag(self.df)
            self.df = self._generate_and_merge_weather_data(self.df)

    def _prepare_dataframe(self) -> Optional[pd.DataFrame]:
        # ... (기존과 동일, 변경 없음) ...
        if not self.raw_data:
            return None
        try:
            df = pd.json_normalize(self.raw_data, record_path='items', meta=['transaction_id', 'timestamp', 'store_id'])
            df['price'] = pd.to_numeric(df['price'])
            df['quantity'] = pd.to_numeric(df['quantity'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['total_sales'] = df['price'] * df['quantity']
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            return df
        except Exception as e:
            print(f"데이터프레임 생성 중 에러 발생: {e}")
            return None

    def _add_holiday_flag(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [데이터 보강] 공휴일 변수 추가

        알고리즘 설명:
        - `holidays` 라이브러리를 사용하여 특정 국가(대한민국) 및 연도의 공휴일 정보를 가져옵니다.
        - DataFrame의 각 날짜가 공휴일 집합에 포함되는지 여부를 확인하여 'is_holiday' 컬럼(True/False)을 추가합니다.
        
        데이터 기반 의사결정 기여 방안:
        - 휴일과 평일의 매출 패턴 차이 분석 -> 휴일 특별 프로모션, 한정 메뉴 출시 등 전략 수립의 근거.
        - 휴일 종류(예: 명절, 일반 공휴일)에 따른 고객 방문 및 소비 패턴 분석 -> 맞춤형 마케팅 실행.
        """
        kr_holidays = holidays.KR(years=self.year)
        df['date'] = df['timestamp'].dt.date
        df['is_holiday'] = df['date'].apply(lambda x: x in kr_holidays)
        return df

    def _generate_and_merge_weather_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [데이터 보강] 가상 날씨 데이터 생성 및 결합

        알고리즘 설명:
        - 분석 대상 기간(2월)에 대한 가상의 일별 날씨 데이터를 생성합니다.
          - 날씨 상태('맑음', '비', '눈'): 현실성을 고려하여 발생 확률에 가중치를 부여합니다.
          - 평균 기온: 한국 2월의 실제 기온 분포를 고려하여 -5°C ~ 10°C 사이의 값을 균등 분포로 생성합니다.
        - 생성된 날씨 데이터를 기존 DataFrame에 날짜를 기준으로 병합('merge')합니다.

        데이터 기반 의사결정 기여 방안:
        - 날씨-매출 상관관계 분석: 특정 날씨(예: 비, 눈)에 잘 팔리는 메뉴(예: 따뜻한 음료, 국물 요리) 파악 -> 수요 예측 및 재고 관리 최적화.
        - 기온-매출 상관관계 분석: 기온 변화에 따른 아이스/핫 메뉴 판매량 변화 분석 -> 메뉴판 구성 및 프로모션 시기 조절.
        """
        start_date = f'{self.year}-02-01'
        end_date = f'{self.year}-02-28'
        dates = pd.to_datetime(pd.date_range(start_date, end_date))
        
        weather_conditions = ['맑음', '비', '눈']
        # 현실성을 위해 '맑음'에 높은 확률 부여
        weather_data = [random.choices(weather_conditions, weights=[0.7, 0.2, 0.1], k=1)[0] for _ in dates]
        
        # 한국 2월 기온을 가정한 -5 ~ 10도 사이의 랜덤 기온 생성
        temp_data = np.random.uniform(-5, 10, size=len(dates))
        
        weather_df = pd.DataFrame({
            'date': dates.date,
            'weather': weather_data,
            'avg_temp': temp_data
        })
        
        # 기존 df와 날씨 df를 'date' 기준으로 병합
        merged_df = pd.merge(df, weather_df, on='date', how='left')
        return merged_df

    def aggregate_sales_by_dow(self) -> Optional[pd.DataFrame]:
        # ... (기존과 동일, 변경 없음) ...
        if self.df is None: return None
        dow_analysis = self.df.groupby('day_of_week').agg(total_sales=('total_sales', 'sum'), transaction_count=('transaction_id', 'nunique')).sort_index()
        day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        dow_analysis.index = dow_analysis.index.map(day_map)
        return dow_analysis

    def aggregate_sales_by_menu(self) -> Optional[pd.DataFrame]:
        # ... (기존과 동일, 변경 없음) ...
        if self.df is None: return None
        menu_analysis = self.df.groupby('item_name').agg(total_quantity=('quantity', 'sum'), total_sales=('total_sales', 'sum')).sort_values(by='total_quantity', ascending=False)
        return menu_analysis

    def analyze_holiday_impact(self) -> Optional[pd.DataFrame]:
        """
        공휴일과 평일의 평균 일 매출을 비교 분석합니다.
        """
        if self.df is None or 'is_holiday' not in self.df.columns:
            return None
        
        # 일별 총 매출 계산
        daily_sales = self.df.groupby(['date', 'is_holiday'])['total_sales'].sum().reset_index()
        
        # 공휴일/평일별 평균 일 매출 계산
        holiday_impact = daily_sales.groupby('is_holiday')['total_sales'].mean().reset_index()
        holiday_impact['is_holiday'] = holiday_impact['is_holiday'].map({True: '공휴일', False: '평일'})
        holiday_impact.rename(columns={'total_sales': 'avg_daily_sales'}, inplace=True)
        
        return holiday_impact

    def analyze_weather_impact(self) -> Optional[Dict[str, Any]]:
        """
        날씨(기상 상태, 기온)가 매출에 미치는 영향을 분석합니다.
        - 우천 시 평균 일 매출
        - 기온과 일 매출 간의 상관 계수
        """
        if self.df is None or 'weather' not in self.df.columns or 'avg_temp' not in self.df.columns:
            return None
            
        # 일별 총 매출 및 평균 기온 계산
        daily_sales_weather = self.df.groupby('date').agg(
            daily_total_sales=('total_sales', 'sum'),
            avg_temp=('avg_temp', 'first'), # 일별 평균 기온은 동일
            weather=('weather', 'first') # 일별 날씨는 동일
        ).reset_index()

        # 1. 우천 시 평균 매출
        rainy_day_sales = daily_sales_weather[daily_sales_weather['weather'] == '비']
        rainy_day_avg = rainy_day_sales['daily_total_sales'].mean()

        # 2. 기온과 매출의 상관관계 (피어슨 상관계수)
        temp_sales_correlation = daily_sales_weather['avg_temp'].corr(daily_sales_weather['daily_total_sales'])
        
        return {
            'rainy_day_avg_sales': rainy_day_avg,
            'temp_sales_correlation': temp_sales_correlation
        }

if __name__ == '__main__':
    # ... (직접 실행 예시 코드 - 필요 시 여기에 새 분석 함수 호출 추가 가능) ...
    pass