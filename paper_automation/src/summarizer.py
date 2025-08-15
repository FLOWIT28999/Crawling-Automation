"""
AI 요약 모듈
Google Gemini API를 사용하여 논문 요약 생성
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()


class PaperSummarizer:
    """논문 요약 생성 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        """초기화
        
        Args:
            api_key: Gemini API 키 (없으면 환경변수나 config에서 로드)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            # config.json에서 로드 시도
            try:
                with open('config/config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.api_key = config.get('gemini_api_key')
            except:
                pass
                
        if not self.api_key:
            raise ValueError("Gemini API 키가 필요합니다")
            
        # Gemini 설정
        genai.configure(api_key=self.api_key)
        # 최신 모델 사용 (gemini-1.5-flash가 더 빠르고 효율적)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API 초기화 완료")
        
    def generate_summary(self, title: str, abstract: str = None, keywords: List[str] = None) -> str:
        """논문 요약 생성
        
        Args:
            title: 논문 제목
            abstract: 논문 초록 (없을 수 있음)
            keywords: 키워드 리스트
            
        Returns:
            생성된 요약
        """
        try:
            # 초록이 없거나 너무 짧으면 제목과 키워드만으로 요약
            if not abstract or len(abstract) < 50:
                logger.warning(f"초록이 없거나 너무 짧음. 제목만으로 요약 시도: {title[:50]}...")
                abstract = f"초록 정보가 없습니다. 제목: {title}"
            
            # 프롬프트 구성
            prompt = self._create_prompt(title, abstract, keywords)
            
            # Gemini API 호출
            response = self.model.generate_content(prompt)
            
            if response.text:
                logger.info(f"요약 생성 완료: {title[:50]}...")
                return response.text
            else:
                logger.warning("요약 생성 실패: 빈 응답")
                return "요약을 생성할 수 없습니다."
                
        except Exception as e:
            logger.error(f"요약 생성 중 오류: {e}")
            return f"요약 생성 실패: {str(e)}"
            
    def _create_prompt(self, title: str, abstract: str, keywords: List[str] = None) -> str:
        """요약용 프롬프트 생성
        
        Args:
            title: 논문 제목
            abstract: 논문 초록
            keywords: 키워드 리스트
            
        Returns:
            프롬프트 문자열
        """
        keywords_str = ", ".join(keywords) if keywords else "없음"
        
        prompt = f"""다음 학술 논문의 정보를 바탕으로 한국어로 간결하고 명확한 요약을 작성해주세요.

**논문 제목**: {title}

**키워드**: {keywords_str}

**초록**: {abstract}

다음 형식으로 요약해주세요:
1. **주요 주제**: (1-2문장으로 논문의 핵심 주제 설명)
2. **연구 목적**: (연구의 목적과 해결하고자 하는 문제)
3. **방법론**: (사용된 연구 방법이나 접근법)
4. **주요 발견**: (연구의 주요 결과나 발견사항)
5. **의의**: (이 연구의 학술적/실용적 의의)

