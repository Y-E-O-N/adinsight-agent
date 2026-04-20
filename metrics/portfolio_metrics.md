# AdInsight Agent — Portfolio Metrics

> 자동/수동 누적. Phase 종료 시 `metrics/run_results.jsonl` 에서 집계되어 갱신됩니다.
> README 의 "포트폴리오 메트릭" 섹션이 이 파일을 참조합니다.

마지막 갱신: **TBD** (Phase 0 진행 중)

---

## Pipeline (Phase 2)
- 합성 데이터 규모: **TBD** rows / **TBD** GB (Parquet)
- 생성 재현성: seed `SEED=42`, 소요 **TBD** s

## dbt (Phase 3 + 4)
- 모델 수: **TBD** (staging / intermediate / marts / ai_native)
- 테스트 수: **TBD** (커버리지 **TBD** %)
- 문서 커버리지: **TBD** %
- 최장 모델 실행: **TBD**
- snapshot 수: **TBD**

## Query Optimization (Phase 5)

| Query | Before | After | Δ | 기법 |
|---|---|---|---|---|
| TBD | — | — | — | — |

상세 로그: `metrics/query_optimization_log.md`

## Text2SQL BI Agent (Phase 6)
- 평가셋: **TBD** 질문 (한 / 영 / 중 / 태)
- 최고 조합: **TBD** + **TBD**
  - Execution Accuracy: **TBD %**
  - Exact Match: **TBD %**
  - Latency p95: **TBD ms**
  - 평균 비용: **$ TBD / query**
- 안전성: Refuse Rate **TBD %**, DELETE/DROP 차단 **TBD %**

## LLM Weekly Report (Phase 7)
- 자동 리포트 회차: **TBD**
- 평균 생성 시간: **TBD** s
- 평균 토큰 비용: **$ TBD / 회**
- halucination 비율 (수동 검증): **TBD %**

## Traffic Experiments (Phase 6 + 5)
- Text2SQL Agent: **TBD** concurrent req 까지 p95 **TBD** s
- Superset: **TBD** concurrent dashboard load 평균 **TBD** s

---

## Phase 진행도
- [x] Phase 0 — 부트스트랩
- [ ] Phase 1 — Docker 스택
- [ ] Phase 2 — 합성/공개 데이터
- [ ] Phase 3 — dbt staging/intermediate/marts
- [ ] Phase 4 — ai_native ⭐
- [ ] Phase 5 — Superset + 쿼리 최적화
- [ ] Phase 6 — Text2SQL Agent ⭐
- [ ] Phase 7 — 주간 LLM 리포트
- [ ] Phase 8 — 품질·관측·CI
- [ ] Phase 9 — 문서·데모·면접
