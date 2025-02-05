# AI 자동 견적 시스템

PySide6 기반의 GUI 애플리케이션으로, OpenAI API를 활용하여 프로젝트 견적을 자동으로 생성하고 관리하는 시스템입니다.

## 주요 기능

- 프로젝트 정보 입력 및 관리
- AI 기반 자동 견적 생성
- 견적서 수정 및 미리보기
- 엑셀 파일 형식으로 견적서 저장
- 다국어 지원 (한국어/영어)

## 시스템 요구사항

- Python 3.8 이상
- OpenAI API 키
- Windows 10 이상 / macOS / Linux

## 설치 방법

1. 저장소 클론
```bash
git clone [repository_url]
cd ai_estimation
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
- `.env` 파일을 생성하고 다음 내용을 추가:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4
```

## 실행 방법

```bash
python src/main.py
```

## 프로젝트 구조

```
ai_estimation/
├── src/
│   ├── main.py              # 메인 애플리케이션
│   ├── ui/                  # UI 관련 모듈
│   │   ├── main_window.py
│   │   ├── project_input_widget.py
│   │   └── estimate_view_widget.py
│   ├── core/               # 핵심 비즈니스 로직
│   │   └── estimate_generator.py
│   ├── utils/              # 유틸리티 함수
│   │   └── logger.py
│   └── config/             # 설정 관련
│       └── settings.py
├── requirements.txt        # 의존성 패키지
├── .env                    # 환경 변수
└── README.md              # 프로젝트 문서
```

## 사용 방법

1. 프로그램 실행 후 프로젝트 정보 입력
   - 프로젝트명
   - 프로젝트 유형
   - 클라이언트 정보
   - 예상 기간
   - 요구사항
   - 기술 스택

2. "견적서 생성" 버튼 클릭
   - AI가 입력된 정보를 분석하여 견적서 자동 생성

3. 생성된 견적서 검토 및 수정
   - 항목별 금액 조정
   - 항목 추가/삭제

4. 견적서 저장
   - 엑셀 파일 형식으로 저장
   - 저장된 파일은 `estimates` 디렉토리에서 확인 가능

## 문제 해결

### 자주 발생하는 문제

1. OpenAI API 연결 오류
   - API 키가 올바르게 설정되었는지 확인
   - 인터넷 연결 상태 확인

2. 견적서 생성 실패
   - 입력된 정보가 충분한지 확인
   - 로그 파일에서 상세 오류 확인

### 로그 확인
- 로그 파일은 `logs/app.log`에서 확인 가능
- 오류 발생 시 로그를 참고하여 문제 해결

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 LICENSE 파일을 참고하세요.

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 연락처

프로젝트 관리자: [이름] - [이메일]

프로젝트 홈페이지: [URL] 