# GUI 버전의 주식 분석기를 만들어보겠습니다
import sys
import requests
from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                               QLineEdit, QProgressBar, QGroupBox, QGridLayout,
                               QMessageBox, QFrame, QScrollArea)
from PySide6.QtCore import QThread, Signal, Qt, QTimer
from PySide6.QtGui import QFont, QPalette, QColor

class StockDataWorker(QThread):
    """백그라운드에서 주식 데이터를 가져오는 워커 클래스"""
    data_fetched = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self, ticker: str, company: str):
        super().__init__()
        self.ticker = ticker
        self.company = company
        self.api_endpoints = {
            'stock': "https://www.alphavantage.co/query",
            'news': "https://newsapi.org/v2/everything"
        }
        self.credentials = {
            'alpha_vantage': "EOWMRQVFKZNV4IFL",
            'news_api': "008196f15126437588a9e0e1087f2652"
        }
    
    def run(self):
        """워커 스레드 실행"""
        try:
            # 주식 데이터 가져오기
            stock_data = self.fetch_stock_data()
            if not stock_data:
                self.error_occurred.emit("주식 데이터를 가져올 수 없습니다.")
                return
            
            # 종가 추출
            today_close, yesterday_close = self.extract_closing_prices(stock_data)
            if today_close is None or yesterday_close is None:
                self.error_occurred.emit("종가 데이터를 추출할 수 없습니다.")
                return
            
            # 변동률 계산
            change, percent_change, trend = self.calculate_price_change(today_close, yesterday_close)
            
            # 뉴스 가져오기 (1% 이상 변동 시)
            news_articles = []
            if abs(percent_change) >= 1:
                news_articles = self.fetch_company_news()
            
            # 결과 데이터 구성
            result_data = {
                'ticker': self.ticker,
                'company': self.company,
                'current_price': today_close,
                'previous_price': yesterday_close,
                'change_amount': change,
                'change_percent': percent_change,
                'trend': trend,
                'news_articles': news_articles
            }
            
            self.data_fetched.emit(result_data)
            
        except Exception as e:
            self.error_occurred.emit(f"오류 발생: {str(e)}")
    
    def fetch_stock_data(self) -> Dict:
        """Alpha Vantage API를 통해 주식 데이터 조회"""
        parameters = {
            "function": "TIME_SERIES_DAILY",
            "symbol": self.ticker,
            "apikey": self.credentials['alpha_vantage']
        }
        
        response = requests.get(self.api_endpoints['stock'], params=parameters, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def extract_closing_prices(self, stock_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """최근 이틀간의 종가 추출"""
        daily_series = stock_data.get("Time Series (Daily)", {})
        dates = sorted(daily_series.keys(), reverse=True)
        
        if len(dates) < 2:
            return None, None
            
        recent_close = float(daily_series[dates[0]]["4. close"])
        previous_close = float(daily_series[dates[1]]["4. close"])
        
        return recent_close, previous_close
    
    def calculate_price_change(self, current: float, previous: float) -> Tuple[float, float, str]:
        """가격 변동률 계산"""
        change_amount = current - previous
        change_percent = (change_amount / previous) * 100
        indicator = "📈" if change_amount >= 0 else "📉"
        return change_amount, round(change_percent, 2), indicator
    
    def fetch_company_news(self) -> List[Dict]:
        """뉴스 API를 통해 관련 뉴스 조회"""
        params = {
            "apiKey": self.credentials['news_api'],
            "qInTitle": self.company,
            "sortBy": "publishedAt",
            "pageSize": 3
        }
        
        response = requests.get(self.api_endpoints['news'], params=params, timeout=10)
        response.raise_for_status()
        news_data = response.json()
        return news_data.get("articles", [])[:3]


class StockAnalyzerGUI(QMainWindow):
    """주식 분석기 GUI 메인 윈도우"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("📈 Stock Analyzer - 주식 분석기")
        self.setGeometry(100, 100, 900, 700)
        self.setStyleSheet(self.get_stylesheet())
        
        # 중앙 위젯 설정
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 헤더
        self.create_header(main_layout)
        
        # 입력 섹션
        self.create_input_section(main_layout)
        
        # 결과 섹션
        self.create_results_section(main_layout)
        
        # 뉴스 섹션
        self.create_news_section(main_layout)
        
        # 상태바
        self.statusBar().showMessage("준비됨")
        
    def create_header(self, layout):
        """헤더 섹션 생성"""
        header_frame = QFrame()
        header_frame.setObjectName("header")
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("📈 Stock Analyzer")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        
        subtitle = QLabel("실시간 주식 데이터 분석 및 뉴스 모니터링")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("subtitle")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header_frame)
    
    def create_input_section(self, layout):
        """입력 섹션 생성"""
        input_group = QGroupBox("📊 주식 정보 입력")
        input_group.setObjectName("inputGroup")
        input_layout = QGridLayout(input_group)
        
        # 티커 입력
        ticker_label = QLabel("주식 심볼:")
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("예: TSLA, AAPL, GOOGL")
        self.ticker_input.setText("TSLA")
        
        # 회사명 입력
        company_label = QLabel("회사명:")
        self.company_input = QLineEdit()
        self.company_input.setPlaceholderText("예: Tesla Inc, Apple Inc")
        self.company_input.setText("Tesla Inc")
        
        # 분석 버튼
        self.analyze_button = QPushButton("🔍 분석 시작")
        self.analyze_button.setObjectName("analyzeButton")
        self.analyze_button.clicked.connect(self.start_analysis)
        
        # 자동 새로고침 버튼
        self.auto_refresh_button = QPushButton("🔄 자동 새로고침 (5분)")
        self.auto_refresh_button.setObjectName("refreshButton")
        self.auto_refresh_button.setCheckable(True)
        self.auto_refresh_button.clicked.connect(self.toggle_auto_refresh)
        
        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # 레이아웃 배치
        input_layout.addWidget(ticker_label, 0, 0)
        input_layout.addWidget(self.ticker_input, 0, 1)
        input_layout.addWidget(company_label, 0, 2)
        input_layout.addWidget(self.company_input, 0, 3)
        input_layout.addWidget(self.analyze_button, 1, 0, 1, 2)
        input_layout.addWidget(self.auto_refresh_button, 1, 2, 1, 2)
        input_layout.addWidget(self.progress_bar, 2, 0, 1, 4)
        
        layout.addWidget(input_group)
        
        # 자동 새로고침 타이머
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.start_analysis)
    
    def create_results_section(self, layout):
        """결과 섹션 생성"""
        results_group = QGroupBox("📈 주식 데이터 분석 결과")
        results_group.setObjectName("resultsGroup")
        results_layout = QGridLayout(results_group)
        
        # 주가 정보 레이블들
        self.current_price_label = QLabel("현재가: -")
        self.previous_price_label = QLabel("전일가: -")
        self.change_amount_label = QLabel("변동액: -")
        self.change_percent_label = QLabel("변동률: -")
        
        # 스타일 적용
        self.current_price_label.setObjectName("priceLabel")
        self.change_percent_label.setObjectName("changeLabel")
        
        results_layout.addWidget(self.current_price_label, 0, 0)
        results_layout.addWidget(self.previous_price_label, 0, 1)
        results_layout.addWidget(self.change_amount_label, 1, 0)
        results_layout.addWidget(self.change_percent_label, 1, 1)
        
        layout.addWidget(results_group)
    
    def create_news_section(self, layout):
        """뉴스 섹션 생성"""
        news_group = QGroupBox("📰 관련 뉴스")
        news_group.setObjectName("newsGroup")
        news_layout = QVBoxLayout(news_group)
        
        # 스크롤 가능한 뉴스 영역
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        self.news_widget = QWidget()
        self.news_layout = QVBoxLayout(self.news_widget)
        
        scroll_area.setWidget(self.news_widget)
        news_layout.addWidget(scroll_area)
        
        layout.addWidget(news_group)
    
    def start_analysis(self):
        """분석 시작"""
        ticker = self.ticker_input.text().strip().upper()
        company = self.company_input.text().strip()
        
        if not ticker or not company:
            QMessageBox.warning(self, "입력 오류", "주식 심볼과 회사명을 모두 입력해주세요.")
            return
        
        # UI 상태 업데이트
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 무한 프로그레스
        self.statusBar().showMessage("데이터를 가져오는 중...")
        
        # 워커 스레드 시작
        self.worker = StockDataWorker(ticker, company)
        self.worker.data_fetched.connect(self.on_data_received)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()
    
    def on_data_received(self, data):
        """데이터 수신 완료"""
        # UI 상태 복원
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("분석 완료")
        
        # 결과 업데이트
        self.update_results(data)
        self.update_news(data)
    
    def on_error(self, error_message):
        """에러 처리"""
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("오류 발생")
        
        QMessageBox.critical(self, "오류", error_message)
    
    def update_results(self, data):
        """결과 섹션 업데이트"""
        current_price = data['current_price']
        previous_price = data['previous_price']
        change_amount = data['change_amount']
        change_percent = data['change_percent']
        trend = data['trend']
        
        self.current_price_label.setText(f"현재가: ${current_price:.2f}")
        self.previous_price_label.setText(f"전일가: ${previous_price:.2f}")
        self.change_amount_label.setText(f"변동액: ${change_amount:+.2f}")
        
        # 변동률에 따른 색상 변경
        percent_text = f"변동률: {change_percent:+.2f}% {trend}"
        self.change_percent_label.setText(percent_text)
        
        if change_percent > 0:
            self.change_percent_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        elif change_percent < 0:
            self.change_percent_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        else:
            self.change_percent_label.setStyleSheet("color: #7f8c8d; font-weight: bold;")
    
    def update_news(self, data):
        """뉴스 섹션 업데이트"""
        # 기존 뉴스 위젯 제거
        for i in reversed(range(self.news_layout.count())):
            self.news_layout.itemAt(i).widget().setParent(None)
        
        news_articles = data['news_articles']
        
        if abs(data['change_percent']) >= 1 and news_articles:
            for idx, article in enumerate(news_articles, 1):
                news_item = self.create_news_item(idx, article, data)
                self.news_layout.addWidget(news_item)
        else:
            no_news_label = QLabel("변동률이 1% 미만이거나 관련 뉴스가 없습니다.")
            no_news_label.setAlignment(Qt.AlignCenter)
            no_news_label.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 20px;")
            self.news_layout.addWidget(no_news_label)
    
    def create_news_item(self, idx, article, data):
        """뉴스 항목 위젯 생성"""
        news_frame = QFrame()
        news_frame.setObjectName("newsItem")
        news_layout = QVBoxLayout(news_frame)
        
        # 뉴스 헤더
        header_text = f"[{data['ticker']}] {data['trend']} {abs(data['change_percent']):.1f}% 변동 - 뉴스 {idx}"
        header_label = QLabel(header_text)
        header_label.setObjectName("newsHeader")
        
        # 뉴스 제목
        title_label = QLabel(f"제목: {article.get('title', '제목 없음')}")
        title_label.setWordWrap(True)
        title_label.setObjectName("newsTitle")
        
        # 뉴스 내용
        description = article.get('description', '내용 없음')
        if len(description) > 200:
            description = description[:200] + "..."
        
        content_label = QLabel(f"요약: {description}")
        content_label.setWordWrap(True)
        content_label.setObjectName("newsContent")
        
        news_layout.addWidget(header_label)
        news_layout.addWidget(title_label)
        news_layout.addWidget(content_label)
        
        return news_frame
    
    def toggle_auto_refresh(self):
        """자동 새로고침 토글"""
        if self.auto_refresh_button.isChecked():
            self.refresh_timer.start(300000)  # 5분 = 300,000ms
            self.auto_refresh_button.setText("⏹️ 자동 새로고침 중지")
            self.statusBar().showMessage("자동 새로고침 활성화 (5분 간격)")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_button.setText("🔄 자동 새로고침 (5분)")
            self.statusBar().showMessage("자동 새로고침 비활성화")
    
    def get_stylesheet(self):
        """애플리케이션 스타일시트"""
        return """
        QMainWindow {
            background-color: #f8f9fa;
        }
        
        #header {
            background-color: #2c3e50;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 10px;
        }
        
        #title {
            font-size: 28px;
            font-weight: bold;
            color: white;
            margin-bottom: 5px;
        }
        
        #subtitle {
            font-size: 14px;
            color: #bdc3c7;
        }
        
        QGroupBox {
            font-size: 14px;
            font-weight: bold;
            color: #2c3e50;
            border: 2px solid #bdc3c7;
            border-radius: 10px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 10px 0 10px;
            background-color: #f8f9fa;
        }
        
        QLineEdit {
            padding: 8px;
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            font-size: 12px;
        }
        
        QLineEdit:focus {
            border-color: #3498db;
        }
        
        #analyzeButton {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
        }
        
        #analyzeButton:hover {
            background-color: #2980b9;
        }
        
        #analyzeButton:pressed {
            background-color: #21618c;
        }
        
        #refreshButton {
            background-color: #27ae60;
            color: white;
            border: none;
            padding: 10px;
            border-radius: 5px;
            font-weight: bold;
            font-size: 14px;
        }
        
        #refreshButton:hover {
            background-color: #229954;
        }
        
        #refreshButton:checked {
            background-color: #e74c3c;
        }
        
        #priceLabel {
            font-size: 16px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        }
        
        #changeLabel {
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        }
        
        #newsItem {
            background-color: white;
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            margin: 5px;
            padding: 15px;
        }
        
        #newsHeader {
            font-weight: bold;
            color: #e74c3c;
            font-size: 13px;
            margin-bottom: 5px;
        }
        
        #newsTitle {
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
            margin-bottom: 5px;
        }
        
        #newsContent {
            color: #7f8c8d;
            font-size: 12px;
            line-height: 1.4;
        }
        
        QScrollArea {
            border: none;
            background-color: #ecf0f1;
            border-radius: 5px;
        }
        
        QProgressBar {
            border: 2px solid #bdc3c7;
            border-radius: 5px;
            text-align: center;
        }
        
        QProgressBar::chunk {
            background-color: #3498db;
            border-radius: 3px;
        }
        """


def main():
    """메인 실행 함수"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 정보 설정
    app.setApplicationName("Stock Analyzer")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Stock Analyzer Corp")
    
    # 메인 윈도우 생성 및 표시
    window = StockAnalyzerGUI()
    window.show()
    
    # 이벤트 루프 시작
    sys.exit(app.exec())

# 실행
if __name__ == "__main__":
    main()