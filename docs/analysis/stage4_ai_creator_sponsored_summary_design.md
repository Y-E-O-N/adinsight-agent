# Stage 4 Design — ai_creator_sponsored_summary

**Date**: 2026-06-11
**Phase**: Phase 4 — AI-Native Mart
**Model**: `ai_native.ai_creator_sponsored_summary`

## 1. Purpose

`ai_creator_sponsored_summary`는 기존 BI mart인 `marts.mart_creator_sponsored_summary`를 Text2SQL Agent가 더 쉽게 찾고 해석할 수 있게 만든 첫 AI-Native mart다.

BI mart는 Superset 대시보드에서 사람이 읽기 좋은 요약 테이블이고, AI-Native mart는 자연어 질문을 SQL로 바꿀 때 schema retrieval과 column selection이 쉬운 테이블이다.

## 2. Input

| item | value |
|---|---|
| Source model | `marts.mart_creator_sponsored_summary` |
| Source grain | creator 1명당 1행 |
| AI-Native grain | creator 1명당 1행 |
| Unique key | `creator_username` |

첫 버전은 row grain을 바꾸지 않는다. Phase 4의 목표는 새 집계 로직보다 semantic metadata 설계와 lineage 확장이다.

## 3. Naming decision

`owner_username`과 `owner_full_name`은 AI-Native layer에서 각각 `creator_username`, `creator_display_name`으로 바꾼다.

이유:

- 사용자는 자연어 질문에서 `owner`보다 `creator`, `influencer`, `작성자`, `크리에이터`를 더 자주 쓸 가능성이 높다.
- Text2SQL Agent가 질문의 명사와 컬럼명을 직접 매칭하기 쉬워진다.
- 원본 lineage는 `ref('mart_creator_sponsored_summary')`로 유지되므로 mart layer의 의미를 잃지 않는다.

## 4. Metadata placement

| metadata | placement | reason |
|---|---|---|
| `meta.grain` | model-level | 모델 전체의 row 단위를 설명한다. |
| `meta.synonyms` | model-level + column-level | 테이블 검색용 동의어와 컬럼 선택용 동의어가 다르다. |
| `meta.example_questions` | model-level | Agent evaluation과 schema retrieval 예시로 재사용한다. |
| column descriptions | column-level | SQL 생성 시 컬럼 의미를 좁게 해석하게 한다. |

## 5. Initial example questions

- Which creators should we review first for sponsored content?
- Show creators with at least one sponsored candidate post.
- Which influencers have a high sponsored candidate rate?
- 협찬 후보 게시물이 있는 크리에이터를 보여줘.
- 광고 의심 비율이 높은 작성자는 누구야?

## 6. Local-to-AWS mapping

| local implementation | AWS managed service equivalent | difference |
|---|---|---|
| dbt model in Docker/Airflow worker | AWS Glue Data Quality or dbt on ECS/MWAA | 로컬은 컨테이너 안에서 직접 실행하고, AWS는 orchestration과 runtime을 managed service가 담당한다. |
| Postgres schemas `marts`, `ai_native` | Redshift or Aurora PostgreSQL schemas | 로컬은 단일 Postgres, AWS는 분석 workload와 운영 workload에 맞춰 storage/compute를 분리할 수 있다. |
| dbt YAML `meta` | Data catalog business glossary / semantic layer metadata | 로컬은 YAML이 source of truth이고, AWS에서는 Glue Data Catalog나 Bedrock Agent schema hints로 확장할 수 있다. |

## 7. Next checkpoint

1. `dbt run --select ai_creator_sponsored_summary`
2. `dbt test --select ai_creator_sponsored_summary`
3. 전체 `dbt run && dbt test` 재검증
4. dbt docs lineage에서 `marts -> ai_native` 확장 확인
