"""
데이터 저장 모듈
수집된 논문 데이터를 JSON 형식으로 저장
"""

import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class DataStorage:
    """데이터 저장 및 관리 클래스"""
    
    def __init__(self, base_path: str = "./results"):
        """초기화
        
        Args:
            base_path: 데이터 저장 기본 경로
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.current_session = None
        self._create_session()
        
    def _create_session(self):
        """새 세션 생성"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = f"session_{timestamp}"
        session_path = self.base_path / self.current_session
        session_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"새 세션 생성: {self.current_session}")
        
    def save_papers(self, papers: List[Dict], filename: Optional[str] = None) -> str:
        """논문 데이터를 JSON으로 저장
        
        Args:
            papers: 논문 데이터 리스트
            filename: 저장할 파일명 (없으면 자동 생성)
            
        Returns:
            저장된 파일 경로
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"papers_{timestamp}.json"
            
        filepath = self.base_path / self.current_session / filename
        
        try:
            # 메타데이터 추가
            data = {
                "metadata": {
                    "total_count": len(papers),
                    "collected_at": datetime.now().isoformat(),
                    "session": self.current_session
                },
                "papers": papers
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"데이터 저장 완료: {filepath} ({len(papers)}개 논문)")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")
            raise
            
    def load_papers(self, filepath: str) -> List[Dict]:
        """저장된 논문 데이터 로드
        
        Args:
            filepath: JSON 파일 경로
            
        Returns:
            논문 데이터 리스트
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if isinstance(data, dict) and 'papers' in data:
                return data['papers']
            elif isinstance(data, list):
                return data
            else:
                logger.warning("알 수 없는 데이터 형식")
                return []
                
        except FileNotFoundError:
            logger.error(f"파일을 찾을 수 없음: {filepath}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            return []
            
    def append_paper(self, paper: Dict, filepath: Optional[str] = None):
        """기존 파일에 논문 추가
        
        Args:
            paper: 추가할 논문 데이터
            filepath: JSON 파일 경로 (없으면 현재 세션의 최신 파일)
        """
        if not filepath:
            # 현재 세션의 최신 파일 찾기
            session_path = self.base_path / self.current_session
            json_files = list(session_path.glob("papers_*.json"))
            if json_files:
                filepath = str(max(json_files, key=os.path.getctime))
            else:
                # 새 파일 생성
                self.save_papers([paper])
                return
                
        papers = self.load_papers(filepath)
        papers.append(paper)
        
        # 파일명 추출
        filename = Path(filepath).name
        self.save_papers(papers, filename)
        
    def get_statistics(self, filepath: str) -> Dict:
        """저장된 데이터의 통계 정보 반환
        
        Args:
            filepath: JSON 파일 경로
            
        Returns:
            통계 정보 딕셔너리
        """
        papers = self.load_papers(filepath)
        
        if not papers:
            return {"total": 0}
            
        stats = {
            "total": len(papers),
            "has_abstract": sum(1 for p in papers if p.get('abstract')),
            "has_fulltext": sum(1 for p in papers if p.get('fulltext_link')),
            "has_keywords": sum(1 for p in papers if p.get('keywords')),
            "years": {}
        }
        
        # 연도별 통계
        for paper in papers:
            year = paper.get('year', 'Unknown')
            stats['years'][year] = stats['years'].get(year, 0) + 1
            
        return stats
        
    def merge_sessions(self, session_ids: List[str], output_filename: str) -> str:
        """여러 세션의 데이터 병합
        
        Args:
            session_ids: 병합할 세션 ID 리스트
            output_filename: 출력 파일명
            
        Returns:
            병합된 파일 경로
        """
        all_papers = []
        
        for session_id in session_ids:
            session_path = self.base_path / session_id
            if not session_path.exists():
                logger.warning(f"세션을 찾을 수 없음: {session_id}")
                continue
                
            json_files = list(session_path.glob("papers_*.json"))
            for json_file in json_files:
                papers = self.load_papers(str(json_file))
                all_papers.extend(papers)
                
        # 중복 제거 (제목 기준)
        unique_papers = []
        seen_titles = set()
        
        for paper in all_papers:
            title = paper.get('title', '')
            if title and title not in seen_titles:
                unique_papers.append(paper)
                seen_titles.add(title)
                
        # 병합된 데이터 저장
        filepath = self.base_path / output_filename
        
        data = {
            "metadata": {
                "total_count": len(unique_papers),
                "merged_from": session_ids,
                "merged_at": datetime.now().isoformat()
            },
            "papers": unique_papers
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"세션 병합 완료: {filepath} ({len(unique_papers)}개 논문)")
        return str(filepath)
        
    def export_for_ai(self, filepath: str) -> List[Dict]:
        """AI 요약을 위한 데이터 준비
        
        Args:
            filepath: JSON 파일 경로
            
        Returns:
            AI 처리용 데이터 리스트
        """
        papers = self.load_papers(filepath)
        ai_ready_data = []
        
        for paper in papers:
            if paper.get('title') and paper.get('abstract'):
                ai_ready_data.append({
                    'title': paper['title'],
                    'abstract': paper['abstract'],
                    'keywords': paper.get('keywords', []),
                    'year': paper.get('year', ''),
                    'original_data': paper  # 원본 데이터 보존
                })
                
        logger.info(f"AI 처리용 데이터 준비: {len(ai_ready_data)}개")
        return ai_ready_data


# 테스트용 함수
def test_storage():
    """저장소 테스트"""
    storage = DataStorage()
    
    # 샘플 데이터
    sample_papers = [
        {
            "title": "AI와 머신러닝 연구",
            "authors": "홍길동",
            "abstract": "이 논문은 AI에 대한 연구입니다.",
            "year": "2024",
            "fulltext_link": "https://example.com/paper1.pdf"
        },
        {
            "title": "딥러닝 응용 사례",
            "authors": "김철수",
            "abstract": "딥러닝의 다양한 응용 사례를 다룹니다.",
            "year": "2024",
            "fulltext_link": "https://example.com/paper2.pdf"
        }
    ]
    
    # 저장
    filepath = storage.save_papers(sample_papers)
    print(f"저장된 파일: {filepath}")
    
    # 로드
    loaded_papers = storage.load_papers(filepath)
    print(f"로드된 논문 수: {len(loaded_papers)}")
    
    # 통계
    stats = storage.get_statistics(filepath)
    print(f"통계 정보: {stats}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_storage()