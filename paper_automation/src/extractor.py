"""
데이터 추출 모듈
논문 상세 페이지에서 필요한 데이터를 추출
"""

import re
import logging
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)


class DataExtractor:
    """논문 데이터 추출 클래스"""
    
    def __init__(self):
        """초기화"""
        self.extracted_data = []
        
    def extract_from_html(self, html_content: str) -> Dict:
        """HTML에서 논문 정보 추출"""
        soup = BeautifulSoup(html_content, 'lxml')
        data = {}
        
        try:
            # 제목 추출
            title_elem = soup.select_one('#thesisInfoDiv > div.thesisInfoTop > h3')
            if title_elem:
                data['title'] = self._clean_text(title_elem.get_text())
            
            # 저자 추출
            author_elem = soup.select_one('.writer')
            if author_elem:
                data['authors'] = self._clean_text(author_elem.get_text())
            
            # 초록 추출
            abstract_elem = soup.select_one('#additionalInfoDiv > div > div > div:nth-child(5) > p')
            if not abstract_elem:
                # 대체 선택자 시도
                abstract_elem = soup.select_one('.abstract')
            if abstract_elem:
                data['abstract'] = self._clean_text(abstract_elem.get_text())
            
            # 원문 링크 추출
            fulltext_elem = soup.select_one('#thesisInfoDiv > div.btnBunch > div.btnBunchL > ul > li:nth-child(1) > a')
            if fulltext_elem:
                data['fulltext_link'] = fulltext_elem.get('href', '')
                if data['fulltext_link'] and not data['fulltext_link'].startswith('http'):
                    data['fulltext_link'] = 'https://www.riss.kr' + data['fulltext_link']
            
            # 발행 정보 추출
            publication_info = self._extract_publication_info(soup)
            data.update(publication_info)
            
            # 키워드 추출
            keywords = self._extract_keywords(soup)
            if keywords:
                data['keywords'] = keywords
            
            # 수집 시간 추가
            data['collected_at'] = datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"HTML 데이터 추출 중 오류: {e}")
            
        return data
    
    def _extract_publication_info(self, soup: BeautifulSoup) -> Dict:
        """발행 정보 추출"""
        info = {}
        
        try:
            # 학술지명
            journal_elem = soup.select_one('.assigned')
            if journal_elem:
                info['journal'] = self._clean_text(journal_elem.get_text())
            
            # 발행연도
            year_elem = soup.select_one('.year')
            if year_elem:
                year_text = self._clean_text(year_elem.get_text())
                year_match = re.search(r'\d{4}', year_text)
                if year_match:
                    info['year'] = year_match.group()
            
            # 권/호
            volume_elem = soup.select_one('.volume')
            if volume_elem:
                info['volume'] = self._clean_text(volume_elem.get_text())
            
            # 페이지
            page_elem = soup.select_one('.page')
            if page_elem:
                info['pages'] = self._clean_text(page_elem.get_text())
                
        except Exception as e:
            logger.debug(f"발행 정보 추출 중 오류: {e}")
            
        return info
    
    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """키워드 추출"""
        keywords = []
        
        try:
            keyword_elem = soup.select_one('.keyword_list')
            if keyword_elem:
                keyword_items = keyword_elem.select('a')
                keywords = [self._clean_text(item.get_text()) for item in keyword_items]
            
            # 대체 선택자
            if not keywords:
                keyword_elem = soup.select_one('.keywords')
                if keyword_elem:
                    text = self._clean_text(keyword_elem.get_text())
                    keywords = [k.strip() for k in text.split(',')]
                    
        except Exception as e:
            logger.debug(f"키워드 추출 중 오류: {e}")
            
        return keywords
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)
        # 앞뒤 공백 제거
        text = text.strip()
        # HTML 엔티티 처리
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        
        return text
    
    def validate_data(self, data: Dict) -> bool:
        """추출된 데이터 유효성 검사"""
        required_fields = ['title']  # 최소한 제목은 있어야 함
        
        for field in required_fields:
            if field not in data or not data[field]:
                logger.warning(f"필수 필드 누락: {field}")
                return False
        
        # 제목이 있으면 기본적으로 유효한 데이터로 간주
        # 초록이나 원문 링크는 있으면 좋지만 필수는 아님
        if not data.get('abstract') and not data.get('fulltext_link'):
            logger.debug("초록과 원문 링크가 없음 (선택적)")
            # return False를 제거하여 계속 진행
            
        return True
    
    def process_batch(self, html_list: List[str]) -> List[Dict]:
        """여러 HTML을 일괄 처리"""
        results = []
        
        for html in html_list:
            data = self.extract_from_html(html)
            if self.validate_data(data):
                results.append(data)
                logger.info(f"데이터 추출 성공: {data.get('title', 'Unknown')}")
            else:
                logger.warning("유효하지 않은 데이터 스킵")
                
        return results
    
    def extract_free_paper_info(self, html_content: str, patterns: List[str]) -> Optional[Dict]:
        """무료 논문 정보 추출"""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # openFulltext 함수 찾기
        scripts = soup.find_all('script')
        for script in scripts:
            script_text = script.get_text()
            if 'openFulltext' in script_text:
                # 패턴 매칭
                for pattern in patterns:
                    if pattern in script_text:
                        # 무료 논문으로 확인됨
                        return self.extract_from_html(html_content)
        
        # onclick 속성 확인
        elements_with_onclick = soup.find_all(attrs={'onclick': True})
        for elem in elements_with_onclick:
            onclick = elem.get('onclick', '')
            if 'openFulltext' in onclick:
                for pattern in patterns:
                    if pattern in onclick:
                        return self.extract_from_html(html_content)
        
        return None


# 테스트용 함수
def test_extractor():
    """추출기 테스트"""
    extractor = DataExtractor()
    
    # 샘플 HTML (실제로는 스크래퍼에서 가져옴)
    sample_html = """
    <html>
        <div id="thesisInfoDiv">
            <div class="thesisInfoTop">
                <h3>AI와 머신러닝 연구</h3>
            </div>
            <div class="btnBunch">
                <div class="btnBunchL">
                    <ul>
                        <li><a href="/download/paper.pdf">원문보기</a></li>
                    </ul>
                </div>
            </div>
        </div>
        <div id="additionalInfoDiv">
            <div>
                <div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div>
                        <p>이 논문은 AI와 머신러닝에 대한 연구입니다...</p>
                    </div>
                </div>
            </div>
        </div>
        <div class="writer">홍길동, 김철수</div>
        <div class="year">2024</div>
    </html>
    """
    
    data = extractor.extract_from_html(sample_html)
    print("추출된 데이터:")
    for key, value in data.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_extractor()