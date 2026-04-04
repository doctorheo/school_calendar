# School Calendar

학교 학사일정을 수집해 Google Calendar 이벤트로 옮기기 위한 Python 프로젝트입니다.

## 개요

이 프로젝트는 다음 흐름으로 동작합니다.

1. 학교 학사일정 페이지 HTML을 가져옵니다.
2. 일정 데이터를 파싱합니다.
3. 기존 Google Calendar에 이벤트를 넣거나 새 캘린더를 만든 뒤 이벤트를 저장합니다.

현재 기준으로 구현 상태는 다음과 같습니다.

- `src/fetch/school_schedule.py`: 학교 일정 페이지 HTML 수집
- `src/parse/schedule_parser.py`: 일정 목록 파싱
- `src/calendar/google_calendar.py`: Google Calendar 생성 및 이벤트 등록
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

## 환경 변수

`.env` 파일 또는 셸 환경변수로 아래 값을 설정합니다.

```bash
GOOGLE_SERVICE_ACCOUNT_FILE=src/calendar/service-account.json
GOOGLE_CALENDAR_ID=
GOOGLE_CALENDAR_NAME=
```

- `GOOGLE_SERVICE_ACCOUNT_FILE`: 서비스 계정 JSON 경로
- `GOOGLE_CALENDAR_ID`: 기존 캘린더에 저장할 때 사용
- `GOOGLE_CALENDAR_NAME`: 새 캘린더 생성 시 기본 이름으로 사용

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

또는

```bash
./scripts/run.sh
```

기존 캘린더에 저장:

```bash
python -m src.main --calendar-id "your_calendar_id@group.calendar.google.com"
```

새 캘린더를 생성한 뒤 저장:

```bash
python -m src.main --create-calendar --calendar-name "학교 일정"
```

모듈 단독 실행도 가능합니다.

```bash
python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --create-calendar --calendar-name "학교 일정"
```

`--calendar-id`와 `--create-calendar`는 동시에 사용할 수 없습니다.

## 현재 한계

- 서비스 계정이 만든 캘린더는 개인 Google Calendar UI에 바로 보이지 않을 수 있음
- 예외 처리 및 로깅이 아직 단순함
- 테스트 코드 없음
- `pyproject.toml` 설명 및 의존성 정리 필요

## 향후 작업

- 캘린더 공유 및 권한 설정 자동화 검토
- 일정 갱신 로직 개선
- 테스트 코드 추가

## 문서

브랜치 운영 규칙은 아래 문서를 확인하세요.

- [BRANCH_POLICY.md](BRANCH_POLICY.md)
- [AGENT_BRANCH_PR_GUIDE.md](AGENT_BRANCH_PR_GUIDE.md)
