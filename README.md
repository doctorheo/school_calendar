# School Calendar

학교 학사일정을 가져와 Google Calendar에 종일 이벤트로 동기화하고, Streamlit 웹 애플리케이션을 통해 여러 학교의 일정을 통합/비교 조회할 수 있는 Python 프로젝트입니다.

## 기능

- **학교 일정 HTML 조회**: 학교 학사일정 페이지에서 일정을 동적으로 가져옵니다.
- **일정 파싱 및 JSON 저장**: HTML에서 날짜 및 일정 제목을 파싱하여 정형화된 JSON 데이터로 저장합니다.
- **연속 일정 병합**: 같은 제목의 연속된 일정을 시작일과 종료일이 포함된 하나의 이벤트 범위로 병합합니다.
- **Google Calendar 동기화**: 파싱된 일정을 Google Calendar에 종일 이벤트로 생성 및 동기화합니다.
- **캘린더 관리 및 권한 공유**: 새로운 구글 캘린더 생성 및 특정 사용자(이메일)에게 읽기 권한을 공유하는 기능을 제공합니다.
- **Streamlit 웹 대시보드**:
  - **개별 및 통합(비교) 모드**: 단일 학교의 일정 또는 여러 학교의 일정을 한눈에 모아보는 다중 학교 달력 뷰어(학교별 고유 색상 구분)를 제공합니다.
  - **동적 학교 추가**: 웹 인터페이스에서 학교 이름과 일정 URL만 입력하면 자동으로 데이터를 가져와 파싱, 병합 후 등록합니다.
  - **동적 학교 삭제**: 더 이상 조회하지 않는 학교 정보를 웹 UI에서 안전하게 제거합니다.

## 요구 사항

- Python 3.13 이상
- `uv` (Python 패키지 및 가상환경 관리 도구)
- Google 서비스 계정 JSON 키 파일 (Google Calendar API 연동 시 필요)

## 설치

```bash
uv sync
```

## 설정

### 1. Google 캘린더 및 API 설정
기본 설정 파일: [src/config/school_calendar.yml](src/config/school_calendar.yml)

주요 항목:
- `schedule.url`: 수집 대상 학교의 학사일정 URL
- `schedule.parsed_output`: 파싱 결과를 저장할 JSON 파일 경로
- `calendar.create`: 새 캘린더 생성 여부 (`true` / `false`)
- `calendar.id`: 연동할 기존 Google Calendar ID (생성 안 함 일 때 사용)
- `calendar.name`: 새로 생성할 캘린더 이름
- `calendar.timezone`: 캘린더 타임존 (기본값: `Asia/Seoul`)
- `calendar.credentials_path`: 서비스 계정 JSON 키 경로
- `calendar.share_with_email`: 캘린더를 공유할 Google 사용자 이메일
- `calendar.share_role`: 공유 대상의 권한 (기본값: `reader`)

**제약사항:**
- `calendar.create: true`인 경우 `calendar.id`를 동시에 지정할 수 없으며, `calendar.name`이 필수적입니다.
- 기존 캘린더를 사용할 경우 `calendar.create: false`로 설정하고 `calendar.id`를 제공해야 합니다.

### 2. 환경 변수 (`.env`)
환경 변수를 통해서도 주요 설정값을 재정의할 수 있습니다:
```env
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
GOOGLE_CALENDAR_NAME=학교 일정
GOOGLE_CALENDAR_SHARE_WITH_EMAIL=someone@example.com
```

### 3. Streamlit 학교 목록 설정
Streamlit 앱에서 노출될 학교 목록 설정 파일: [src/config/streamlit_schools.yml](src/config/streamlit_schools.yml)
- `default_school`: 앱 실행 시 기본으로 선택되어 노출될 학교 이름
- `schools`: 등록된 각 학교의 이름(`name`)과 병합된 일정 JSON 경로(`events_path`) 목록

## 실행

### 1. 전체 파이프라인 실행 (CLI)
웹 데이터 수집부터 파싱, Google Calendar 동기화까지 한 번에 실행합니다.

```bash
# 기본 설정을 사용한 실행
uv run python -m src.main

# 또는 쉘 스크립트 실행
bash scripts/run.sh
```

특정 설정 파일을 지정하여 다른 학교의 파이프라인을 실행할 수 있습니다:
```bash
# 번천초 파이프라인 예시
bash scripts/run_beoncheon.sh
```

### 2. 개별 모듈 실행

- **HTML 조회만 실행**:
  ```bash
  uv run python -m src.fetch.school_schedule
  ```

- **일정 파싱만 실행**:
  ```bash
  uv run python -m src.parse.schedule_parser --config src/config/parse_schedule.yml
  ```

- **연속 일정 병합만 실행**:
  ```bash
  uv run python -m src.calendar.merge_events --config src/config/merge_events.yml
  ```

- **Google Calendar 동기화만 실행 (파싱 데이터 기반)**:
  ```bash
  uv run python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --calendar-id "your-calendar-id@group.calendar.google.com" --credentials-path "/absolute/path/to/service-account.json"
  ```

- **새 캘린더 생성 및 동기화**:
  ```bash
  uv run python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --create-calendar --calendar-name "학교 일정" --credentials-path "/absolute/path/to/service-account.json"
  ```

- **캘린더 읽기 권한 설정**:
  ```bash
  uv run python -m src.calendar.google_calendar --config src/config/calendar_access.yml --grant-reader-access
  ```

### 3. Streamlit 웹 애플리케이션 실행
월간 캘린더 뷰어 및 학교 동적 추가/삭제 기능을 제공하는 웹 대시보드를 구동합니다.

```bash
bash scripts/run_streamlit.sh
```

## 한계 및 향후 개선 계획

- 기존 이벤트 수정 및 삭제에 대한 Google Calendar 양방향 동기화 미지원 (단방향 추가만 지원)
- 유닛 테스트 코드 부재

## 참고 파일 및 경로

- [src/config/school_calendar.yml](src/config/school_calendar.yml): 전체 파이프라인 설정
- [src/config/parse_schedule.yml](src/config/parse_schedule.yml): 일정 파서 설정
- [src/config/calendar_access.yml](src/config/calendar_access.yml): 구글 캘린더 권한 설정
- [src/config/streamlit_schools.yml](src/config/streamlit_schools.yml): Streamlit 학교 목록 설정
