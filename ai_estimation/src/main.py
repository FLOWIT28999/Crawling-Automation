#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI 자동 견적 시스템의 메인 진입점
이 모듈은 PySide6 기반의 GUI 애플리케이션을 시작하고 초기화합니다.
"""

import sys
import logging
from pathlib import Path
from PySide6.QtWidgets import QApplication

# 상대 경로 import를 위한 경로 설정
current_dir = Path(__file__).resolve().parent
sys.path.append(str(current_dir))

from ui.main_window import MainWindow
from utils.logger import setup_logger
from config.settings import load_settings

def main():
    """
    애플리케이션의 메인 진입점
    GUI를 초기화하고 이벤트 루프를 시작합니다.
    """
    try:
        # 로깅 설정
        setup_logger()
        logger = logging.getLogger(__name__)
        logger.info("AI 자동 견적 시스템을 시작합니다.")

        # 설정 로드
        settings = load_settings()
        
        # GUI 애플리케이션 초기화
        app = QApplication(sys.argv)
        window = MainWindow(settings)
        window.show()
        
        # 이벤트 루프 시작
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main() 