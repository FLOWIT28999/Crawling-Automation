"""
메인 애플리케이션 모듈
AI 자동 견적 시스템의 진입점입니다.
"""

import sys
import os
import logging
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication
from src.ui.main_window import MainWindow
from src.config.constants import LOG_FILE, LOG_FORMAT

def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )

def main():
    """메인 함수"""
    try:
        # 현재 디렉토리를 Python 경로에 추가
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # 환경 변수 로드
        load_dotenv()
        
        # OpenAI API 키 확인
        if not os.getenv('OPENAI_API_KEY'):
            raise Exception("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        # 로깅 설정
        setup_logging()
        
        # Qt 애플리케이션 생성
        app = QApplication(sys.argv)
        
        # 메인 윈도우 생성 및 표시
        window = MainWindow()
        window.show()
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        logging.error(f"애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 