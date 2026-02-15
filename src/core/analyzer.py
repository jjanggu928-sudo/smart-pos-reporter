# -*- coding: utf-8 -*-
"""
매출 데이터 분석 모듈

이 모듈은 POS 데이터 클라이언트로부터 받은 원본 거래 데이터를 가공하고,
다양한 관점에서 인사이트를 도출하기 위한 핵심 분석 로직을 포함합니다.

주요 클래스:
- SalesAnalyzer: 매출 데이터를 입력받아 요일별, 메뉴별 등 다양한 기준으로
  집계 및 분석을 수행하는 메인 클래스입니다.

기술적 결정:
- pandas 라이브러리 채택: 내부 데이터 처리의 핵심 도구로 pandas를 선택했습니다.
  - 이유 1: 고성능 데이터 구조 (DataFrame): 대용량 데이터를 메모리 내에서 효율적으로 처리하며, 
    강력한 인덱싱, 슬라이싱, 집계 기능을 제공하여 복잡한 분석 로직을 간결하게 표현할 수 있습니다.
  - 이유 2: 벡터화 연산: pandas는 내부적으로 C 또는 Cython으로 구현된 벡터화 연산을 통해,
    순수 Python 반복문에 비해 월등히 빠른 데이터 처리 속도를 보장합니다. 이는 분석 성능의 핵심입니다.
  - 이유 3: 시계열 데이터 처리: `to_datetime`과 같은 강력한 시계열 변환 및 분석 기능을 내장하여,
    거래 시간을 기준으로 요일, 시간대 등 다차원 분석을 용이하게 합니다.
"""

from typing import List, Dict, Any, Optional
import pandas as pd

class SalesAnalyzer:
    """
    매출 데이터를 분석하고 통계를 생성하는 클래스.

    이 클래스는 원본 거래 데이터 리스트를 pandas DataFrame으로 변환하여
    효율적인 데이터 집계 및 분석을 수행합니다.
    """
    def __init__(self, sales_data: List[Dict[str, Any]]):
        """
        SalesAnalyzer를 초기화합니다.

        Args:
            sales_data (List[Dict[str, Any]]): POS 클라이언트로부터 받은 원본 거래 데이터 리스트.
        """
        self.raw_data = sales_data
        self.df: Optional[pd.DataFrame] = self._prepare_dataframe()

    def _prepare_dataframe(self) -> Optional[pd.DataFrame]:
        """
        알고리즘 설명:
        - 원본 데이터(JSON과 유사한 리스트/딕셔너리 구조)는 분석에 비효율적입니다.
        - 이를 행과 열로 구성된 2차원 테이블 형태의 DataFrame으로 변환해야 
          강력한 집계(aggregation) 및 그룹화(grouping) 연산이 가능해집니다.
        - 이 메서드는 'items' 리스트에 중첩된 데이터를 `explode`하여 정규화(Normalization)하고,
          각 거래 항목을 개별 행으로 만듭니다. 이 과정을 통해 메뉴별 분석이 용이해집니다.
        - 시계열 분석을 위해 'timestamp' 문자열을 datetime 객체로 변환하고, 
          이를 기반으로 'day_of_week' 파생 변수를 생성합니다.
        """
        if not self.raw_data:
            print("분석할 데이터가 없습니다.")
            return None
        
        try:
            # 중첩된 item 구조를 정규화하기 위해 pandas의 json_normalize 사용
            df = pd.json_normalize(self.raw_data, record_path='items', meta=['transaction_id', 'timestamp', 'store_id'])

            # 데이터 타입 최적화
            df['price'] = pd.to_numeric(df['price'])
            df['quantity'] = pd.to_numeric(df['quantity'])
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # 총 판매액 컬럼 추가 (벡터화 연산)
            df['total_sales'] = df['price'] * df['quantity']

            # 요일 정보 추가 (0:월요일, 1:화요일, ..., 6:일요일)
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            return df
        except Exception as e:
            print(f"데이터프레임 생성 중 에러 발생: {e}")
            return None

    def aggregate_sales_by_dow(self) -> Optional[pd.DataFrame]:
        """
        요일별 총 매출 및 거래 횟수를 집계합니다.

        알고리즘 설명:
        - `groupby('day_of_week')`: 데이터를 요일별로 그룹화합니다.
        - `agg()`: 여러 집계 함수를 동시에 적용합니다.
          - `total_sales: 'sum'`: 각 그룹(요일)의 총 매출액을 합산합니다.
          - `transaction_id: 'nunique'`: 각 그룹(요일)의 고유한 거래 ID 수를 세어, 
            실질적인 거래 횟수(고객 방문 수)를 계산합니다.
        
        Returns:
            pd.DataFrame: 요일별 분석 결과. 
                          인덱스는 요일(0-6), 컬럼은 'total_sales', 'transaction_count' 입니다.
                          분석 실패 시 None을 반환합니다.
        """
        if self.df is None:
            return None

        dow_analysis = self.df.groupby('day_of_week').agg(
            total_sales=('total_sales', 'sum'),
            transaction_count=('transaction_id', 'nunique')
        ).sort_index()

        # 요일 이름을 한글로 매핑
        day_map = {0: '월', 1: '화', 2: '수', 3: '목', 4: '금', 5: '토', 6: '일'}
        dow_analysis.index = dow_analysis.index.map(day_map)
        
        return dow_analysis

    def aggregate_sales_by_menu(self) -> Optional[pd.DataFrame]:
        """
        메뉴별 총 판매량과 총 매출을 집계합니다.

        알고리즘 설명:
        - `groupby('item_name')`: 데이터를 메뉴 이름별로 그룹화합니다.
        - `agg()`:
          - `quantity: 'sum'`: 각 메뉴의 총 판매 수량을 계산합니다.
          - `total_sales: 'sum'`: 각 메뉴의 총 매출액을 합산합니다.
        - `sort_values()`: 분석 결과의 가독성을 높이기 위해, 가장 많이 팔린 메뉴 순으로 정렬합니다.

        Returns:
            pd.DataFrame: 메뉴별 분석 결과.
                          인덱스는 메뉴명, 컬럼은 'total_quantity', 'total_sales' 입니다.
                          분석 실패 시 None을 반환합니다.
        """
        if self.df is None:
            return None

        menu_analysis = self.df.groupby('item_name').agg(
            total_quantity=('quantity', 'sum'),
            total_sales=('total_sales', 'sum')
        ).sort_values(by='total_quantity', ascending=False)
        
        return menu_analysis

# 사용 예시 (직접 실행 시)
if __name__ == '__main__':
    from src.api.pos_client import MockPOSClient

    # 1. 데이터 로드
    client = MockPOSClient()
    sales_data = client.fetch_weekly_sales_data()

    if sales_data:
        # 2. 분석기 생성
        analyzer = SalesAnalyzer(sales_data)

        if analyzer.df is not None:
            print("\\n===== 요일별 매출 분석 =====\\n")
            dow_result = analyzer.aggregate_sales_by_dow()
            print(dow_result)

            print("\\n\\n===== 메뉴별 판매 분석 =====\\n")
            menu_result = analyzer.aggregate_sales_by_menu()
            print(menu_result)
        else:
            print("분석기 초기화에 실패했습니다.")
