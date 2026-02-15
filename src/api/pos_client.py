# -*- coding: utf-8 -*-
"""
POS 데이터 클라이언트 모듈

이 모듈은 POS 시스템의 매출 데이터를 가져오기 위한 클라이언트 인터페이스와 구현체를 제공합니다.
현재는 Mock 클라이언트만 존재하지만, 향후 실제 API와 연동되는 클라이언트로 쉽게 확장할 수 있도록
추상 기본 클래스(Abstract Base Class)를 기반으로 설계되었습니다.

- BasePOSClient: 모든 POS 데이터 클라이언트가 준수해야 하는 인터페이스를 정의합니다.
- MockPOSClient: 로컬 JSON 파일에서 데이터를 읽어오는 Mock 구현체입니다.

기술적 결정:
- ABC(Abstract Base Class) 사용: 클라이언트의 교체 가능성(swappable)을 보장하고, 
  시스템의 다른 부분에 영향을 주지 않고 데이터 소스를 변경할 수 있는 유연성을 제공합니다.
  이는 '개방-폐쇄 원칙(OCP)'을 따르는 설계로, 기능 확장에 열려있고, 수정에는 닫혀있는 구조를 지향합니다.
"""
import json
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BasePOSClient(ABC):
    """
    POS 데이터 클라이언트의 기본 인터페이스를 정의하는 추상 클래스.

    모든 POS 클라이언트는 이 클래스를 상속받아 `fetch_weekly_sales_data` 메서드를 구현해야 합니다.
    """
    @abstractmethod
    def fetch_weekly_sales_data(self) -> List[Dict[str, Any]]:
        """
        일주일간의 모든 매출 거래 데이터를 가져옵니다.

        Returns:
            List[Dict[str, Any]]: 거래 데이터 리스트. 각 요소는 하나의 거래를 나타내는 딕셔너리입니다.
                                  데이터가 없거나 오류 발생 시 빈 리스트를 반환할 수 있습니다.
        """
        pass

class MockPOSClient(BasePOSClient):
    """
    로컬 JSON 파일로부터 POS 데이터를 읽어오는 Mock 클라이언트.

    주어진 파일 경로에서 JSON 데이터를 로드하여 반환합니다. 실제 API가 개발되기 전,
    개발 및 테스트 단계에서 사용하기 위한 구현체입니다.
    """
    def __init__(self, file_path: str = "data/mock_pos_data.json"):
        """
        MockPOSClient 초기화.

        Args:
            file_path (str): 읽어올 Mock 데이터 JSON 파일의 경로.
        """
        self.file_path = file_path

    def fetch_weekly_sales_data(self) -> List[Dict[str, Any]]:
        """
        지정된 경로의 JSON 파일에서 매출 데이터를 읽어옵니다.

        파일이 존재하지 않거나 JSON 파싱에 실패할 경우, 상세한 에러 로그를 남기고
        시스템의 안정성을 위해 빈 리스트를 반환합니다.

        Returns:
            List[Dict[str, Any]]: 파일에서 성공적으로 읽어온 거래 데이터 리스트.
        
        Raises:
            FileNotFoundError: 파일 경로가 잘못되었을 경우 발생할 수 있습니다. (내부 처리)
            json.JSONDecodeError: 파일 내용이 유효한 JSON 형식이 아닐 경우 발생할 수 있습니다. (내부 처리)
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # print(f"Successfully loaded {len(data)} records from {self.file_path}") # 디버깅용
            return data
        except FileNotFoundError:
            print(f"에러: Mock 데이터 파일을 찾을 수 없습니다. 경로: {self.file_path}")
            return []
        except json.JSONDecodeError:
            print(f"에러: Mock 데이터 파일의 JSON 형식이 올바르지 않습니다. 파일: {self.file_path}")
            return []
        except Exception as e:
            print(f"데이터 로딩 중 예기치 않은 에러가 발생했습니다: {e}")
            return []

# 사용 예시 (직접 실행 시)
if __name__ == '__main__':
    # Mock 클라이언트 생성 및 데이터 로드 테스트
    mock_client = MockPOSClient()
    sales_data = mock_client.fetch_weekly_sales_data()

    if sales_data:
        print("===== Mock POS 데이터 로드 성공 =====")
        print(f"총 {len(sales_data)}개의 거래 내역을 불러왔습니다.")
        print("첫 번째 거래 데이터:")
        # Pretty print the first transaction
        print(json.dumps(sales_data[0], indent=2, ensure_ascii=False))
    else:
        print("===== Mock POS 데이터 로드 실패 =====")
