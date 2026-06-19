# ADR 002 — Phase 3 모델링: Layered Mart 우선, OBT는 보류

**날짜**: 2026-06-09
**상태**: 수용(Accepted)
**결정자**: Yeon (with Codex, Session 10)

---

## 배경

Phase 3에서 Round 1 Instagram 수집 데이터 49건을 dbt로 모델링했다.

현재 raw 데이터는 작지만, 프로젝트의 최종 목표는 아래 흐름이다.

1. raw 원본 보존
2. staging 정제
3. intermediate 재사용 계산
4. marts BI 분석 테이블
5. 이후 Phase 4 AI-Native mart와 Phase 6 Text2SQL Agent 연결

이 시점에서 모델링 방향을 결정해야 했다.

- **선택지 A: Kimball star schema를 바로 만든다**
  - `dim_creator`, `dim_source_hashtag`, `fct_ig_post`, `fct_creator_sponsored_daily` 등
- **선택지 B: OBT(One Big Table)를 만든다**
  - Superset이 바로 읽는 wide table 하나로 빠르게 대시보드 구성
- **선택지 C: layered mart pattern을 먼저 만든다**
  - staging → intermediate → mart로 역할을 나누되, 완전한 star schema는 데이터가 늘어난 뒤 확장

---

## 결정

**Phase 3에서는 layered mart pattern을 우선 채택**한다.

구체적으로 아래 구조를 만든다.

| layer | model | materialization | 역할 |
|---|---|---|---|
| staging | `stg_ig_posts` | view | raw Instagram 게시물 1건을 분석 가능한 row로 정리 |
| intermediate | `int_ig_post_source_quality` | view | source hashtag별 수집 품질 요약 |
| intermediate | `int_ig_sponsored_candidates` | view | caption 키워드 기반 광고/협찬 후보 게시물 분리 |
| intermediate | `int_ig_owner_activity` | view | 작성자별 게시물/협찬 후보/engagement 요약 |
| marts | `mart_creator_sponsored_summary` | table | Superset과 포트폴리오가 직접 읽는 creator 단위 분석 테이블 |

OBT 하나로 모든 컬럼을 합치는 방식은 보류한다.

완전한 Kimball star schema는 데이터가 늘어나고 campaign/advertiser/payment 도메인이 들어온 뒤 Phase 4 이후에 확장한다.

---

## 근거

### 선택한 이유 (Layered Mart)

| 항목 | 설명 |
|---|---|
| **현재 데이터 규모** | Round 1은 49 posts / 49 source links로 작다. 지금 `dim_*`, `fact_*`를 과하게 쪼개면 모델 수 대비 분석 이득이 낮다. |
| **학습 효율** | staging, intermediate, mart의 역할 차이를 실제 dbt lineage와 tests로 설명할 수 있다. |
| **품질 검증** | 각 레이어에 `schema.yml` descriptions와 data tests를 붙여 모델 계약을 검증할 수 있다. |
| **BI 연결성** | `mart_creator_sponsored_summary`가 Superset dataset/chart/dashboard로 바로 연결된다. |
| **AI-Native 확장성** | Phase 4에서 LLM 친화 mart를 만들 때 intermediate 계산을 재사용할 수 있다. |

### 대안과 기각 이유

| 대안 | 기각 이유 |
|---|---|
| **즉시 Kimball star schema** | 현재 Instagram 단일 채널 49건이라 fact/dim 분리 근거가 약하다. campaign/advertiser/payment이 들어온 뒤 설계하는 편이 자연스럽다. |
| **OBT 하나로 Superset 직행** | 빠르게 차트는 만들 수 있지만, raw→staging→intermediate→mart lineage와 테스트 가능한 변환 계약을 보여주기 어렵다. |
| **raw SQL view만 수동 생성** | dbt docs, tests, lineage, 재현 가능한 run/test 기록을 잃는다. 포트폴리오 증거로 약하다. |

---

## 트레이드오프

| 장점 | 단점 |
|---|---|
| 작은 데이터에서도 레이어별 책임을 설명 가능 | 모델 수가 OBT보다 많아 초반 작성량이 증가 |
| dbt lineage screenshot이 면접 자료가 됨 | 완전한 star schema 경험은 아직 보여주지 못함 |
| intermediate 재사용으로 Phase 4 확장 쉬움 | 현재 mart는 Instagram creator 단위에 한정 |
| Superset chart와 직접 연결 가능 | 데이터가 작아 ranking/비율의 대표성은 낮음 |

**운영 환경과의 차이**: 실제 광고 분석 warehouse에서는 campaign, advertiser, creator, date, region 같은 conformed dimension과 fact table을 더 엄격히 분리한다. 이번 결정은 **Phase 3 학습/포트폴리오 단계**에 맞춘 중간 결정이며, 데이터 범위가 넓어지면 star schema로 확장한다.

---

## 결과

Phase 3 종료 시점의 결과:

| metric | value |
|---|---:|
| dbt models | 5 |
| staging models | 1 |
| intermediate models | 3 |
| mart models | 1 |
| dbt tests | 44/44 pass |
| dbt run time | 0.18s |
| dbt test time | 0.37s |
| creator mart rows | 46 |
| creator review rows | 24 |
| sponsored candidate posts | 21 |

생성된 포트폴리오 자산:

- `docs/images/03_dbt_lineage.png`
- `docs/images/phase3_creator_review_table.jpg`
- `dashboards/superset_exports/adinsight_creator_review_export.zip`
- `docs/analysis/stage3_mart_creator_sponsored_summary_design.md`

---

## 향후 확장

데이터가 늘어나면 아래 star schema 후보로 확장한다.

| future model | 역할 |
|---|---|
| `dim_creator` | creator profile, platform, region, follower bucket |
| `dim_source_hashtag` | 수집 seed와 source taxonomy |
| `dim_date` | 일자/주차/월/타임존 분석 |
| `fct_ig_post` | 게시물 단위 fact |
| `fct_creator_sponsored_daily` | creator × date 단위 광고/협찬 후보 성과 fact |

Phase 4 AI-Native mart에서는 Text2SQL Agent가 이해하기 쉬운 컬럼명, synonyms, example questions를 별도 `ai_native` 레이어에 추가한다.

---

## Known Limitations

- Round 1 데이터가 49건이라 현재 mart의 ranking과 비율은 대표성이 낮다.
- `is_sponsored_candidate`는 caption 키워드 기반 후보값이며 실제 광고 여부를 확정하지 않는다.
- 아직 advertiser/campaign/payment 도메인이 없어 진짜 광고 ROI star schema는 구현하지 않았다.
- OBT 대비 모델 수가 많아 초보자에게는 초기 구조가 복잡해 보일 수 있다.
