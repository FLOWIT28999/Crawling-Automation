"""
RISS 웹 스크래핑 모듈
Playwright를 사용하여 RISS 웹사이트에서 논문 정보를 수집
"""

import asyncio
import json
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, Browser

logger = logging.getLogger(__name__)


class RISSScraper:
    """RISS 웹사이트 스크래핑 클래스"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """초기화"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.papers: List[Dict] = []
        
    async def initialize(self):
        """브라우저 초기화"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.page = await self.browser.new_page()
        logger.info("브라우저 초기화 완료")
        
    async def search_papers(self, keyword: str, max_papers: int = 50) -> List[Dict]:
        """논문 검색 및 무료 논문 필터링"""
        if not self.page:
            await self.initialize()
            
        papers = []
        
        try:
            # RISS 국내학술논문 검색 페이지로 직접 이동
            search_url = f"{self.config['riss_settings']['base_url']}/search/Search.do?isDetailSearch=N&searchGubun=true&viewYn=OP&query={keyword}&queryText=&strQuery={keyword}&colName=re_a_kor&pageNumber=1&pageSize=20"
            await self.page.goto(search_url)
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # 검색 결과가 로드될 때까지 대기
            try:
                await self.page.wait_for_selector('.srchResultListW', timeout=15000)
            except:
                # 검색 결과가 없을 경우
                logger.warning(f"'{keyword}' 검색 결과가 없습니다.")
                return papers
            
            # 무료 논문 수집
            papers = await self._collect_free_papers(max_papers)
            
        except Exception as e:
            logger.error(f"검색 중 오류 발생: {e}")
            
        return papers
    
    async def _collect_free_papers(self, max_papers: int) -> List[Dict]:
        """무료 논문만 필터링하여 수집"""
        papers = []
        page_num = 1
        max_pages = 10  # 최대 페이지 수 제한
        
        while len(papers) < max_papers and page_num <= max_pages:
            try:
                # 현재 페이지의 논문 목록 가져오기
                await self.page.wait_for_selector('.srchResultListW', timeout=10000)
                
                # 논문 항목들 선택 - 올바른 선택자 사용
                paper_elements = await self.page.query_selector_all('.srchResultListW .cont')
                
                if not paper_elements:
                    # 다른 선택자 시도
                    paper_elements = await self.page.query_selector_all('.srchResultListW li .cont')
                
                if not paper_elements:
                    logger.warning(f"페이지 {page_num}에서 논문을 찾을 수 없습니다.")
                    break
                
                logger.info(f"페이지 {page_num}에서 {len(paper_elements)}개의 논문 항목 발견")
                
                for element in paper_elements:
                    if len(papers) >= max_papers:
                        break
                    
                    # 논문 정보 추출 시도
                    paper_info = await self._extract_paper_info(element)
                    if paper_info:
                        # 무료 논문 확인
                        is_free = await self._is_free_paper(element)
                        paper_info['is_free'] = is_free
                        
                        # 무료 논문만 수집하거나 설정에 따라 모든 논문 수집
                        if is_free or not self.config.get('free_papers_only', True):
                            papers.append(paper_info)
                            logger.info(f"수집된 논문 ({len(papers)}/{max_papers}): {paper_info.get('title', 'Unknown')[:50]}...")
                
                # 다음 페이지로 이동
                if len(papers) < max_papers:
                    # 페이지네이션 찾기
                    next_button = await self.page.query_selector('div.Paging a.next')
                    if not next_button:
                        # 다른 형태의 페이지네이션 시도
                        next_button = await self.page.query_selector('a[title="다음페이지"]')
                    
                    if next_button:
                        # 버튼이 비활성화되었는지 확인
                        is_disabled = await next_button.get_attribute('class')
                        if is_disabled and 'disabled' in str(is_disabled):
                            logger.info("마지막 페이지에 도달했습니다.")
                            break
                            
                        await next_button.click()
                        await self.page.wait_for_load_state('networkidle', timeout=15000)
                        page_num += 1
                        logger.info(f"페이지 {page_num}으로 이동")
                    else:
                        logger.info("다음 페이지 버튼을 찾을 수 없습니다.")
                        break
                else:
                    break
                    
            except Exception as e:
                logger.error(f"페이지 {page_num} 수집 중 오류: {e}")
                break
                
        return papers[:max_papers]
    
    async def _is_free_paper(self, element) -> bool:
        """무료 논문인지 확인"""
        try:
            # 무료 아이콘/라벨 확인 (RISS는 무료 논문에 특별한 표시를 함)
            free_indicators = [
                'img[src*="free"]',
                'img[src*="open"]',
                'span.free',
                'span:has-text("무료")',
                'span:has-text("원문보기")',
                '.originView',  # 원문보기 버튼
                'a.btn_orig'  # 원문 버튼
            ]
            
            for selector in free_indicators:
                try:
                    free_element = await element.query_selector(selector)
                    if free_element:
                        return True
                except:
                    continue
            
            # onclick 속성에서 원문 관련 함수 확인
            all_links = await element.query_selector_all('a')
            for link in all_links:
                onclick = await link.get_attribute('onclick')
                if onclick:
                    if any(func in onclick for func in ['openFulltext', 'viewOriginal', 'fn_origView']):
                        return True
                        
                # href 속성 확인
                href = await link.get_attribute('href')
                if href and any(keyword in href for keyword in ['openFulltext', 'original', 'fulltext']):
                    return True
                    
        except Exception as e:
            logger.debug(f"무료 논문 확인 중 오류: {e}")
            
        return False
    
    async def _extract_paper_info(self, element) -> Dict:
        """논문 정보 추출"""
        try:
            paper_info = {}
            
            # 제목 추출 - 여러 가능한 선택자 시도
            title_selectors = [
                'p.title a',
                '.title a', 
                'div.cont p.title a',
                'a.tit'
            ]
            
            for selector in title_selectors:
                title_elem = await element.query_selector(selector)
                if title_elem:
                    paper_info['title'] = (await title_elem.inner_text()).strip()
                    paper_info['link'] = await title_elem.get_attribute('href')
                    if paper_info['link'] and not paper_info['link'].startswith('http'):
                        paper_info['link'] = self.config['riss_settings']['base_url'] + paper_info['link']
                    break
            
            if not paper_info.get('title'):
                return None  # 제목이 없으면 유효하지 않은 논문
            
            # 저자 추출
            author_selectors = [
                'p.writer',
                '.writer',
                'span.writer',
                'p.etc span:first-child'
            ]
            
            for selector in author_selectors:
                author_elem = await element.query_selector(selector)
                if author_elem:
                    authors_text = (await author_elem.inner_text()).strip()
                    # 저자명 정제
                    authors_text = authors_text.replace('저자:', '').strip()
                    paper_info['authors'] = authors_text
                    break
            
            # 발행 정보 추출
            pub_selectors = [
                'p.etc',
                '.etc',
                'span.source'
            ]
            
            for selector in pub_selectors:
                pub_elem = await element.query_selector(selector)
                if pub_elem:
                    pub_text = (await pub_elem.inner_text()).strip()
                    paper_info['publication'] = pub_text
                    
                    # 발행 정보에서 연도 추출 시도
                    import re
                    year_match = re.search(r'(19|20)\d{2}', pub_text)
                    if year_match:
                        paper_info['year'] = year_match.group()
                    break
            
            # 초록 미리보기 추출 - 더 많은 시도
            abstract_selectors = [
                'p.preAbstract',
                '.preAbstract',
                'p.abstract',
                'span.preAbstract',
                'div.abstract'
            ]
            
            for selector in abstract_selectors:
                abstract_elem = await element.query_selector(selector)
                if abstract_elem:
                    paper_info['abstract_preview'] = (await abstract_elem.inner_text()).strip()
                    break
            
            # 초록이 없으면 페이지 내 텍스트에서 찾기
            if not paper_info.get('abstract_preview'):
                # 전체 요소의 텍스트에서 초록 패턴 찾기
                element_text = await element.inner_text()
                if '초록' in element_text or 'Abstract' in element_text:
                    lines = element_text.split('\n')
                    for i, line in enumerate(lines):
                        if '초록' in line or 'Abstract' in line:
                            # 다음 줄이 초록일 가능성
                            if i + 1 < len(lines) and len(lines[i + 1]) > 100:
                                paper_info['abstract_preview'] = lines[i + 1].strip()
                                break
            
            # 원문 링크 추출 시도
            fulltext_link = await element.query_selector('a.btn_orig, a.originView, a[onclick*="openFulltext"]')
            if fulltext_link:
                onclick = await fulltext_link.get_attribute('onclick')
                if onclick:
                    paper_info['fulltext_onclick'] = onclick
            
            return paper_info if paper_info else None
            
        except Exception as e:
            logger.error(f"논문 정보 추출 중 오류: {e}")
            return None
    
    async def get_paper_details(self, paper_url: str) -> Dict:
        """논문 상세 정보 가져오기"""
        if not self.page:
            await self.initialize()
            
        details = {}
        
        try:
            # 새 탭에서 열기 (현재 검색 결과를 보존하기 위해)
            detail_page = await self.browser.new_page()
            
            await detail_page.goto(paper_url)
            await detail_page.wait_for_load_state('networkidle', timeout=15000)
            await asyncio.sleep(2)  # 페이지가 완전히 로드되기를 기다림
            
            # 제목
            title_selector = '#thesisInfoDiv > div.thesisInfoTop > h3'
            title_elem = await detail_page.query_selector(title_selector)
            if title_elem:
                details['title'] = await title_elem.inner_text()
            
            # 초록 보기 버튼 클릭 시도
            try:
                abstract_btn = await detail_page.query_selector('a#soptionview, button.btn_option')
                if abstract_btn:
                    await abstract_btn.click()
                    await asyncio.sleep(1)
            except:
                pass
            
            # 초록 - 다양한 방법으로 시도
            abstract_selectors = [
                '#soptionview p',
                '#additionalInfoDiv p.text',
                'div.abstract_layer p',
                'div.thesisInfo p.text',
                'p.abstractTxt',
                '.addInfo p.text',
                'div[id*="abstract"] p'
            ]
            
            for selector in abstract_selectors:
                try:
                    abstract_elem = await detail_page.query_selector(selector)
                    if abstract_elem:
                        text = await abstract_elem.inner_text()
                        if len(text) > 50:  # 실제 초록인지 확인
                            details['abstract'] = text.strip()
                            break
                except:
                    continue
            
            # JavaScript로 초록 찾기 (위 방법이 실패한 경우)
            if not details.get('abstract'):
                try:
                    js_abstract = await detail_page.evaluate("""
                        () => {
                            // 모든 텍스트 요소에서 초록 찾기
                            const elements = document.querySelectorAll('p, div');
                            for (const elem of elements) {
                                const text = elem.textContent || '';
                                // 초록일 가능성이 높은 긴 텍스트
                                if (text.length > 200 && text.length < 5000) {
                                    // 학술적 단어가 포함되어 있는지 확인
                                    if (text.includes('연구') || text.includes('분석') || 
                                        text.includes('결과') || text.includes('this') || 
                                        text.includes('study') || text.includes('research')) {
                                        // RISS 메뉴 텍스트가 아닌지 확인
                                        if (!text.includes('RISS') && !text.includes('로그인') && 
                                            !text.includes('회원가입') && !text.includes('MyRISS')) {
                                            return text.trim();
                                        }
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                    if js_abstract and len(js_abstract) > 100:
                        details['abstract'] = js_abstract
                except:
                    pass
            
            # 원문 링크
            fulltext_selectors = [
                'a.btn_orig',
                'a.originView',
                '#thesisInfoDiv a[onclick*="openFulltext"]',
                'a[href*="link.riss.kr"]'
            ]
            
            for selector in fulltext_selectors:
                fulltext_elem = await detail_page.query_selector(selector)
                if fulltext_elem:
                    href = await fulltext_elem.get_attribute('href')
                    onclick = await fulltext_elem.get_attribute('onclick')
                    
                    if href and href != '#':
                        details['fulltext_link'] = href if href.startswith('http') else self.config['riss_settings']['base_url'] + href
                    elif onclick:
                        details['fulltext_onclick'] = onclick
                    break
            
            # 추가 메타데이터
            meta_selectors = {
                'authors': '.infoDetailL .writer',
                'journal': '.infoDetailL .assigned',
                'year': '.infoDetailL span:has-text("발행연도")',
                'keywords': '.keyword'
            }
            
            for key, selector in meta_selectors.items():
                elem = await detail_page.query_selector(selector)
                if elem:
                    details[key] = await elem.inner_text()
            
            # 페이지 닫기
            await detail_page.close()
                    
        except Exception as e:
            logger.error(f"상세 정보 가져오기 중 오류: {e}")
            
        return details
    
    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            logger.info("브라우저 종료")


# 테스트용 메인 함수
async def main():
    scraper = RISSScraper()
    try:
        await scraper.initialize()
        papers = await scraper.search_papers("AI", max_papers=5)
        
        print(f"\n총 {len(papers)}개의 논문을 수집했습니다.\n")
        
        for i, paper in enumerate(papers, 1):
            print(f"\n[논문 {i}]")
            print(f"제목: {paper.get('title', 'N/A')}")
            print(f"저자: {paper.get('authors', 'N/A')}")
            print(f"링크: {paper.get('link', 'N/A')}")
            print(f"무료여부: {paper.get('is_free', False)}")
            print("-" * 50)
            
    finally:
        await scraper.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())