요약은 전문가가 아닌 일반 독자도 이해할 수 있도록 작성해주세요."""
        
        return prompt
        
    async def summarize_batch_async(self, papers: List[Dict]) -> List[Dict]:
        """여러 논문을 비동기로 일괄 요약
        
        Args:
            papers: 논문 데이터 리스트
            
        Returns:
            요약이 추가된 논문 데이터 리스트
        """
        tasks = []
        for paper in papers:
            # 제목만 있어도 요약 시도
            if paper.get('title'):
                task = self._summarize_single_async(paper)
                tasks.append(task)
            else:
                # 요약할 수 없는 논문은 그대로 반환
                tasks.append(self._return_unchanged_async(paper))
                
        results = await asyncio.gather(*tasks)
        return results
        
    async def _summarize_single_async(self, paper: Dict) -> Dict:
        """단일 논문 비동기 요약
        
        Args:
            paper: 논문 데이터
            
        Returns:
            요약이 추가된 논문 데이터
        """
        try:
            # 동기 함수를 비동기로 실행
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(
                None,
                self.generate_summary,
                paper.get('title', ''),
                paper.get('abstract', ''),
                paper.get('keywords', [])
            )
            
            paper['summary'] = summary
            paper['summary_generated_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"비동기 요약 중 오류: {e}")
            paper['summary'] = f"요약 생성 실패: {str(e)}"
            
        return paper
        
    async def _return_unchanged_async(self, paper: Dict) -> Dict:
        """변경 없이 반환 (비동기 일관성 유지)"""
        return paper
        
    def summarize_batch(self, papers: List[Dict]) -> List[Dict]:
        """여러 논문 일괄 요약 (동기)
        
        Args:
            papers: 논문 데이터 리스트
            
        Returns:
            요약이 추가된 논문 데이터 리스트
        """
        summarized_papers = []
        total = len(papers)
        
        for idx, paper in enumerate(papers, 1):
            logger.info(f"요약 진행중: {idx}/{total}")
            
            if paper.get('title') and paper.get('abstract'):
                summary = self.generate_summary(
                    paper.get('title', ''),
                    paper.get('abstract', ''),
                    paper.get('keywords', [])
                )
                paper['summary'] = summary
                paper['summary_generated_at'] = datetime.now().isoformat()
            else:
                paper['summary'] = "요약 생성 불가: 제목 또는 초록 누락"
                
            summarized_papers.append(paper)
            
            # API 호출 제한을 위한 대기
            if idx < total:
                asyncio.sleep(1)  # 1초 대기
                
        return summarized_papers
        
    def create_executive_summary(self, papers: List[Dict]) -> str:
        """전체 논문 컬렉션의 종합 요약 생성
        
        Args:
            papers: 논문 데이터 리스트
            
        Returns:
            종합 요약 텍스트
        """
        if not papers:
            return "요약할 논문이 없습니다."
            
        # 논문 제목들 수집
        titles = [p.get('title', 'Unknown') for p in papers[:10]]  # 최대 10개
        
        prompt = f"""다음은 수집된 학술 논문들의 제목입니다:

{chr(10).join(f'{i+1}. {title}' for i, title in enumerate(titles))}

이 논문들의 전반적인 연구 동향과 주제를 분석하여, 다음 형식으로 종합 요약을 작성해주세요:

1. **주요 연구 분야**: 논문들이 다루는 주요 연구 분야
2. **공통 주제**: 논문들 간의 공통된 주제나 관심사
3. **연구 트렌드**: 현재 연구 동향이나 트렌드
4. **향후 연구 방향**: 예상되는 향후 연구 방향

간결하고 통찰력 있는 분석을 제공해주세요."""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text if response.text else "종합 요약 생성 실패"
        except Exception as e:
            logger.error(f"종합 요약 생성 중 오류: {e}")
            return f"종합 요약 생성 실패: {str(e)}"


# 테스트용 함수
def test_summarizer():
    """요약기 테스트"""
    # 테스트용 API 키 설정 필요
    # summarizer = PaperSummarizer(api_key="YOUR_API_KEY")
    
    sample_paper = {
        "title": "딥러닝을 활용한 자연어 처리 연구",
        "abstract": "본 연구는 딥러닝 기술을 활용하여 한국어 자연어 처리의 성능을 향상시키는 방법을 제안한다. BERT와 GPT 모델을 기반으로 한 새로운 아키텍처를 설계하고, 대규모 한국어 코퍼스를 사용하여 사전 학습을 수행했다. 실험 결과, 제안된 방법이 기존 방법보다 15% 높은 정확도를 보였다.",
        "keywords": ["딥러닝", "자연어처리", "BERT", "GPT", "한국어"]
    }
    
    print("Gemini API 키가 필요합니다. 실제 테스트는 API 키 설정 후 실행하세요.")
    
    # API 키가 있다면:
    # summary = summarizer.generate_summary(
    #     sample_paper['title'],
    #     sample_paper['abstract'],
    #     sample_paper['keywords']
    # )
    # print("생성된 요약:")
    # print(summary)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_summarizer()