# Daily Log — AdInsight Agent

> 매일 저녁 10분 적립 루틴 (`portfolio_template.md` 부록 A).
> 한 줄이라도 좋다. 가장 위에 최근 날짜.

## 루틴
```
매일 저녁 10분:
1. 오늘 한 작업을 한 줄로 이 파일에 append (가장 위에)
2. 수치가 나왔으면 metrics/run_results.jsonl 또는 docs/portfolio_draft.md 에 기록
3. 캡처할 화면이 있으면 docs/images/NN_topic.png 에 저장
4. README 의 "Phase 진행도" 체크박스 업데이트

매주 금요일 30분:
1. 이번 주 수치를 docs/portfolio_draft.md 의 빈 자리에 반영
2. 실패 사례가 있으면 agent/eval/failure_cases.md (또는 phase별 문서) 에 정리
3. 다음 주 Phase 우선순위 정리
```

매일 10분 × 10주 = 16시간 → 프로젝트 끝에 몰아서 정리하는 40시간을 아낍니다.

---

## 2026-04-19 (Sat)
- **Phase 1 코드 완료 (가이드 모드 첫 세션)**
  - 가이드 모드 전환 결정: Yeon 이 프로덕션 파일 직접 타이핑, Claude 는 설명·리뷰
  - 8개 파일 직접 작성: smoke DAG / postgres init SQL·sh / airflow requirements+Dockerfile / superset Dockerfile+config / docker-compose.yml
  - `docker compose config --quiet` YAML 검증 통과 (error 0건)
  - 문서: ADR 001, README Quick Start 갱신, 세션 로그 03
  - 학습: Airflow DAG 구조, CeleryExecutor vs Thread, CMD vs CMD-SHELL, YAML anchor, \gexec 트릭
  - **다음**: `cp .env.example .env` → `make up` → smoke DAG 트리거 → Phase 2

## 2026-04-16 (Wed)
- **부트스트랩 (Phase 0)**
  - 폴더 스켈레톤 + CLAUDE.md + Makefile + pyproject(uv) + .env.example + 메트릭 인프라 셋업
  - 세션 로그 시스템 도입 (`docs/session_log/`)
  - **포트폴리오 워크플로 셋업**: CLAUDE.md 에 *포트폴리오 First* + *Teaching-First* 원칙 추가, `docs/portfolio_draft.md` (Phase별 빈 자리), `docs/daily_log.md` (이 파일), `docs/images/` 신설
  - 산출물: `metrics/run_results.jsonl` 1줄 (recorder smoke test)
- **다음**: Phase 1 — docker-compose 작성 (블루프린트 §5 Phase 1 프롬프트)

<!--
한 줄 양식 예:
## YYYY-MM-DD (Day)
- (Phase X) 무엇을 했나, 무엇이 막혔나, 어떤 수치가 나왔나
- 다음: 무엇을 할 차례
-->
- 2026-04-20 Session 04: Phase 1 스택 기동 완료. make up 10.7s, 8컨테이너 healthy, Smoke DAG 1s 성공. 버그 3개 디버깅 (ARG 스코프·chmod·볼륨 재초기화). GitHub 푸시.
