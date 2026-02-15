# -*- coding: utf-8 -*-
import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

def migrate():
    """데이터 마이그레이션 메인 함수"""
    print("환경 변수를 로드하고 Supabase 클라이언트를 초기화합니다...")
    load_dotenv()
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("에러: .env 파일에 SUPABASE_URL과 SUPABASE_ANON_KEY가 설정되지 않았습니다.")
        return

    supabase: Client = create_client(url, key)
    print("Supabase 클라이언트 초기화 완료.")

    # --- [수정됨] 데이터 삭제 로직 보완 ---
    print("\n[주의] 기존 데이터 삭제를 시작합니다. 이 작업은 되돌릴 수 없습니다.")
    # 외래 키 제약조건을 고려하여 역순으로 삭제
    tables_to_delete = ['transaction_items', 'transactions', 'stores', 'menu_items']
    for table_name in tables_to_delete:
        try:
            print(f"'{table_name}' 테이블의 데이터를 삭제합니다...")
            # id가 -1이 아닌 모든 데이터를 삭제 (숫자/문자 ID 모두에 안전하게 적용)
            supabase.table(table_name).delete().neq('id', -99999).execute()
            print(f"'{table_name}' 테이블 데이터 삭제 완료.")
        except Exception as e:
            print(f"'{table_name}' 테이블 데이터 삭제 중 에러 발생: {e}")
            print("스크립트를 중단합니다. Supabase 대시보드에서 테이블 스키마를 확인해주세요.")
            return # 삭제 실패 시 더 이상 진행하지 않음
    print("기존 데이터 삭제 완료.")
    # --- 데이터 삭제 로직 끝 ---

    try:
        with open('data/mock_pos_data.json', 'r', encoding='utf-8') as f:
            sales_data = json.load(f)
        print("\n'mock_pos_data.json' 파일 로드 완료.")
    except FileNotFoundError:
        print("에러: 'data/mock_pos_data.json' 파일을 찾을 수 없습니다.")
        return

    stores_to_upsert = set()
    menu_items_to_upsert = {}

    for record in sales_data:
        stores_to_upsert.add(record['store_id'])
        for item in record['items']:
            if item['item_name'] not in menu_items_to_upsert:
                menu_items_to_upsert[item['item_name']] = {"name": item['item_name'], "price": item['price']}
    
    print(f"\n{len(stores_to_upsert)}개의 매장 정보를 DB에 저장(Upsert)합니다...")
    stores_list = [{"id": store_id, "name": f"Store {store_id}"} for store_id in stores_to_upsert]
    supabase.table('stores').upsert(stores_list).execute()
    print("매장 정보 저장 완료.")

    print(f"{len(menu_items_to_upsert)}개의 메뉴 정보를 DB에 저장(Upsert)합니다...")
    supabase.table('menu_items').upsert(list(menu_items_to_upsert.values())).execute()
    print("메뉴 정보 저장 완료.")

    print("\nDB로부터 메뉴 ID를 조회하여 맵을 생성합니다...")
    menu_items_from_db = supabase.table('menu_items').select("id, name").execute().data
    menu_name_to_id = {item['name']: item['id'] for item in menu_items_from_db}
    print("메뉴 맵 생성 완료.")

    transactions_to_insert = []
    transaction_items_to_insert = []
    
    # 중복 거래 항목을 방지하기 위한 집합
    processed_transaction_items = set()

    for record in sales_data:
        transactions_to_insert.append({"id": record['transaction_id'], "store_id": record['store_id'], "created_at": record['timestamp']})
        for item in record['items']:
            menu_id = menu_name_to_id.get(item['item_name'])
            # 복합키 (transaction_id, menu_id)
            item_key = (record['transaction_id'], menu_id)
            if menu_id and item_key not in processed_transaction_items:
                transaction_items_to_insert.append({"transaction_id": record['transaction_id'], "menu_item_id": menu_id, "quantity": item['quantity']})
                processed_transaction_items.add(item_key)

    # 데이터를 작은 chunk로 나누어 insert
    def batch_insert(table_name, data, chunk_size=500):
        print(f"\n{len(data)}개의 {table_name} 데이터를 DB에 저장(Insert)합니다...")
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            try:
                supabase.table(table_name).insert(chunk).execute()
                print(f"  - {table_name} chunk {i//chunk_size + 1} 저장 완료.")
            except Exception as e:
                print(f"  - {table_name} chunk {i//chunk_size + 1} 저장 중 에러 발생: {e}")
        print(f"{table_name} 데이터 저장 완료.")
    
    batch_insert('transactions', transactions_to_insert)
    batch_insert('transaction_items', transaction_items_to_insert)

    print("\n[SUCCESS] 데이터 마이그레이션이 성공적으로 완료되었습니다!")

if __name__ == "__main__":
    migrate()
