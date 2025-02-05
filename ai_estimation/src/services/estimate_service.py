"""
견적 생성 서비스 모듈
OpenAI API를 사용하여 프로젝트 견적을 자동으로 생성합니다.
"""

import os
import logging
import json
from typing import Dict, Any, List
from openai import OpenAI
from src.config.constants import DEFAULT_MODEL, MAX_TOKENS, ERROR_MESSAGES

logger = logging.getLogger(__name__)

class EstimateService:
    """견적 생성 서비스 클래스"""

    def __init__(self):
        """OpenAI API 클라이언트 초기화"""
        try:
            self.client = OpenAI()
        except Exception as e:
            logger.error(f"OpenAI API 클라이언트 초기화 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["API_ERROR"])

    def generate_estimate(self, project_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        프로젝트 정보를 기반으로 견적을 생성합니다.
        
        Args:
            project_info: 프로젝트 정보를 담은 딕셔너리
                - name: 프로젝트명
                - description: 프로젝트 설명
                - requirements: 요구사항 목록
                - duration: 예상 기간
                - team_size: 팀 규모
        
        Returns:
            생성된 견적 정보를 담은 딕셔너리
        """
        try:
            # 프롬프트 생성
            prompt = self._create_prompt(project_info)
            
            # API 호출
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": """당신은 전문적인 프로젝트 견적 산정 전문가입니다. 
                        항상 다음과 같은 JSON 형식으로 응답해야 합니다:
                        {
                            "labor_costs": [
                                {
                                    "role": "직무명",
                                    "monthly_rate": 단가(숫자),
                                    "duration": 기간(숫자)
                                }
                            ],
                            "setup_cost": 숫자,
                            "license_cost": 숫자,
                            "maintenance_cost": 숫자,
                            "contingency": 숫자,
                            "total_cost": 숫자
                        }"""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.7
            )
            
            # 응답 파싱
            estimate_data = self._parse_response(response.choices[0].message.content)
            return estimate_data
            
        except Exception as e:
            logger.error(f"견적 생성 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["API_ERROR"])

    def _create_prompt(self, project_info: Dict[str, Any]) -> str:
        """API 요청을 위한 프롬프트를 생성합니다."""
        return f"""
다음 프로젝트에 대한 상세한 견적을 작성해주세요. 반드시 JSON 형식으로 응답해주세요.

프로젝트명: {project_info['name']}
프로젝트 설명: {project_info['description']}
요구사항:
{self._format_requirements(project_info['requirements'])}
예상 기간: {project_info['duration']}개월
팀 규모: {project_info['team_size']}명

다음 항목들을 포함하여 JSON 형식으로 작성해주세요:
1. labor_costs: 인건비 (역할별 단가 및 투입 기간)
   - role: 직무명
   - monthly_rate: 월 단가
   - duration: 투입 기간(월)
2. setup_cost: 개발 환경 구축 비용
3. license_cost: 라이선스 및 외부 서비스 비용
4. maintenance_cost: 유지보수 비용
5. contingency: 예비비 (전체 금액의 10%)
6. total_cost: 총 견적 금액

숫자는 모두 정수로 표현해주세요.
"""

    def _format_requirements(self, requirements: List[str]) -> str:
        """요구사항 목록을 포맷팅합니다."""
        return "\n".join(f"- {req}" for req in requirements)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """API 응답을 파싱하여 구조화된 데이터로 변환합니다."""
        try:
            # 응답 텍스트에서 JSON 부분만 추출
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("JSON 형식의 응답을 찾을 수 없습니다.")
            
            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)
            
            # 필수 필드 검증
            required_fields = ['labor_costs', 'setup_cost', 'license_cost', 
                             'maintenance_cost', 'contingency', 'total_cost']
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"필수 필드가 누락되었습니다: {field}")
            
            return data
            
        except Exception as e:
            logger.error(f"응답 파싱 중 오류 발생: {e}")
            # 기본 견적 템플릿 반환
            return {
                "labor_costs": [
                    {
                        "role": "프로젝트 매니저",
                        "monthly_rate": 7000000,
                        "duration": 3
                    },
                    {
                        "role": "개발자",
                        "monthly_rate": 6000000,
                        "duration": 3
                    }
                ],
                "setup_cost": 5000000,
                "license_cost": 2000000,
                "maintenance_cost": 1000000,
                "contingency": 3000000,
                "total_cost": 30000000
            }

    def refine_estimate(self, original_estimate: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        기존 견적을 피드백을 반영하여 수정합니다.
        
        Args:
            original_estimate: 원본 견적 데이터
            feedback: 고객 피드백
            
        Returns:
            수정된 견적 데이터
        """
        try:
            prompt = f"""
기존 견적서:
{json.dumps(original_estimate, ensure_ascii=False, indent=2)}

고객 피드백:
{feedback}

위 피드백을 반영하여 견적서를 수정해주세요. 반드시 JSON 형식으로 응답해주세요.
"""
            response = self.client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[
                    {
                        "role": "system", 
                        "content": "당신은 전문적인 프로젝트 견적 산정 전문가입니다. 반드시 JSON 형식으로 응답해주세요."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=MAX_TOKENS
            )
            
            return self._parse_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"견적 수정 중 오류 발생: {e}")
            raise Exception(ERROR_MESSAGES["API_ERROR"]) 