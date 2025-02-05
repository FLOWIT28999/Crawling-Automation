#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
애플리케이션 설정 모듈
환경 변수 및 기본 설정을 관리합니다.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 기본 설정값
DEFAULT_SETTINGS = {
    "openai_model": "gpt-4o-mini",
    "temperature": 0.7,
    "output_dir": "estimates",
    "log_level": "INFO",
    "log_file": "app.log"
}

def load_settings():
    """
    애플리케이션 설정 로드
    환경 변수와 설정 파일을 통합하여 설정을 반환합니다.
    
    Returns:
        dict: 애플리케이션 설정
    """
    # 환경 변수 로드
    load_dotenv()
    
    # 설정 파일 경로
    config_path = Path("config.json")
    
    # 설정 딕셔너리 초기화
    settings = DEFAULT_SETTINGS.copy()
    
    # 설정 파일이 있으면 로드
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            file_settings = json.load(f)
            settings.update(file_settings)
            
    # 환경 변수에서 설정 업데이트
    env_settings = {
        "openai_model": os.getenv("OPENAI_MODEL"),
        "temperature": os.getenv("TEMPERATURE"),
        "output_dir": os.getenv("OUTPUT_DIR"),
        "log_level": os.getenv("LOG_LEVEL"),
        "log_file": os.getenv("LOG_FILE")
    }
    
    # None이 아닌 환경 변수 값으로 설정 업데이트
    settings.update({k: v for k, v in env_settings.items() if v is not None})
    
    return settings 