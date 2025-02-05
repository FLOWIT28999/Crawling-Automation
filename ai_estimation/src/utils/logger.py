#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
로깅 설정 모듈
애플리케이션의 로깅 설정을 관리합니다.
"""

import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

def setup_logger(log_level="INFO", log_file="app.log"):
    """
    애플리케이션 로거 설정
    파일과 콘솔에 로그를 출력하도록 설정합니다.
    
    Args:
        log_level (str): 로깅 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str): 로그 파일 경로
    """
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / log_file
    
    # 로거 가져오기
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # 파일 핸들러 설정
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)
    
    # 콘솔 핸들러 설정
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter('%(levelname)s: %(message)s')
    )
    logger.addHandler(console_handler) 