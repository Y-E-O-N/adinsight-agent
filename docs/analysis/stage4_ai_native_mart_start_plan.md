# Stage 4 Start Plan — AI-Native Mart

**Date**: 2026-06-11
**Phase**: Phase 4 — AI-Native Mart 설계 시작
**Starting point**: Phase 3 creator mart 완료 후 Text2SQL 친화 layer 설계

## 1. 현재 입력 자산

Phase 4의 첫 입력 모델은 아래 mart다.

| item | value |
|---|---|
| Source mart | `marts.mart_creator_sponsored_summary` |
| Grain | creator 1명당 1행 |
| Rows | 46 creators |
| Review 대상 | 24 creators |
| Sponsored 후보 게시물 | 21 posts |
| dbt tests | 44/44 pass |

관련 증거:

- `docs/images/03_dbt_lineage.png`
- `docs/images/phase3_creator_review_table.jpg`
- `dashboards/superset_exports/adinsight_creator_review_export.zip`
- `docs/adr/002-layered-mart-vs-obt.md`

## 2. Phase 4 목표

AI-Native mart는 일반 BI mart를 Text2SQL Agent가 더 잘 이해하도록 재구성한 layer다.

일반 mart가 "사람이 Superset에서 읽기 좋은 테이블"이라면, AI-Native mart는 "LLM이 자연어 질문을 SQL로 바꾸기 쉬운 테이블"을 목표로 한다.

이번 Phase 4 첫 모델 후보:

```text
ai_native.ai_creator_sponsored_summary
```

예상 입력:

```sql
select * from {{ ref('mart_creator_sponsored_summary') }}
```

## 3. 첫 설계 질문

다음 세션에서는 코드 작성 전에 아래를 먼저 결정한다.

1. `ai_native.ai_creator_sponsored_summary`를 mart의 단순 복사로 시작할지, LLM 친화 컬럼을 추가할지
2. `creator`, `influencer`, `작성자`, `크리에이터` 같은 동의어를 model-level `meta.synonyms`에 둘지, column-level meta에 둘지
3. 예시 질문을 한국어/영어 몇 개까지 넣을지
4. 현재 49건 데이터로 AI-Native layer를 시작할지, 추가 수집을 먼저 할지

## 4. 추천 1차 범위

작게 시작한다.

| file | role |
|---|---|
| `dbt/models/ai_native/ai_creator_sponsored_summary.sql` | Text2SQL 친화 creator summary 모델 |
| `dbt/models/ai_native/schema.yml` | descriptions + `meta.grain`, `meta.synonyms`, `meta.example_questions` |
| `docs/analysis/stage4_ai_creator_sponsored_summary_design.md` | 설계 노트 |

초기 컬럼은 Phase 3 mart와 거의 같게 둔다.

- `creator_username`
- `creator_display_name`
- `total_posts`
- `sponsored_candidate_posts`
- `sponsored_candidate_rate`
- `hidden_likes_rate`
- `has_engagement_signal`
- `included_in_creator_review`

컬럼명을 `owner_*`에서 `creator_*`로 바꾸는 이유는 자연어 질문에서 사용자가 "작성자"보다 "creator/크리에이터/influencer"라고 물을 가능성이 높기 때문이다.

## 5. 다음 세션 시작 명령

```bash
docker compose exec airflow-worker bash -lc "cd /opt/dbt && dbt run --profiles-dir /opt/dbt && dbt test --profiles-dir /opt/dbt"
```

통과 기준:

```text
dbt run: 5/5 pass
dbt test: 44/44 pass
```

## 6. Known Limitations

- 현재 raw 데이터는 49건이라 AI-Native mart의 정확도 평가에는 충분하지 않다.
- Phase 4의 첫 목표는 agent accuracy 측정이 아니라 semantic metadata 설계와 lineage 확장이다.
- 실제 Text2SQL 평가셋과 schema retrieval은 Phase 6에서 본격화한다.
