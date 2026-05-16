# School Calendar

학교 학사일정을 가져와 Google Calendar에 종일 이벤트로 동기화하는 Python 프로젝트입니다.

## 기능

- 학교 일정 HTML 조회
- 일정 파싱 및 JSON 저장
- 같은 제목의 연속 일정 병합
- Google Calendar 이벤트 생성
- 새 캘린더 생성 및 읽기 권한 공유

## 요구 사항

- Python 3.13 이상
- `uv`
- Google 서비스 계정 JSON

## 설치

```bash
uv sync
```

## 설정

기본 설정 파일: [src/config/school_calendar.yml](/Users/jeongwoo/Documents/문서%20-%20MacBook%20Air%20%282%29/Projects/school_calendar/src/config/school_calendar.yml)

주요 항목:

- `schedule.url`
- `schedule.parsed_output`
- `calendar.create`
- `calendar.id`
- `calendar.name`
- `calendar.timezone`
- `calendar.credentials_path`
- `calendar.share_with_email`
- `calendar.share_role`

제약:

- `calendar.create: true`와 `calendar.id`는 동시에 사용할 수 없습니다.
- 새 캘린더 생성 시 `calendar.name`이 필요합니다.
- 기존 캘린더 사용 시 `calendar.id`가 필요합니다.

환경 변수:

```env
GOOGLE_SERVICE_ACCOUNT_FILE=/absolute/path/to/service-account.json
GOOGLE_CALENDAR_ID=your-calendar-id@group.calendar.google.com
GOOGLE_CALENDAR_NAME=학교 일정
GOOGLE_CALENDAR_SHARE_WITH_EMAIL=someone@example.com
```

## 실행

전체 워크플로:

```bash
uv run python -m src.main
```

또는:

```bash
bash scripts/run.sh
```

HTML만 조회:

```bash
uv run python -m src.fetch.school_schedule
```

파싱만 실행:

```bash
uv run python -m src.parse.schedule_parser --config src/config/parse_schedule.yml
```

파싱된 JSON으로 캘린더 동기화:

```bash
uv run python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --calendar-id "your-calendar-id@group.calendar.google.com" --credentials-path "/absolute/path/to/service-account.json"
```

새 캘린더 생성 후 동기화:

```bash
uv run python -m src.calendar.google_calendar --input src/parse/output/parsed_schedule.json --create-calendar --calendar-name "학교 일정" --credentials-path "/absolute/path/to/service-account.json"
```

읽기 권한 부여:

```bash
uv run python -m src.calendar.google_calendar --config src/config/calendar_access.yml --grant-reader-access
```

Streamlit 월간 캘린더 뷰어:

```bash
bash scripts/run_streamlit.sh
```

## 한계

- 기존 이벤트 수정 및 삭제 동기화 미지원
- 테스트 코드 없음
- `requirements.txt`보다 `uv` 기준 사용이 정확함

## 참고

- [src/config/school_calendar.yml](/Users/jeongwoo/Documents/문서%20-%20MacBook%20Air%20%282%29/Projects/school_calendar/src/config/school_calendar.yml)
- [src/config/parse_schedule.yml](/Users/jeongwoo/Documents/문서%20-%20MacBook%20Air%20%282%29/Projects/school_calendar/src/config/parse_schedule.yml)
- [src/config/calendar_access.yml](/Users/jeongwoo/Documents/문서%20-%20MacBook%20Air%20%282%29/Projects/school_calendar/src/config/calendar_access.yml)
