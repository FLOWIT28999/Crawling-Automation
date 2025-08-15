"""
백엔드 통합 모듈
모든 모듈을 연결하고 전체 워크플로우를 관리
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QThread

from src.scraper import RISSScraper
from src.extractor import DataExtractor
from src.storage import DataStorage
from src.summarizer import PaperSummarizer
from src.exporter import ExcelExporter

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    """워커 스레드 시그널"""
    progress = Signal(int)  # 진행률 (0-100)
    status = Signal(str)    # 상태 메시지
    error = Signal(str)     # 에러 메시지
    finished = Signal()     # 작업 완료
    result = Signal(object) # 결과 데이터


class PaperCollectorWorker(QThread):
    """논문 수집 워커 스레드"""
    
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.signals = WorkerSignals()
        self.is_running = True
        
    def run(self):
        """워커 실행"""
        try:
            # 백엔드 엔진 생성
            engine = PaperCollectionEngine(self.config)
            
            # 진행 상황 콜백 연결
            engine.set_progress_callback(self.update_progress)
            engine.set_status_callback(self.update_status)
            
            # 비동기 작업 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                engine.collect_papers_async(
                    self.config.get('search_keywords', ['AI']),
                    self.config.get('max_papers', 50)
                )
            )
            
            self.signals.result.emit(result)
            self.signals.finished.emit()
            
        except Exception as e:
            logger.error(f"워커 실행 중 오류: {e}")
            self.signals.error.emit(str(e))
            
    def update_progress(self, value: int):
        """진행률 업데이트"""
        self.signals.progress.emit(value)
        
    def update_status(self, message: str):
        """상태 메시지 업데이트"""
        self.signals.status.emit(message)
        
    def stop(self):
        """작업 중지"""
        self.is_running = False


class PaperCollectionEngine:
    """논문 수집 엔진"""
    
    def __init__(self, config: Dict):
        """초기화
        
        Args:
            config: 설정 딕셔너리
        """
        self.config = config
        self.scraper = None
        self.extractor = DataExtractor()
        self.storage = DataStorage(config.get('output_path', './results'))
        self.summarizer = None
        self.exporter = ExcelExporter(config.get('output_path', './results'))
        
        # 콜백 함수
        self.progress_callback = None
        self.status_callback = None
        
        # Gemini API 키 확인
        api_key = config.get('gemini_api_key')
        if api_key:
            try:
                self.summarizer = PaperSummarizer(api_key)
            except Exception as e:
                logger.warning(f"Gemini API 초기화 실패: {e}")
                
    def set_progress_callback(self, callback: Callable[[int], None]):
        """진행률 콜백 설정"""
        self.progress_callback = callback
        
    def set_status_callback(self, callback: Callable[[str], None]):
        """상태 콜백 설정"""
        self.status_callback = callback
        
    def _update_progress(self, value: int):
        """진행률 업데이트"""
        if self.progress_callback:
            self.progress_callback(value)
            
    def _update_status(self, message: str):
        """상태 업데이트"""
        logger.info(message)
        if self.status_callback:
            self.status_callback(message)
            
    async def collect_papers_async(self, keywords: List[str], max_papers: int = 50) -> Dict:
        """논문 수집 (비동기)
        
        Args:
            keywords: 검색 키워드 리스트
            max_papers: 최대 수집 논문 수
            
        Returns:
            수집 결과 딕셔너리
        """
        result = {
            'success': False,
            'papers': [],
            'files': {},
            'statistics': {},
            'error': None
        }
        
        try:
            # 1. 스크래퍼 초기화
            self._update_status("브라우저 초기화 중...")
            self._update_progress(5)
            
            self.scraper = RISSScraper()
            await self.scraper.initialize()
            
            all_papers = []
            papers_per_keyword = max_papers // len(keywords) if len(keywords) > 0 else max_papers
            
            # 2. 각 키워드로 검색
            for idx, keyword in enumerate(keywords):
                self._update_status(f"'{keyword}' 검색 중...")
                progress = 10 + (idx * 30 // len(keywords))
                self._update_progress(progress)
                
                papers = await self.scraper.search_papers(keyword, papers_per_keyword)
                
                # 3. 상세 정보 수집 (선택적)
                # 상세 정보 수집이 실패해도 기본 정보는 유지
                for i, paper in enumerate(papers):
                    if paper.get('link'):
                        try:
                            self._update_status(f"상세 정보 수집 중... ({i+1}/{len(papers)})")
                            details = await self.scraper.get_paper_details(paper['link'])
                            if details:
                                paper.update(details)
                        except Exception as e:
                            logger.warning(f"상세 정보 수집 실패 ({paper.get('title', 'Unknown')}): {e}")
                            # 상세 정보 수집 실패해도 계속 진행
                        
                all_papers.extend(papers)
                
            # 4. 브라우저 종료
            await self.scraper.close()
            
            # 5. 데이터 정제
            self._update_status("데이터 정제 중...")
            self._update_progress(50)
            
            validated_papers = []
            for paper in all_papers:
                if self.extractor.validate_data(paper):
                    validated_papers.append(paper)
                    
            # 6. AI 요약 생성
            if self.summarizer and validated_papers:
                self._update_status("AI 요약 생성 중...")
                self._update_progress(60)
                
                validated_papers = await self.summarizer.summarize_batch_async(validated_papers)
                
                # 종합 요약 생성
                executive_summary = self.summarizer.create_executive_summary(validated_papers)
                result['executive_summary'] = executive_summary
                
            # 7. 데이터 저장
            self._update_status("데이터 저장 중...")
            self._update_progress(80)
            
            json_path = self.storage.save_papers(validated_papers)
            result['files']['json'] = json_path
            
            # 8. Excel 출력
            self._update_status("Excel 파일 생성 중...")
            self._update_progress(90)
            
            excel_path = self.exporter.export_papers(validated_papers)
            result['files']['excel'] = excel_path
            
            # 종합 보고서 생성
            if result.get('executive_summary'):
                report_path = self.exporter.export_summary_report(
                    validated_papers,
                    result['executive_summary']
                )
                result['files']['report'] = report_path
                
            # 9. 통계 생성
            result['statistics'] = self.storage.get_statistics(json_path)
            result['papers'] = validated_papers
            result['success'] = True
            
            self._update_status(f"수집 완료! 총 {len(validated_papers)}개 논문")
            self._update_progress(100)
            
        except Exception as e:
            logger.error(f"논문 수집 중 오류: {e}")
            result['error'] = str(e)
            self._update_status(f"오류 발생: {e}")
            
            # 브라우저 정리
            if self.scraper:
                try:
                    await self.scraper.close()
                except:
                    pass
                    
        return result
        
    def collect_papers_sync(self, keywords: List[str], max_papers: int = 50) -> Dict:
        """논문 수집 (동기)
        
        Args:
            keywords: 검색 키워드 리스트
            max_papers: 최대 수집 논문 수
            
        Returns:
            수집 결과 딕셔너리
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            self.collect_papers_async(keywords, max_papers)
        )
        
    def load_and_export(self, json_path: str) -> Dict:
        """저장된 데이터를 로드하고 Excel로 출력
        
        Args:
            json_path: JSON 파일 경로
            
        Returns:
            결과 딕셔너리
        """
        result = {
            'success': False,
            'files': {},
            'error': None
        }
        
        try:
            # 데이터 로드
            papers = self.storage.load_papers(json_path)
            
            if not papers:
                result['error'] = "데이터를 로드할 수 없습니다"
                return result
                
            # Excel 출력
            excel_path = self.exporter.export_papers(papers)
            result['files']['excel'] = excel_path
            
            # AI 요약이 있는 경우 보고서 생성
            if self.summarizer:
                executive_summary = self.summarizer.create_executive_summary(papers)
                report_path = self.exporter.export_summary_report(papers, executive_summary)
                result['files']['report'] = report_path
                
            result['success'] = True
            
        except Exception as e:
            logger.error(f"데이터 처리 중 오류: {e}")
            result['error'] = str(e)
            
        return result
        
    def update_config(self, config: Dict):
        """설정 업데이트
        
        Args:
            config: 새 설정 딕셔너리
        """
        self.config.update(config)
        
        # Gemini API 키 업데이트
        if 'gemini_api_key' in config and config['gemini_api_key']:
            try:
                self.summarizer = PaperSummarizer(config['gemini_api_key'])
            except Exception as e:
                logger.warning(f"Gemini API 업데이트 실패: {e}")


# 테스트용 함수
async def test_engine():
    """엔진 테스트"""
    config = {
        'search_keywords': ['AI', '머신러닝'],
        'max_papers': 5,
        'output_path': './test_results',
        'gemini_api_key': ''  # API 키 필요
    }
    
    engine = PaperCollectionEngine(config)
    
    # 진행 상황 출력
    engine.set_progress_callback(lambda x: print(f"진행률: {x}%"))
    engine.set_status_callback(lambda x: print(f"상태: {x}"))
    
    result = await engine.collect_papers_async(['AI'], 3)
    
    if result['success']:
        print(f"수집 성공! 논문 수: {len(result['papers'])}")
        print(f"저장된 파일: {result['files']}")
    else:
        print(f"수집 실패: {result['error']}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(test_engine())