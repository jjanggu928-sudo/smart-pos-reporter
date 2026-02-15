# -*- coding: utf-8 -*-
"""
데이터 마이그레이션 스크립트

로컬 mock_pos_data.json 파일의 데이터를 읽어,
Supabase에 생성된 테이블로 이전하는 일회성 스크립트입니다.

실행 전 확인사항:
- .env 파일에 Supabase URL과 Key가 올바르게 설정되어 있어야 합니다.
- `pip install -r requirements.txt`를 통해 supabase, python-dotenv 라이브러리가 설치되어 있어야 합니다.

스크립트 로직:
1. 환경 변수 로드 및 Supabase 클라이언트 초기화
2. mock_pos_data.json 파일 로드
3. 중복을 제거한 stores, menu_items 데이터를 추출하여 DB에 'upsert'
   (Upsert: 데이터가 없으면 INSERT, 있으면 UPDATE. 스크립트를 여러 번 실행해도 안전하도록 보장)
4. DB에 저장된 menu_items를 다시 불러와 '메뉴이름: ID' 맵 생성 (효율적인 조회를 위함)
5. transactions 및 transaction_items 데이터를 DB에 'insert'
"""
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

def migrate():
    """데이터 마이그레이션 메인 함수"""
    # 1. Supabase 클라이언트 초기화
    print("환경 변수를 로드하고 Supabase 클라이언트를 초기화합니다...")
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("에러: .env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY가 설정되지 않았습니다.")
        return

    supabase: Client = create_client(url, key)
    print("Supabase 클라이언트 초기화 완료.")

    # 2. JSON 데이터 로드
    try:
        with open('data/mock_pos_data.json', 'r', encoding='utf-8') as f:
            sales_data = json.load(f)
        print("mock_pos_data.json 파일 로드 완료.")
    except FileNotFoundError:
        print("에러: data/mock_pos_data.json 파일을 찾을 수 없습니다.")
        return

    # 3. Stores 및 Menu Items 데이터 추출 및 Upsert
    stores_to_upsert = set()
    menu_items_to_upsert = {}

    for record in sales_data:
        stores_to_upsert.add(record['store_id'])
        for item in record['items']:
            if item['item_name'] not in menu_items_to_upsert:
                menu_items_to_upsert[item['item_name']] = {
                    "name": item['item_name'],
                    "price": item['price']
                }
    
    # Stores 데이터 Upsert
    print(f"\n{len(stores_to_upsert)}개의 매장 정보를 DB에 저장합니다...")
    stores_list = [{"id": store_id, "name": f"Store {store_id}"} for store_id in stores_to_upsert]
    try:
        supabase.table('stores').upsert(stores_list).execute()
        print("매장 정보 저장 완료.")
    except Exception as e:
        print(f"매장 정보 저장 중 에러 발생: {e}")

    # Menu Items 데이터 Upsert
    print(f"{len(menu_items_to_upsert)}개의 메뉴 정보를 DB에 저장합니다...")
    try:
        supabase.table('menu_items').upsert(list(menu_items_to_upsert.values())).execute()
        print("메뉴 정보 저장 완료.")
    except Exception as e:
        print(f"메뉴 정보 저장 중 에러 발생: {e}")


    # 4. 메뉴 이름 <-> ID 맵 생성
    print("\nDB로부터 메뉴 ID를 조회하여 맵을 생성합니다...")
    try:
        menu_items_from_db = supabase.table('menu_items').select("id, name").execute().data
        menu_name_to_id = {item['name']: item['id'] for item in menu_items_from_db}
        print("메뉴 맵 생성 완료.")
    except Exception as e:
        print(f"메뉴 ID 조회 중 에러 발생: {e}")
        return

    # 5. Transactions 및 Transaction Items 데이터 Insert
    transactions_to_insert = []
    transaction_items_to_insert = []

    for record in sales_data:
        transactions_to_insert.append({
            "id": record['transaction_id'],
            "store_id": record['store_id'],
            "created_at": record['timestamp']
        })
        for item in record['items']:
            menu_id = menu_name_to_id.get(item['item_name'])
            if menu_id:
                transaction_items_to_insert.append({
                    "transaction_id": record['transaction_id'],
                    "menu_item_id": menu_id,
                    "quantity": item['quantity']
                })

    # Transactions 데이터 Insert
    print(f"\n{len(transactions_to_insert)}개의 거래 내역을 DB에 저장합니다...")
    try:
        supabase.table('transactions').insert(transactions_to_insert).execute()
        print("거래 내역 저장 완료.")
    except Exception as e:
        # P0001: raising_exception (중복 키 에러 코드와 유사)
        if 'duplicate key value' in str(e):
             print("이미 저장된 거래 내역이 있어 건너뜁니다.")
        else:
             print(f"거래 내역 저장 중 에러 발생: {e}")

    # Transaction Items 데이터 Insert
    print(f"{len(transaction_items_to_insert)}개의 판매 항목을 DB에 저장합니다...")
    try:
        supabase.table('transaction_items').insert(transaction_items_to_insert).execute()
        print("판매 항목 저장 완료.")
    except Exception as e:
        if 'duplicate key value' in str(e):
             print("이미 저장된 판매 항목이 있어 건너뜁니다.")
        else:
            print(f"판매 항목 저장 중 에러 발생: {e}")

    print("\n✅ 데이터 마이그레이션이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    migrate()
