# -*- coding: utf-8 -*-
"""
Supabase 데이터 클라이언트 모듈

이 모듈은 Supabase 데이터베이스로부터 POS 데이터를 가져오는 클라이언트를 구현합니다.
기존의 `BasePOSClient` 인터페이스를 상속받아, 데이터 소스가 파일에서 DB로 변경되어도
시스템의 다른 부분(예: SalesAnalyzer)은 영향을 받지 않도록 합니다.
"""
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from supabase import create_client, Client

# BasePOSClient 인터페이스를 가져오기 위해 import
from .pos_client import BasePOSClient

class SupabasePOSClient(BasePOSClient):
    """
    Supabase 데이터베이스로부터 POS 데이터를 조회하는 클라이언트.
    """
    def __init__(self):
        """
        SupabasePOSClient를 초기화하고 DB 연결을 설정합니다.
        .env 파일로부터 접속 정보를 로드합니다.
        """
        load_dotenv()
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("Supabase URL과 Key가 .env 파일에 설정되지 않았습니다.")

        self.supabase: Client = create_client(url, key)

    def fetch_weekly_sales_data(self) -> List[Dict[str, Any]]:
        """
        Supabase DB에서 일주일간의 모든 매출 거래 데이터를 가져옵니다.

        기술적 결정:
        - PostgREST 쿼리 최적화: Supabase는 내부적으로 PostgREST를 사용하여 테이블을 API로 제공합니다.
          `select()` 메소드에서 중첩된 형태로 관계(join)를 명시하면, 
          DB단에서 모든 데이터가 조합된 후 단일 요청으로 결과를 반환받을 수 있습니다.
          이는 여러 테이블의 데이터를 가져오기 위해 여러 번의 API 요청을 보내는 방식(N+1 문제)에 비해
          네트워크 오버헤드가 월등히 적어, 애플리케이션의 응답 속도를 크게 향상시킵니다.
        
        쿼리 설명:
        - `transactions(*, ...)`: transactions 테이블의 모든 컬럼을 선택합니다.
        - `transaction_items(*, ...)`: 각 transaction에 연결된 transaction_items를 모두 가져옵니다.
        - `menu_items(name, price)`: 각 transaction_item에 연결된 menu_item의 이름과 가격을 가져옵니다.

        Returns:
            List[Dict[str, Any]]: SalesAnalyzer가 이해할 수 있는 표준 포맷으로 변환된 거래 데이터 리스트.
        """
        try:
            # Supabase의 PostgREST 기능을 활용한 한번의 쿼리로 모든 관련 데이터 로드
            query_result = self.supabase.table('transactions').select(
                'id, created_at, store_id, transaction_items(quantity, menu_items(name, price))'
            ).execute().data
            
            # SalesAnalyzer가 사용하는 표준 포맷으로 데이터 구조를 변환
            formatted_data = []
            for record in query_result:
                formatted_record = {
                    "transaction_id": record['id'],
                    "timestamp": record['created_at'],
                    "store_id": record['store_id'],
                    "items": [
                        {
                            "item_name": item['menu_items']['name'],
                            "price": item['menu_items']['price'],
                            "quantity": item['quantity']
                        }
                        for item in record.get('transaction_items', []) if item.get('menu_items')
                    ]
                }
                formatted_data.append(formatted_record)
            
            return formatted_data

        except Exception as e:
            print(f"Supabase 데이터 조회 중 에러 발생: {e}")
            return []

# 사용 예시 (직접 실행 시)
if __name__ == '__main__':
    try:
        print("Supabase 클라이언트를 통해 데이터를 조회합니다...")
        supabase_client = SupabasePOSClient()
        weekly_sales = supabase_client.fetch_weekly_sales_data()

        if weekly_sales:
            print(f"\n✅ 성공적으로 {len(weekly_sales)}개의 거래 내역을 불러왔습니다.")
            print("\n첫 번째 거래 데이터:")
            # Pretty print the first transaction
            import json
            print(json.dumps(weekly_sales[0], indent=2, ensure_ascii=False))
        else:
            print("\n❌ 데이터를 불러오지 못했습니다. DB 연결 또는 데이터를 확인해주세요.")
            
    except ValueError as e:
        print(f"에러: {e}")
    except Exception as e:
        print(f"예기치 않은 에러 발생: {e}")
