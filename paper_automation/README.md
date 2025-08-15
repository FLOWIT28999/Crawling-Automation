# RISS 학술논문 자동 수집 시스템

RISS(학술연구정보서비스)에서 학술논문을 자동으로 수집하고 AI로 요약하는 시스템입니다.

## 🚀 빠른 시작

### 설치
```bash
# uv 사용 (권장)
uv sync
uv run playwright install chromium

# 또는 pip 사용
pip install -r requirements.txt
playwright install chromium
```

### 실행
```bash
# GUI 모드
uv run run.py

# CLI 모드
uv run run.py --cli -k "AI,머신러닝" -c 10 --api-key YOUR_API_KEY
```

## 📁 프로젝트 구조

```
paper_automation/
├── src/                # 핵심 모듈
│   ├── backend.py      # 백엔드 엔진
│   ├── scraper.py      # 웹 스크래핑
│   ├── extractor.py    # 데이터 추출
│   ├── storage.py      # 데이터 저장
│   ├── summarizer.py   # AI 요약
│   └── exporter.py     # Excel 내보내기
├── config/             # 설정 파일
│   └── config.json     # 프로젝트 설정
├── docs/               # 문서
│   ├── README.md       # 상세 문서
│   └── CLAUDE.md       # Claude 가이드
├── run.py              # 메인 실행 파일
└── gui.py              # GUI 인터페이스
```

## ✨ 주요 기능

- 📚 RISS 논문 검색 및 수집
- 🆓 무료 논문 필터링
- 🤖 AI 요약 (Gemini API)
- 📊 Excel 파일 내보내기
- 🖥️ GUI 및 CLI 지원

## 📝 라이선스

MIT License