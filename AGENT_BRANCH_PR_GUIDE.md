# 에이전트 브랜치 커밋 및 PR 생성 가이드

## 목적
- 에이전트가 브랜치 전략에 맞춰 일관되게 작업하고 PR까지 생성할 수 있도록 표준 절차를 제공한다.

## 브랜치 규칙
- 기준 브랜치: `main`, `dev`
- 기능 브랜치: `feat/agent-name/feature-name`
- 기타 브랜치: `etc/task-name`
- 수정 브랜치: `fix/agent-name/issue-name`
- 원칙: 작업 시작 전에 반드시 새 브랜치를 먼저 생성한다. `main`, `dev` 브랜치에 직접 커밋하지 않는다. 다만 최초 커밋인 경우는 `main`에 진행한다. 커밋 메시지는 한글로 작성한다.

## 사전 확인
1. 현재 브랜치 확인: `git branch --show-current`
2. 작업 트리 확인: `git status`
3. 최신 `dev` 반영:
   - `git checkout dev`
   - `git pull origin dev`

## 브랜치 생성
### 기능 작업
```bash
git checkout -b feat/<agent-name>/<feature-name>
```

### 버그 수정
```bash
git checkout -b fix/<agent-name>/<issue-name>
```

### 기타 작업
```bash
git checkout -b etc/<task-name>
```

## 변경사항 커밋
1. 변경 확인: `git status`, `git diff`
2. 커밋 전 실행 요건 확인:
   - 실행 스크립트를 `scripts/*.sh` 형태로 별도 작성했는지 확인한다.
   - 각 에이전트를 실행하는 스크립트가 준비되어 있는지 확인한다.
   - 새로 정의한 모듈에 직접 실행 진입점(예: `if __name__ == "__main__":`)이 있는지 확인한다.
3. 스크립트/모듈 실행 테스트를 수행한다.
4. 스테이징: `git add <path>` 또는 `git add .`
5. 커밋:
```bash
git commit -m "변경 목적 중심으로 간결하게 작성"
```

## 원격 푸시
```bash
git push -u origin HEAD
```

## PR 생성
### 원칙
- `feat/*`, `fix/*`, `etc/*` 브랜치는 `dev`로 PR을 생성한다.
- PR 제목은 변경 이유가 드러나게 작성한다.
- PR 본문에는 변경 요약과 테스트 결과를 포함한다.

### GitHub CLI 예시
```bash
gh pr create --base dev --head HEAD \
  --title "기능 요약" \
  --body "## 변경 내용
- 핵심 변경 1
- 핵심 변경 2

## 테스트
- [ ] 로컬 테스트 완료
- [ ] 회귀 영향 확인"
```

## 작업 완료 체크리스트
- [ ] 브랜치가 네이밍 규칙(`feat/*`, `fix/*`, `etc/*`)을 준수함
- [ ] `dev` 최신 상태 기반으로 작업함
- [ ] 실행 스크립트를 `scripts/*.sh`로 별도 작성함
- [ ] 에이전트별 실행 스크립트를 사전 준비함
- [ ] 신규 모듈에 `if __name__ == "__main__":` 진입점을 작성함
- [ ] 스크립트/모듈 실행 테스트를 완료함
- [ ] 변경 파일만 스테이징 및 커밋함
- [ ] 원격 브랜치 푸시 완료
- [ ] `dev` 대상 PR 생성 완료
