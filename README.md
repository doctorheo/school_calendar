# School Calendar

학교 학사일정을 수집해 Google Calendar 이벤트로 옮기기 위한 Python 프로젝트입니다.

## 개요

이 프로젝트는 다음 흐름으로 동작합니다.

1. 학교 학사일정 페이지 HTML을 가져옵니다.
2. 일정 데이터를 파싱합니다.
3. 파싱한 일정을 캘린더 이벤트 형식으로 변환합니다.

현재 기준으로 구현 상태는 다음과 같습니다.

- `src/fetch/school_schedule.py`: 학교 일정 페이지 HTML 수집
- `src/parse/schedule_parser.py`: 일정 목록 파싱
- `src/calendar/google_calendar.py`: 캘린더 연동 자리만 있음
- `src/main.py`: 전체 실행 흐름 연결

## 프로젝트 구조

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── src
│   ├── main.py
│   ├── fetch
│   │   ├── school_schedule.py
│   │   └── output
│   │       └── school_schedule.html
│   ├── parse
│   │   └── schedule_parser.py
│   └── calendar
│       └── google_calendar.py
├── BRANCH_POLICY.md
└── AGENT_BRANCH_PR_GUIDE.md
```

## 요구 사항

- Python 3.13 이상

## 설치

의존성 파일이 아직 정리되지 않은 상태라면 먼저 아래 기준으로 환경을 맞춥니다.

```bash
uv sync
```

또는

```bash
pip install -r requirements.txt
```

## 사용 방법

### 1. HTML 가져오기

```bash
python src/fetch/school_schedule.py
```

옵션 예시:

```bash
python src/fetch/school_schedule.py --url "학교 일정 URL" --output "저장할 파일 경로"
```

### 2. 일정 파싱

`src/parse/schedule_parser.py`는 저장된 HTML을 읽어 일정 목록을 추출합니다.

### 3. 전체 흐름 실행

```bash
python src/main.py
```

현재 `google_calendar.py`는 실제 Google Calendar API 연동 대신 입력된 일정을 그대로 반환하도록 되어 있습니다.

## 현재 한계

- Google Calendar API 연동 미구현
- 예외 처리 및 로깅 부족
- 테스트 코드 없음
- `pyproject.toml` 설명 및 의존성 정리 필요

## 향후 작업

- Google Calendar API 인증 및 이벤트 생성 구현
- 일정 중복 방지 로직 추가
- 환경변수 기반 설정 분리
- 테스트 코드 작성

## 문서

브랜치 운영 규칙은 아래 문서를 확인하세요.

- [BRANCH_POLICY.md](BRANCH_POLICY.md)
- [AGENT_BRANCH_PR_GUIDE.md](AGENT_BRANCH_PR_GUIDE.md)
