import sys
import os
import pandas as pd
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLineEdit, QSpinBox, QPushButton, 
                              QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
                              QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

class CoupangCrawler:
    """쿠팡 웹사이트 크롤링을 담당하는 클래스"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.setup_driver()

    def setup_driver(self):
        """Selenium WebDriver 초기화"""
        try:
            options = webdriver.ChromeOptions()
            # 필수 옵션 추가
            options.add_argument('--headless')  # 헤드리스 모드
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')  # Windows 환경에서 필요
            options.add_argument('--window-size=1920,1080')  # 윈도우 크기 설정
            options.add_argument('--ignore-certificate-errors')  # 인증서 오류 무시
            options.add_argument('--disable-extensions')  # 확장 프로그램 비활성화
            options.add_argument('--disable-blink-features=AutomationControlled')  # 자동화 감지 방지
            
            # User-Agent 설정
            options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            
            # 크롬 드라이버 자동 설치 및 초기화
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # 페이지 로드 타임아웃 설정
            self.driver.set_page_load_timeout(30)
            
            # 암묵적 대기 시간 설정
            self.driver.implicitly_wait(10)
            
            return True
            
        except Exception as e:
            print(f"드라이버 초기화 중 오류 발생: {str(e)}")
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
            raise

    def search_products(self, keyword, max_items=10):
        """제품 검색 및 정보 수집"""
        try:
            # URL 인코딩
            encoded_keyword = requests.utils.quote(keyword)
            url = f'https://www.coupang.com/np/search?q={encoded_keyword}&channel=user&component=&eventCategory=SRP'
            
            # 페이지 로드 전 쿠키 및 캐시 삭제
            self.driver.delete_all_cookies()
            
            # 페이지 로드
            self.driver.get(url)
            
            # 페이지 로드 대기
            time.sleep(random.uniform(2, 3))  # 랜덤 딜레이 증가

            products = []
            page_count = 1
            
            while len(products) < max_items and page_count <= 5:  # 최대 5페이지까지만 검색
                try:
                    # 제품 목록 대기
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "search-product"))
                    )

                    # 제품 정보 추출
                    items = self.driver.find_elements(By.CLASS_NAME, "search-product")
                    
                    for item in items:
                        if len(products) >= max_items:
                            break

                        try:
                            product = self._extract_product_info(item)
                            if product:
                                products.append(product)
                        except Exception as e:
                            print(f"제품 정보 추출 중 오류: {str(e)}")
                            continue

                    # 다음 페이지 확인
                    if len(products) < max_items:
                        try:
                            next_button = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.CLASS_NAME, "btn-next"))
                            )
                            if "disabled" not in next_button.get_attribute("class"):
                                next_button.click()
                                time.sleep(random.uniform(2, 3))
                                page_count += 1
                            else:
                                break
                        except Exception as e:
                            print(f"다음 페이지 이동 중 오류: {str(e)}")
                            break

                except Exception as e:
                    print(f"페이지 {page_count} 처리 중 오류: {str(e)}")
                    break

            return products[:max_items]

        except Exception as e:
            print(f"검색 중 오류 발생: {str(e)}")
            return []

    def _extract_product_info(self, item):
        """개별 제품 정보 추출"""
        try:
            # 제품명
            name = item.find_element(By.CLASS_NAME, "name").text

            # 가격 정보
            price = item.find_element(By.CLASS_NAME, "price-value").text
            price = price.replace(",", "")

            # 평점
            try:
                rating = item.find_element(By.CLASS_NAME, "rating").text
            except:
                rating = "평점 없음"

            # 리뷰 수
            try:
                review_count = item.find_element(By.CLASS_NAME, "rating-total-count").text
                review_count = review_count.strip("()")
            except:
                review_count = "0"

            # 제품 링크
            link = item.find_element(By.CLASS_NAME, "search-product-link").get_attribute("href")

            return {
                "제품명": name,
                "가격": price,
                "평점": rating,
                "리뷰수": review_count,
                "링크": link
            }
        except Exception as e:
            print(f"제품 정보 추출 중 오류: {str(e)}")
            return None

    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()

class CrawlerThread(QThread):
    """크롤링 작업을 위한 스레드 클래스"""
    
    finished = Signal(list)  # 크롤링 완료 시그널
    progress = Signal(int)   # 진행률 시그널
    error = Signal(str)      # 에러 시그널

    def __init__(self, keyword, max_items):
        super().__init__()
        self.keyword = keyword
        self.max_items = max_items
        self.crawler = None

    def run(self):
        """크롤링 실행"""
        try:
            self.crawler = CoupangCrawler()
            products = self.crawler.search_products(self.keyword, self.max_items)
            self.finished.emit(products)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if self.crawler:
                self.crawler.close()

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("쿠팡 제품 크롤러")
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        """UI 구성"""
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 검색 영역
        search_layout = QHBoxLayout()
        
        # 검색어 입력
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("검색어를 입력하세요")
        search_layout.addWidget(self.search_input)

        # 검색 수량 설정
        self.item_count = QSpinBox()
        self.item_count.setRange(1, 100)
        self.item_count.setValue(10)
        search_layout.addWidget(QLabel("검색 수량:"))
        search_layout.addWidget(self.item_count)

        # 검색 버튼
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.start_crawling)
        search_layout.addWidget(self.search_button)

        # 저장 버튼
        self.save_button = QPushButton("엑셀로 저장")
        self.save_button.clicked.connect(self.save_to_excel)
        self.save_button.setEnabled(False)
        search_layout.addWidget(self.save_button)

        layout.addLayout(search_layout)

        # 진행률 표시
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 결과 테이블
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(["제품명", "가격", "평점", "리뷰수", "링크"])
        layout.addWidget(self.result_table)

        # 상태 표시줄
        self.statusBar().showMessage("준비됨")

    def start_crawling(self):
        """크롤링 시작"""
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "경고", "검색어를 입력하세요.")
            return

        self.search_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.result_table.setRowCount(0)
        self.statusBar().showMessage("크롤링 중...")

        # 크롤링 스레드 시작
        self.crawler_thread = CrawlerThread(keyword, self.item_count.value())
        self.crawler_thread.finished.connect(self.update_table)
        self.crawler_thread.error.connect(self.show_error)
        self.crawler_thread.start()

    def update_table(self, products):
        """테이블 업데이트"""
        self.result_table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            self.result_table.setItem(row, 0, QTableWidgetItem(product["제품명"]))
            self.result_table.setItem(row, 1, QTableWidgetItem(product["가격"]))
            self.result_table.setItem(row, 2, QTableWidgetItem(product["평점"]))
            self.result_table.setItem(row, 3, QTableWidgetItem(product["리뷰수"]))
            self.result_table.setItem(row, 4, QTableWidgetItem(product["링크"]))

        self.result_table.resizeColumnsToContents()
        self.search_button.setEnabled(True)
        self.save_button.setEnabled(True)
        self.progress_bar.setValue(100)
        self.statusBar().showMessage("크롤링 완료")

    def save_to_excel(self):
        """엑셀 파일로 저장"""
        try:
            # 현재 날짜시간으로 파일명 생성
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"coupang_products_{current_time}.xlsx"

            # 테이블 데이터를 데이터프레임으로 변환
            data = []
            for row in range(self.result_table.rowCount()):
                row_data = {}
                for col in range(self.result_table.columnCount()):
                    item = self.result_table.item(row, col)
                    header = self.result_table.horizontalHeaderItem(col).text()
                    row_data[header] = item.text() if item else ""
                data.append(row_data)

            df = pd.DataFrame(data)
            df.to_excel(filename, index=False)
            
            QMessageBox.information(self, "알림", f"파일이 저장되었습니다.\n{filename}")
            
        except Exception as e:
            QMessageBox.critical(self, "오류", f"파일 저장 중 오류가 발생했습니다.\n{str(e)}")

    def show_error(self, error_message):
        """에러 메시지 표시"""
        QMessageBox.critical(self, "오류", f"크롤링 중 오류가 발생했습니다.\n{error_message}")
        self.search_button.setEnabled(True)
        self.statusBar().showMessage("오류 발생")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
