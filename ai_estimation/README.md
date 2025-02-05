# AI 자동 견적 시스템

PySide6 기반의 GUI 애플리케이션으로, OpenAI API를 활용하여 프로젝트 견적을 자동으로 생성하고 관리하는 시스템입니다.

## 주요 기능

- 프로젝트 정보 입력 및 관리
- OpenAI API를 활용한 자동 견적 생성
- 견적서 수정 및 피드백 관리
- 엑셀 파일 형식으로 견적서 내보내기
- 프로젝트 데이터 저장 및 불러오기

## 시스템 요구사항

- Python 3.8 이상
- OpenAI API 키
- Windows 10 이상 (다른 OS에서도 동작 가능)

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/yourusername/ai-estimate-system.git
cd ai-estimate-system
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 값을 설정
```

## 실행 방법

```bash
python src/main.py
```

## 사용 방법

1. 프로젝트 정보 입력
   - 프로젝트명
   - 프로젝트 설명
   - 요구사항 목록
   - 예상 기간
   - 팀 규모

2. 견적 생성
   - "견적 생성" 버튼 클릭
   - AI가 자동으로 견적 생성

3. 견적서 확인 및 수정
   - 생성된 견적 확인
   - 필요한 경우 수정
   - 피드백 입력 가능

4. 견적서 내보내기
   - "엑셀로 내보내기" 버튼 클릭
   - 원하는 위치에 저장

## 개발자 정보

- 개발자: [Your Name]
- 이메일: [Your Email]
- 라이선스: MIT

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 