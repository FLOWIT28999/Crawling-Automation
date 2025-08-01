import requests
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

class StockAnalyzer:
    """주식 데이터 분석 및 뉴스 모니터링 클래스"""
    
    def __init__(self, ticker: str, company: str):
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
        
    def fetch_stock_data(self) -> Dict:
        """Alpha Vantage API를 통해 주식 데이터 조회"""
        parameters = {
            "function": "TIME_SERIES_DAILY",
            "symbol": self.ticker,
            "apikey": self.credentials['alpha_vantage']
        }
        
        try:
            response = requests.get(self.api_endpoints['stock'], params=parameters)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"주식 데이터 조회 실패: {e}")
            return {}
    
    def extract_closing_prices(self, stock_data: Dict) -> Tuple[Optional[float], Optional[float]]:
        """최근 이틀간의 종가 추출"""
        try:
            daily_series = stock_data.get("Time Series (Daily)", {})
            dates = sorted(daily_series.keys(), reverse=True)
            
            if len(dates) < 2:
                return None, None
                
            recent_close = float(daily_series[dates[0]]["4. close"])
            previous_close = float(daily_series[dates[1]]["4. close"])
            
            return recent_close, previous_close
            
        except (KeyError, ValueError, IndexError):
            return None, None
    
    def calculate_price_change(self, current: float, previous: float) -> Tuple[float, float, str]:
        """가격 변동률 계산"""
        change_amount = current - previous
        change_percent = (change_amount / previous) * 100
        
        indicator = "📈" if change_amount >= 0 else "📉"
        
        return change_amount, round(change_percent), indicator
    
    def fetch_company_news(self, min_threshold: float = 1.0) -> List[Dict]:
        """뉴스 API를 통해 관련 뉴스 조회"""
        params = {
            "apiKey": self.credentials['news_api'],
            "qInTitle": self.company,
            "sortBy": "publishedAt",
            "pageSize": 3
        }
        
        try:
            response = requests.get(self.api_endpoints['news'], params=params)
            response.raise_for_status()
            news_data = response.json()
            return news_data.get("articles", [])[:3]
        except requests.exceptions.RequestException as e:
            print(f"뉴스 조회 실패: {e}")
            return []
    
    def format_news_item(self, article: Dict, price_info: Tuple[str, float, str]) -> str:
        """뉴스 항목 포맷팅"""
        ticker, percent, indicator = price_info
        
        return (f"[{ticker}] {indicator} {abs(percent)}% 변동\n"
                f"제목: {article.get('title', '제목 없음')}\n"
                f"요약: {article.get('description', '내용 없음')[:200]}...")
    
    def analyze_and_report(self):
        """주식 분석 및 리포트 생성"""
        # 주식 데이터 가져오기
        stock_data = self.fetch_stock_data()
        if not stock_data:
            print("주식 데이터를 가져올 수 없습니다.")
            return
        
        # 종가 추출
        today_close, yesterday_close = self.extract_closing_prices(stock_data)
        if today_close is None or yesterday_close is None:
            print("종가 데이터를 추출할 수 없습니다.")
            return
        
        # 가격 정보 출력
        print(f"최근 종가: ${today_close:.2f}")
        print(f"이전 종가: ${yesterday_close:.2f}")
        
        # 변동률 계산
        change, percent_change, trend = self.calculate_price_change(today_close, yesterday_close)
        print(f"변동률: {percent_change}% ({trend})")
        
        # 뉴스 확인 (1% 이상 변동 시)
        if abs(percent_change) >= 1:
            print("\n📰 관련 뉴스를 검색합니다...")
            articles = self.fetch_company_news()
            
            if articles:
                print(f"\n최신 {len(articles)}개 뉴스:\n")
                for idx, article in enumerate(articles, 1):
                    news_text = self.format_news_item(
                        article, 
                        (self.ticker, percent_change, trend)
                    )
                    print(f"[뉴스 {idx}]")
                    print(news_text)
                    print("-" * 60)
            else:
                print("관련 뉴스를 찾을 수 없습니다.")
        else:
            print("\n변동률이 1% 미만이므로 뉴스를 검색하지 않습니다.")


def main():
    """메인 실행 함수"""
    # 모니터링할 주식 설정
    monitor = StockAnalyzer(ticker="TSLA", company="Tesla Inc")
    
    # 분석 실행
    monitor.analyze_and_report()


if __name__ == "__main__":
    main()