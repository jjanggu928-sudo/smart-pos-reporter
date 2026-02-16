# -*- coding: utf-8 -*-
import json
import random
import pandas as pd
from datetime import datetime, timedelta
import holidays

# --- 1. 기본 설정 ---

YEAR = 2025
OUTPUT_FILE = 'data/mock_pos_data.json'
KR_HOLIDAYS = holidays.KR(years=YEAR)
MAJOR_HOLIDAYS = {
    datetime(YEAR, 1, 1).date(): 3.0,   # 신정
    datetime(YEAR, 1, 28).date(): 4.0,  # 설날
    datetime(YEAR, 1, 29).date(): 4.0,  # 설날
    datetime(YEAR, 1, 30).date(): 4.0,  # 설날
    datetime(YEAR, 5, 5).date(): 3.5,   # 어린이날
    datetime(YEAR, 10, 5).date(): 4.0, # 추석
    datetime(YEAR, 10, 6).date(): 4.0, # 추석
    datetime(YEAR, 10, 7).date(): 4.0, # 추석
    datetime(YEAR, 12, 25).date(): 4.5, # 크리스마스
}

MENU_ITEMS = [
    # 커피 (HOT/ICE)
    {"name": "아메리카노 (HOT)", "price": 4000, "category": "hot"},
    {"name": "카페라떼 (HOT)", "price": 4500, "category": "hot"},
    {"name": "바닐라 라떼 (HOT)", "price": 5000, "category": "hot"},
    {"name": "아메리카노 (ICE)", "price": 4500, "category": "ice"},
    {"name": "카페라떼 (ICE)", "price": 5000, "category": "ice"},
    {"name": "바닐라 라떼 (ICE)", "price": 5500, "category": "ice"},
    # 음료 & 디저트
    {"name": "레몬에이드", "price": 5500, "category": "beverage"},
    {"name": "자몽에이드", "price": 5500, "category": "beverage"},
    {"name": "치즈케이크", "price": 6000, "category": "dessert"},
    {"name": "초코케이크", "price": 6500, "category": "dessert"},
    # 특별 메뉴
    {"name": "해물파전", "price": 15000, "category": "special"},
    {"name": "뱅쇼", "price": 7000, "category": "special_hot"},
]

# --- 2. 데이터 생성 함수 ---

def get_menu_weights(day: pd.Timestamp, weather: str) -> list[float]:
    """
    날짜와 날씨에 따라 메뉴별 판매 가중치를 동적으로 조절합니다.
    """
    weights = [1.0] * len(MENU_ITEMS)
    month = day.month
    
    for i, item in enumerate(MENU_ITEMS):
        # 계절성: 여름(6-8월)
        if 6 <= month <= 8:
            if item['category'] == 'ice': weights[i] *= 2.5
            if item['category'] == 'hot': weights[i] *= 0.5
        
        # 계절성: 겨울(11-2월)
        if month in [11, 12, 1, 2]:
            if item['category'] == 'hot': weights[i] *= 2.0
            if item['category'] == 'dessert': weights[i] *= 1.5
            if item['name'] == '뱅쇼': weights[i] *= 3.0

        # 날씨: 비 오는 날
        if weather == '비':
            if item['name'] == '해물파전': weights[i] *= 5.0
            if item['category'] == 'hot': weights[i] *= 1.8
    
    return weights


def generate_mock_data():
    """
    1년치 가상 매출 데이터를 생성하여 JSON 파일로 저장합니다.
    """
    print(f"{YEAR}년 가상 매출 데이터 생성을 시작합니다...")
    all_transactions = []
    transaction_id_counter = 1
    
    date_range = pd.date_range(start=f'{YEAR}-01-01', end=f'{YEAR}-12-31')

    for day in date_range:
        # 하루의 특성 결정
        is_weekend = day.dayofweek >= 5  # 토, 일
        is_holiday = day.date() in KR_HOLIDAYS
        weather = random.choices(['맑음', '흐림', '비'], weights=[0.7, 0.2, 0.1], k=1)[0]

        # 하루 거래량 결정
        base_transactions = random.randint(10, 30)
        multiplier = 1.0
        if day.date() in MAJOR_HOLIDAYS:
            multiplier = MAJOR_HOLIDAYS[day.date()]
        elif is_holiday:
            multiplier = 2.0
        elif is_weekend:
            multiplier = 1.5
        
        num_transactions = int(base_transactions * multiplier)

        # 메뉴 가중치 설정
        menu_weights = get_menu_weights(day, weather)

        # 거래 데이터 생성
        for _ in range(num_transactions):
            num_items_in_transaction = random.randint(1, 4)
            items_for_transaction = random.choices(MENU_ITEMS, weights=menu_weights, k=num_items_in_transaction)
            
            transaction_time = day + timedelta(hours=random.randint(9, 22), minutes=random.randint(0, 59))
            
            transaction_record = {
                "transaction_id": f"T{transaction_id_counter:06d}",
                "timestamp": transaction_time.isoformat(),
                "store_id": "STORE_001",
                "items": [
                    {
                        "item_name": item["name"],
                        "price": item["price"],
                        "quantity": 1 # 편의상 수량은 1로 고정
                    } for item in items_for_transaction
                ]
            }
            all_transactions.append(transaction_record)
            transaction_id_counter += 1

    print(f"총 {len(all_transactions)}개의 거래 내역을 생성했습니다.")

    # 파일 저장
    print(f"'{OUTPUT_FILE}' 파일로 저장합니다...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_transactions, f, ensure_ascii=False, indent=2)
    
    print("데이터 생성이 완료되었습니다.")


if __name__ == '__main__':
    generate_mock_data()
