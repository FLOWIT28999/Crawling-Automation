"""
상수 정의 모듈
프로젝트에서 사용되는 모든 상수값들을 정의합니다.
"""

# 애플리케이션 설정
APP_NAME = "AI 자동 견적 시스템"
APP_VERSION = "1.0.0"

# 데이터베이스 설정
DB_FILE = "database.db"

# OpenAI API 설정
DEFAULT_MODEL = "gpt-4-turbo-preview"
MAX_TOKENS = 4000

# UI 설정
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
FONT_FAMILY = "Malgun Gothic"
FONT_SIZE = 10

# 견적서 템플릿 설정
TEMPLATE_DIR = "templates"
DEFAULT_TEMPLATE = "default_template.xlsx"

# 로깅 설정
LOG_FILE = "app.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 에러 메시지
ERROR_MESSAGES = {
    "API_ERROR": "OpenAI API 호출 중 오류가 발생했습니다.",
    "DB_ERROR": "데이터베이스 작업 중 오류가 발생했습니다.",
    "FILE_ERROR": "파일 처리 중 오류가 발생했습니다.",
    "INVALID_INPUT": "입력값이 올바르지 않습니다.",
} 