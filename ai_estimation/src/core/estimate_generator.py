#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 견적 생성기
OpenAI API를 활용하여 프로젝트 견적을 자동으로 생성하는 모듈입니다.
"""

import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import openpyxl

class EstimateGenerator:
    """
    AI 견적 생성기 클래스
    프로젝트 정보를 기반으로 견적을 자동 생성하고 엑셀 파일로 저장합니다.
    """
    
    def __init__(self, settings):
        """
        견적 생성기 초기화
        
        Args:
            settings (dict): 애플리케이션 설정
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.client = OpenAI()
        
    def generate(self, project_data):
        """
        프로젝트 데이터를 기반으로 견적 생성
        
        Args:
            project_data (dict): 프로젝트 정보
            
        Returns:
            dict: 생성된 견적 데이터
        """
        try:
            # OpenAI API 프롬프트 구성
            prompt = self._create_prompt(project_data)
            
            # API 호출
            response = self.client.chat.completions.create(
                model="gpt-4",  # 또는 설정에서 지정된 모델
                messages=[
                    {"role": "system", "content": "당신은 소프트웨어 프로젝트 견적 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # 응답 파싱
            estimate_data = self._parse_response(response.choices[0].message.content)
            
            self.logger.info("견적 생성 완료")
            return estimate_data
            
        except Exception as e:
            self.logger.error(f"견적 생성 중 오류 발생: {str(e)}", exc_info=True)
            raise
            
    def save_to_excel(self, estimate_data, file_path=None):
        """
        견적 데이터를 엑셀 파일로 저장
        
        Args:
            estimate_data (dict): 견적 데이터
            file_path (str, optional): 저장할 파일 경로. None이면 기본 경로에 저장
        """
        try:
            if file_path is None:
                # 기본 출력 디렉토리 사용
                output_dir = self.settings.get("output_dir", "estimates")
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # 파일명 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = output_path / f"estimate_{timestamp}.xlsx"
            else:
                # 지정된 파일 경로 사용
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 프로젝트 정보 시트 데이터 준비
            project_info = [
                ["견적서 정보", ""],
                ["생성일자", datetime.now().strftime("%Y-%m-%d")],
                ["총 견적 금액", f"{sum(item['amount'] for item in estimate_data['items']):,}원"],
                ["예상 기간", f"{len(estimate_data['items'])}개월"],
                ["", ""],
                ["항목별 상세 내역", ""]
            ]
            
            # DataFrame 생성
            df_items = pd.DataFrame(estimate_data["items"])
            
            # 천단위 구분기호 적용
            df_items["unit_price"] = df_items["unit_price"].apply(lambda x: format(x, ","))
            df_items["amount"] = df_items["amount"].apply(lambda x: format(x, ","))
            
            # 컬럼명 한글화
            df_items.columns = ["항목", "설명", "단가", "수량", "금액"]
            
            # 엑셀 작성
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 프로젝트 정보 시트
                pd.DataFrame(project_info).to_excel(
                    writer,
                    sheet_name='프로젝트 정보',
                    header=False,
                    index=False
                )
                
                # 견적 상세 시트
                df_items.to_excel(
                    writer,
                    sheet_name='견적서',
                    index=False
                )
                
                # 워크시트 가져오기
                workbook = writer.book
                
                # 프로젝트 정보 시트 서식 설정
                ws_info = workbook['프로젝트 정보']
                for row in ws_info.iter_rows():
                    for cell in row:
                        cell.alignment = openpyxl.styles.Alignment(vertical='center')
                        if cell.row == 1:
                            cell.font = openpyxl.styles.Font(bold=True, size=12)
                
                # 견적서 시트 서식 설정
                ws_estimate = workbook['견적서']
                
                # 헤더 서식
                for cell in ws_estimate[1]:
                    cell.font = openpyxl.styles.Font(bold=True)
                    cell.alignment = openpyxl.styles.Alignment(horizontal='center')
                    cell.fill = openpyxl.styles.PatternFill(
                        start_color='CCE5FF',
                        end_color='CCE5FF',
                        fill_type='solid'
                    )
                
                # 열 너비 자동 조정
                for ws in [ws_info, ws_estimate]:
                    for column in ws.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        ws.column_dimensions[column[0].column_letter].width = adjusted_width
            
            self.logger.info(f"견적서가 저장되었습니다: {file_path}")
            
        except Exception as e:
            self.logger.error(f"엑셀 파일 저장 중 오류 발생: {str(e)}", exc_info=True)
            raise
            
    def _create_prompt(self, project_data):
        """
        OpenAI API 프롬프트 생성
        
        Args:
            project_data (dict): 프로젝트 정보
            
        Returns:
            str: 생성된 프롬프트
        """
        # 개발 수준별 기본 인건비 설정 (1인/월 기준)
        dev_level_costs = {
            "기업형 (Enterprise)": {
                "시니어 개발자": 12000000,
                "미들 개발자": 8000000,
                "주니어 개발자": 5000000,
                "PM": 15000000,
                "디자이너": 7000000,
                "QA": 6000000
            },
            "전문가형 (Professional)": {
                "시니어 개발자": 10000000,
                "미들 개발자": 7000000,
                "주니어 개발자": 4500000,
                "PM": 12000000,
                "디자이너": 6000000,
                "QA": 5000000
            },
            "표준형 (Standard)": {
                "시니어 개발자": 8000000,
                "미들 개발자": 6000000,
                "주니어 개발자": 4000000,
                "PM": 10000000,
                "디자이너": 5000000,
                "QA": 4000000
            },
            "기본형 (Basic)": {
                "시니어 개발자": 7000000,
                "미들 개발자": 5000000,
                "주니어 개발자": 3500000,
                "PM": 8000000,
                "디자이너": 4000000,
                "QA": 3500000
            }
        }
        
        # 선택된 개발 수준의 비용 정보
        selected_costs = dev_level_costs[project_data['dev_level']]
        
        return f"""
당신은 소프트웨어 프로젝트 견적 전문가입니다. 다음 프로젝트에 대한 상세 견적서를 생성해주세요.
현실적이고 합리적인 견적을 작성하되, 프로젝트의 품질과 안정성을 보장할 수 있는 수준이어야 합니다.

프로젝트 정보:
- 프로젝트명: {project_data['project_name']}
- 프로젝트 유형: {project_data['project_type']}
- 클라이언트: {project_data['client_name']}
- 예상 기간: {project_data['project_period']}개월
- 개발 수준: {project_data['dev_level']}

요구사항:
{project_data['requirements']}

기술 스택:
{project_data['tech_stack']}

개발 인력 기준 단가 (1인/월):
- 시니어 개발자: {selected_costs['시니어 개발자']:,}원
- 미들 개발자: {selected_costs['미들 개발자']:,}원
- 주니어 개발자: {selected_costs['주니어 개발자']:,}원
- PM: {selected_costs['PM']:,}원
- 디자이너: {selected_costs['디자이너']:,}원
- QA: {selected_costs['QA']:,}원

다음 형식으로 JSON 응답을 제공해주세요:
{{
    "items": [
        {{
            "item": "항목명",
            "description": "설명",
            "unit_price": 단가(숫자),
            "quantity": 수량(숫자),
            "amount": 금액(숫자)
        }},
        ...
    ]
}}

견적 작성 시 다음 사항을 고려해주세요:

1. 인력 구성
   - 프로젝트 규모와 기간에 맞는 적절한 인력 구성
   - 각 역할별 필요 인원수와 투입 기간 명시
   - 시니어/미들/주니어 개발자의 적절한 비율 구성

2. 주요 비용 항목
   - 개발 인력 비용 (역할별 단가 기준)
   - 프로젝트 관리 및 품질 관리 비용
   - UI/UX 디자인 비용
   - 테스트 및 QA 비용
   - 인프라 및 라이선스 비용
   - 유지보수 및 기술지원 비용

3. 기타 고려사항
   - 프로젝트 난이도와 복잡성
   - 기술 스택의 전문성 요구 수준
   - 보안 요구사항 및 규제 준수 사항
   - 예상되는 리스크와 대응 비용

각 비용 항목에 대해 상세한 설명을 포함하고, 시장 표준과 프로젝트 특성을 고려하여 현실적인 견적을 작성해주세요.
"""
            
    def _parse_response(self, response_text):
        """
        API 응답 파싱
        
        Args:
            response_text (str): API 응답 텍스트
            
        Returns:
            dict: 파싱된 견적 데이터
        """
        try:
            # JSON 문자열 찾기
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            json_str = response_text[start_idx:end_idx]
            
            # JSON 파싱
            data = json.loads(json_str)
            
            # 금액 계산 검증
            for item in data["items"]:
                expected_amount = item["unit_price"] * item["quantity"]
                if item["amount"] != expected_amount:
                    item["amount"] = expected_amount
                    
            return data
            
        except Exception as e:
            self.logger.error(f"응답 파싱 중 오류 발생: {str(e)}", exc_info=True)
            raise ValueError("API 응답을 파싱할 수 없습니다.") 