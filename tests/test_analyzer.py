# -*- coding: utf-8 -*-
"""
SalesAnalyzer 유닛 테스트 모듈

이 모듈은 `src.core.analyzer.SalesAnalyzer` 클래스의 기능이
정확하고 안정적으로 동작하는지 검증하는 단위 테스트를 포함합니다.

테스트 원칙:
- 격리(Isolation): 각 테스트는 다른 테스트에 영향을 주지 않고 독립적으로 실행됩니다.
- 제어된 환경(Controlled Environment): 외부 파일(`mock_pos_data.json`)에 의존하지 않고,
  테스트 케이스 내에서 직접 정의한 작은 규모의 예측 가능한 Mock 데이터를 사용합니다.
  이를 통해 결과의 일관성을 보장합니다.
- 완전성(Completeness): 정상적인 시나리오(Happy Path)뿐만 아니라,
  비정상적인 입력(빈 데이터 등)에 대한 엣지 케이스(Edge Case) 처리 능력도 검증합니다.
"""
import unittest
import pandas as pd

from src.core.analyzer import SalesAnalyzer

class TestSalesAnalyzer(unittest.TestCase):
    """`SalesAnalyzer` 클래스에 대한 테스트 스위트."""

    @classmethod
    def setUpClass(cls):
        """테스트 전체에서 사용할 공통 데이터셋을 한 번만 설정합니다."""
        cls.mock_sales_data = [
            {
                "transaction_id": "T01", "timestamp": "2026-02-09T10:00:00Z", "store_id": "S01", # 월요일
                "items": [
                    {"item_name": "아메리카노", "price": 4000, "quantity": 2}, # 8000
                    {"item_name": "카페라떼", "price": 5000, "quantity": 1},  # 5000
                ]
            },
            {
                "transaction_id": "T02", "timestamp": "2026-02-10T14:00:00Z", "store_id": "S01", # 화요일
                "items": [
                    {"item_name": "아메리카노", "price": 4000, "quantity": 1}  # 4000
                ]
            },
            {
                "transaction_id": "T03", "timestamp": "2026-02-09T15:00:00Z", "store_id": "S02", # 월요일
                "items": [
                    {"item_name": "치즈케이크", "price": 6000, "quantity": 1}, # 6000
                    {"item_name": "아메리카노", "price": 4000, "quantity": 1}, # 4000
                ]
            }
        ]
        
        cls.analyzer_with_data = SalesAnalyzer(cls.mock_sales_data)
        cls.analyzer_empty = SalesAnalyzer([])

    def test_initialization_with_data(self):
        """데이터가 있을 때 SalesAnalyzer가 정상적으로 초기화되는지 테스트합니다."""
        self.assertIsNotNone(self.analyzer_with_data)
        self.assertIsInstance(self.analyzer_with_data.df, pd.DataFrame)
        self.assertFalse(self.analyzer_with_data.df.empty)

    def test_initialization_with_empty_data(self):
        """빈 데이터로 초기화할 때를 정상적으로 처리하는지 테스트합니다."""
        self.assertIsNotNone(self.analyzer_empty)
        self.assertIsNone(self.analyzer_empty.df)

    def test_prepare_dataframe(self):
        """데이터 전처리(_prepare_dataframe)가 정확하게 수행되는지 테스트합니다."""
        df = self.analyzer_with_data.df
        
        # 1. 예상 컬럼 존재 여부 확인
        expected_columns = ['item_name', 'price', 'quantity', 'transaction_id', 'timestamp', 'store_id', 'total_sales', 'day_of_week']
        self.assertCountEqual(df.columns, expected_columns)

        # 2. 아이템 기준으로 row가 정상적으로 분리(explode)되었는지 확인
        self.assertEqual(len(df), 5) # 3개의 거래, 총 5개의 아이템

        # 3. total_sales (가격 * 수량) 계산 정확성 확인
        # T01의 아메리카노(2개)
        expected_total = 4000 * 2
        actual_total = df[(df['transaction_id'] == 'T01') & (df['item_name'] == '아메리카노')]['total_sales'].iloc[0]
        self.assertEqual(actual_total, expected_total)

        # 4. day_of_week (요일) 계산 정확성 확인 (월요일=0, 화요일=1)
        # T01, T03은 월요일(0) / T02는 화요일(1)
        self.assertEqual(df[df['transaction_id'] == 'T01']['day_of_week'].iloc[0], 0)
        self.assertEqual(df[df['transaction_id'] == 'T03']['day_of_week'].iloc[0], 0)
        self.assertEqual(df[df['transaction_id'] == 'T02']['day_of_week'].iloc[0], 1)

    def test_aggregate_sales_by_dow(self):
        """요일별 집계(aggregate_sales_by_dow) 기능의 정확성을 테스트합니다."""
        dow_result = self.analyzer_with_data.aggregate_sales_by_dow()
        
        # 데이터: 월(T01, T03) = 13000 + 10000 = 23000, 화(T02) = 4000
        # 거래수: 월(2), 화(1)
        self.assertAlmostEqual(dow_result.loc['월', 'total_sales'], 23000)
        self.assertEqual(dow_result.loc['월', 'transaction_count'], 2)
        
        self.assertAlmostEqual(dow_result.loc['화', 'total_sales'], 4000)
        self.assertEqual(dow_result.loc['화', 'transaction_count'], 1)

    def test_aggregate_sales_by_menu(self):
        """메뉴별 집계(aggregate_sales_by_menu) 기능의 정확성을 테스트합니다."""
        menu_result = self.analyzer_with_data.aggregate_sales_by_menu()

        # 데이터:
        # 아메리카노: 4개, 16000
        # 카페라떼: 1개, 5000
        # 치즈케이크: 1개, 6000
        self.assertEqual(menu_result.loc['아메리카노', 'total_quantity'], 4)
        self.assertAlmostEqual(menu_result.loc['아메리카노', 'total_sales'], 16000)
        
        self.assertEqual(menu_result.loc['카페라떼', 'total_quantity'], 1)
        self.assertAlmostEqual(menu_result.loc['카페라떼', 'total_sales'], 5000)

        self.assertEqual(menu_result.loc['치즈케이크', 'total_quantity'], 1)
        self.assertAlmostEqual(menu_result.loc['치즈케이크', 'total_sales'], 6000)

        # 정렬 순서 확인 (total_quantity 기준 내림차순)
        self.assertEqual(menu_result.index.tolist(), ['아메리카노', '치즈케이크', '카페라떼'])

if __name__ == '__main__':
    # 테스트 실행
    unittest.main()
