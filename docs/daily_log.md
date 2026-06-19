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

## 2026-06-16 (Tue)
- **Phase P A+C 전략 재설계 반영**
  - `docs/guides/project_redesign_master_guide.md` 기준으로 프로젝트 피치를 결제 전환·ROAS 예측·Text2SQL Agent 중심으로 재정렬
  - `CLAUDE.md`, `README.md`, `docs/adinsight_project_blueprint.md`, `docs/guides/project_redesign_master_guide.md` 갱신
  - 신규 ADR: `docs/adr/003-redesign-ac-strategy.md`
  - **다음**: Phase 2B Apify 운영 등급 자동화 파이프라인 착수

## 2026-06-11 (Thu)
- **Phase 4 Text2SQL 평가 질문셋 초안**
  - `dbt docs generate` 실행 후 manifest에서 `marts -> ai_native` lineage와 dbt `meta` 적재 확인
  - `agent/eval/text2sql_questions.yml`에 bilingual 평가 질문 10개와 expected SQL 작성
  - expected SQL 10개 실행 확인: row count 범위 3~44건
  - 문서: `docs/analysis/stage4_text2sql_eval_questions.md`
  - **다음**: YAML을 읽어 expected SQL row count를 비교하는 evaluator 구현
- **Phase 4 AI-Native mart 첫 모델 구축**
  - `ai_native.ai_creator_sponsored_summary` 추가: creator 1명당 1행, 46 rows
  - `meta.grain`, model/column-level `meta.synonyms`, `meta.example_questions` 작성
  - 전체 dbt 검증 갱신: `dbt run` 6/6 pass, `dbt test` 50/50 pass
  - 설계 노트: `docs/analysis/stage4_ai_creator_sponsored_summary_design.md`
  - **다음**: dbt docs lineage에서 `marts -> ai_native` 확장 확인 후 Text2SQL 평가 질문셋 초안 작성
- **Phase 4 시작 준비**
  - Session 10의 Next session 지점을 Phase 4 AI-Native mart 설계로 정리
  - Phase 3 마감 자산 확인: dbt lineage screenshot, Superset screenshot/export, ADR 002
  - 신규 시작 노트: `docs/analysis/stage4_ai_native_mart_start_plan.md`
  - **다음**: `ai_native.ai_creator_sponsored_summary` 설계 전 `meta.grain`, `meta.synonyms`, `meta.example_questions` 범위 결정

## 2026-06-09 (Tue)
- **Phase 3 creator mart + Superset 포트폴리오 자산 완료**
  - dbt models 5개 (`staging=1`, `intermediate=3`, `marts=1`), 전체 `dbt test` 44/44 pass
  - creator mart: 46 creators / review 대상 24 creators / sponsored 후보 게시물 21건
  - Superset dataset·chart·dashboard 생성, screenshot과 export ZIP 저장
  - 메트릭: `metrics/run_results.jsonl`에 `p3.creator_mart_superset_complete` append
  - **다음**: dbt docs lineage screenshot 또는 ADR 002 작성 후 Phase 4 AI-Native mart 설계

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
- 2026-04-28 Session 05: Phase 2 Stage 0 완료. Apify $29 구독, 시드 3개 합의 (#뷰티/#올리브영/#다이소화장품), 가이드 모드 5파일 작성. 로컬·Airflow 양쪽 20건 수집 성공. PYTHONPATH 함정 디버깅 1회. 응답 스키마 적립.
