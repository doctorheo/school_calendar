# Google Calendar 생성 기능 구현 계획

## 목표

현재 프로젝트는 기존 Google Calendar ID에 이벤트를 추가할 수 있다. 여기에 새 캘린더를 생성한 뒤 그 캘린더에 학사일정을 저장하는 흐름을 추가한다.

## 구현 항목

- Google Calendar 생성 함수 추가
- 새 캘린더 생성 후 이벤트 저장 orchestration 추가
- CLI 옵션 확장
- 환경변수 예시와 README 정리
- 실행 스크립트 갱신

## 구현 순서

1. `src/calendar/google_calendar.py`에 `create_calendar()` 추가
2. `create_calendar_and_events()`를 추가해 새 캘린더 생성과 일정 저장을 연결
3. `src/main.py`와 `src/calendar/google_calendar.py` CLI에 `--create-calendar`, `--calendar-name` 옵션 추가
4. `--calendar-id`와 `--create-calendar` 동시 사용 시 에러 처리 추가
5. `.env.example`, `README.md`, `scripts/run.sh`를 실제 사용 흐름에 맞게 수정
6. CLI help와 모듈 실행 기준으로 수동 검증

## 검증 포인트

- 새 캘린더 생성 응답에서 `id`가 반환되는지 확인
- 생성된 `id`로 이벤트 저장이 이어지는지 확인
- 기존 `calendar_id` 기반 흐름이 깨지지 않는지 확인
- 충돌 인자 조합에서 명확한 에러가 나는지 확인
