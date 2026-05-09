# School Calendar

학교 학사일정을 수집해 Google Calendar 이벤트로 옮기기 위한 Python 프로젝트입니다.

## 개요

이 프로젝트는 다음 흐름으로 동작합니다.

1. 학교 학사일정 페이지 HTML을 가져옵니다.
2. 일정 데이터를 파싱해 JSON으로 저장할 수 있습니다.
3. 같은 제목의 연속 일정을 병합합니다.
4. 기존 Google Calendar에 이벤트를 넣거나 새 캘린더를 만든 뒤 일정을 저장합니다.

현재 기준으로 구현 상태는 다음과 같습니다.

- `src/fetch/school_schedule.py`: 학교 일정 페이지 HTML 수집
- `src/parse/schedule_parser.py`: 일정 목록 파싱 및 JSON 저장
- `src/calendar/merge_events.py`: 같은 제목의 연속 일정 병합
- `src/calendar/google_calendar.py`: Google Calendar 생성, 이벤트 등록, 중복 스킵
- `src/config/app_config.py`: YAML 설정 로드
- `src/main.py`: 전체 실행 흐름 연결

## 프로젝트 구조

```text
.
├── main.py
├── pyproject.toml
├── requirements.txt
├── scripts
│   └── run.sh
├── src
│   ├── config
│   │   ├── app_config.py
│   │   └── school_calendar.yml
│   ├── main.py
│   ├── calendar
│   │   ├── google_calendar.py
│   │   └── merge_events.py
│   ├── fetch
│   │   ├── school_schedule.py
│   │   └── output
│   │       └── school_schedule.html
│   └── parse
│       └── schedule_parser.py
├── BRANCH_POLICY.md
└── AGENT_BRANCH_PR_GUIDE.md
```

## 요구 사항

- Python 3.13 이상

## 설치

권장 방식:

```bash
uv sync
```

Google Calendar 연동을 사용하려면 서비스 계정 JSON 파일이 필요합니다.

`.env` 예시:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
GOOGLE_CALENDAR_NAME=학교 일정
```

## 환경 변수

`.env` 파일 또는 셸 환경변수로 아래 값을 설정할 수 있습니다.

- `GOOGLE_SERVICE_ACCOUNT_FILE`: 서비스 계정 JSON 경로
- `GOOGLE_CALENDAR_ID`: 기존 캘린더에 이벤트를 넣을 때 사용할 캘린더 ID
- `GOOGLE_CALENDAR_NAME`: 새 캘린더 생성 시 기본 이름

기본 실행 입력값은 환경변수 대신 YAML config 파일에서 관리합니다.

## 설정 파일

기본 설정 파일은 `src/config/school_calendar.yml` 입니다.

```yaml
schedule:
  url: "https://bunwon-e.goegh.kr/bunwon-e/ps/schdul/selectSchdulMainList.do?mi=2547"
  parsed_output: "src/parse/output/parsed_schedule.json"

calendar:
  create: true
  name: "학교 일정"
  description: "학교 학사일정 자동 동기화"
  timezone: "Asia/Seoul"
  credentials_path: "src/calendar/service-account.json"
  share_with_email: "jeongwoohoho@gmail.com"
  share_role: "reader"
```

- `schedule.url`: 학사일정 페이지 URL
- `schedule.parsed_output`: 파싱 결과 JSON 저장 경로
- `calendar.create`: 새 캘린더 생성 여부
- `calendar.id`: 기존 캘린더에 저장할 때 사용할 캘린더 ID
- `calendar.name`: 새 캘린더 생성 시 사용할 이름
- `calendar.description`: 새 캘린더 설명
- `calendar.timezone`: 캘린더와 종일 이벤트 시간대
- `calendar.credentials_path`: 서비스 계정 JSON 파일 경로
- `calendar.share_with_email`: 생성하거나 사용하는 캘린더를 공유할 Google 계정 이메일
- `calendar.share_role`: 공유 권한. `reader`, `writer`, `owner`, `freeBusyReader` 중 하나

`calendar.create: true`와 `calendar.id`는 동시에 사용할 수 없습니다.

## 사용 방법

### 1. HTML 가져오기

```bash
uv run python -m src.fetch.school_schedule
```

옵션 예시:

```bash
uv run python -m src.fetch.school_schedule --url "학교 일정 URL" --output "저장할 파일 경로"
```

### 2. 일정 파싱

저장된 HTML에서 일정 목록을 읽어 JSON으로 저장합니다.

```bash
uv run python -m src.parse.schedule_parser --config src/config/parse_schedule.yml
```

기본 출력 파일:

- `src/parse/output/parsed_schedule.json`

파서 전용 YAML 설정 예시:

```yaml
schedule:
  html_input: "src/fetch/output/school_schedule.html"
  parsed_output: "src/parse/output/parsed_schedule.json"
```

### 3. 전체 흐름 실행

기본 YAML 설정 파일 사용:

```bash
uv run python -m src.main
```

다른 설정 파일 사용:

```bash
uv run python -m src.main --config src/config/custom.yml
```

이 명령은 다음을 한 번에 처리합니다.

- 학교 일정 페이지 HTML 조회
- 일정 파싱
- 파싱 결과 JSON 저장
- 같은 제목의 연속 일정 병합
- Google Calendar 이벤트 생성 또는 새 캘린더 생성 후 이벤트 저장

### 4. 파싱 결과로만 캘린더 동기화

이미 저장된 JSON이 있으면 아래 명령으로 캘린더 생성만 따로 실행할 수 있습니다.

```bash
uv run python -m src.calendar.google_calendar
```

옵션 예시:

```bash
uv run python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --create-calendar --calendar-name "학교 일정" --credentials-path "/absolute/path/to/service-account.json"
```

특정 사용자에게 캘린더 `reader` 권한만 부여하려면:

```bash
uv run python -m src.calendar.google_calendar --config src/config/calendar_access.yml --grant-reader-access
```

이 경우 아래 설정값을 YAML에서 읽습니다.

- `calendar.id`
- `calendar.credentials_path`
- `calendar.share_with_email`

예시 파일:

- `src/config/calendar_access.yml`

### 5. 간단 실행 스크립트

```bash
bash scripts/run.sh
```

현재 스크립트는 HTML 수집만 수행합니다.

## 동작 방식

- 파서는 일정 제목, 시작일, 종료일을 추출합니다.
- 병합 유틸리티는 같은 제목의 연속 날짜 범위를 하나의 일정으로 합칩니다.
- Google Calendar 등록 시 종일 이벤트 형식으로 생성합니다.
- 이미 생성된 일정은 내부 키를 기준으로 조회해 중복 생성을 건너뜁니다.

## 현재 한계

- 테스트 코드 없음
- 예외 처리 및 로깅이 단순함
- `pyproject.toml` 설명 문구가 아직 기본값임
- `requirements.txt`가 비어 있어 설치 문서를 `uv` 기준으로 정리하는 편이 안전함
- 서비스 계정이 만든 캘린더는 개인 Google Calendar UI에 바로 보이지 않을 수 있음

## 향후 작업

- 기존 Google Calendar 이벤트 갱신 및 삭제 동기화
- 캘린더 공유 및 권한 설정 자동화 검토
- 설정 구조와 실행 스크립트 정리
- 테스트 코드 작성
- 의존성 및 배포 방식 정리

## 문서

브랜치 운영 규칙은 아래 문서를 확인하세요.

- [BRANCH_POLICY.md](BRANCH_POLICY.md)
- [AGENT_BRANCH_PR_GUIDE.md](AGENT_BRANCH_PR_GUIDE.md)
