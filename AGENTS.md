# AdInsight Agent — Codex Context

> 매 Codex 세션 시작 시 이 파일을 먼저 읽어주세요.
> 1급 참조 문서: `CLAUDE.md` · `docs/adinsight_project_blueprint.md` · `docs/lecture/SK AX/adinsight_application_plan.md` · `docs/session_log/README.md`

---

## 0. 기본 원칙

이 저장소의 운영 기준은 `CLAUDE.md` 와 동일합니다. Codex 세션에서도 다음 원칙을 그대로 적용합니다.

- 포트폴리오 First: 코드 변경은 문서·메트릭·스크린샷·ADR 같은 면접 자산으로 환산합니다.
- Teaching-First: Yeon 이 목적·구조·동작을 이해할 수 있게 한국어로 설명합니다.
- 데이터 불변 규칙: raw 원본 보존, idempotent 파이프라인, UTC 저장, 시크릿 커밋 금지.
- 문서 언어는 한국어 우선, 코드 식별자는 영어 snake_case 를 따릅니다.
- 답변 언어: 사용자가 어떤 언어로 질문하더라도 Codex 의 본문 답변은 반드시 한국어로 작성합니다.
- 영어 질문 표현 보조: 사용자가 한국어로 질문하면, 매 응답 상단에 `English dev phrasing:` 한 줄을 먼저 표시하고, 영어 사용 개발자라면 같은 질문을 어떻게 물었을지 자연스러운 영어 문장으로 제시합니다.
  - 예: `English dev phrasing: What does DDL mean in this project?`
  - 이 줄은 학습 보조용이며, 그 아래 설명·검토·작업 결과는 한국어로 작성합니다.

## 1. Codex 작업 방식

- 작업 시작 시 `CLAUDE.md` 의 현재 Phase 와 직전 세션 요약을 확인합니다.
- `docs/session_log/` 의 최신 1~2개 세션 로그를 읽고 `Next session — start here` 를 확인합니다.
- Phase 설계·포트폴리오 스토리 정리 시 `docs/lecture/SK AX/adinsight_application_plan.md` 의 L0/L1/L2, 메타데이터, Self-Service, 운영 모니터링 적용안을 함께 확인합니다.
- 각 Phase 작업을 설명할 때 현재 로컬 구현이 AWS의 어떤 서비스에 대응되는지, 그리고 로컬 구현과 AWS managed service의 차이점을 함께 안내합니다.
- 코드 변경 전에는 기존 패턴을 먼저 읽고, 변경 범위를 작게 유지합니다.
- 사용자가 명시적으로 "대신 써줘" 라고 하거나 문서류 작업인 경우 Codex 가 직접 파일을 수정할 수 있습니다.
- 프로덕션 코드 신규 작성은 `CLAUDE.md` 의 Guided-Coding 원칙을 우선합니다.

## 2. 세션 로그 저장 규칙

이 프로젝트는 세션 기록을 두 층으로 나눕니다.

- **기본 대화 로그**: `logs/session_YYYYMMDD_HHMMSS.log`
  - 예: `logs/session_20260504_105009.log`
  - shell 설정의 `codex()` wrapper 로 Codex 를 시작하면 현재 작업 디렉터리 아래에 즉시 생성되고, 사용자/assistant 대화가 추가될 때마다 append 됩니다.
  - 지침, 사고 과정, 도구 호출/출력은 저장하지 않습니다.
  - 이미 열린 Codex 세션에서는 별도 터미널에서 `make session-log` 를 실행해 현재 세션을 미러링합니다.
  - 사용자/assistant 대화 전문에 가까운 기록입니다.
  - `logs/` 는 `.gitignore` 대상이므로 Git 에 커밋하지 않습니다.
- **Codex 내부 원본 로그**: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`
  - Codex 가 자동 저장하는 도구 호출 포함 원본 기록입니다.
  - 기본 보관 위치로 쓰지 않고, 필요할 때 `logs/session_*.log` 형식으로 변환해 참조합니다.
- **프로젝트 공식 요약 로그**: `docs/session_log/YYYY-MM-DD_session-NN_<topic>.md`
  - 다음 세션 시작과 포트폴리오 정리를 위한 사람이 읽기 좋은 요약입니다.

### 세션 종료 시

1. 현재 대화 전문은 기본적으로 `logs/session_YYYYMMDD_HHMMSS.log` 형식으로 남깁니다.
2. `docs/session_log/YYYY-MM-DD_session-NN_<topic-kebab-case>.md` 를 새로 작성합니다.
3. `Operator` 는 `Yeon (with Codex)` 또는 실제 사용한 도구명으로 적습니다.
4. `Goals / Done / Decisions / Files changed / Concepts taught / Portfolio assets added / Open questions / Metrics / Next session — start here` 를 채웁니다.
5. `docs/session_log/README.md` 의 Index 에 한 줄을 추가합니다.
6. 필요하면 `CLAUDE.md` 의 `직전 세션 요약` 도 갱신합니다.

## 3. 현재 Phase

현재 프로젝트 상태는 `CLAUDE.md` 의 `## 10. 현재 Phase` 를 기준으로 합니다.
