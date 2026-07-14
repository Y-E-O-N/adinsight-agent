# Text2SQL LLM Decision Guide

**Date**: 2026-07-09
**Phase**: Phase 6 — Text2SQL v2 provider tuning
**Purpose**: LLM이 자연어 질문을 SQL로 바꾸기 전에 적용해야 하는 결정 절차.

이 문서는 `CLAUDE.md`처럼 작업 원칙을 고정하기 위한 LLM-facing guide다. SQL 생성 모델은 이 절차를 내부적으로 적용하되, 긴 사고과정을 사용자에게 출력하지 않는다. JSON `reason`에는 최종 판단 근거만 짧게 남긴다.

## Core Principle

질문을 바로 SQL로 바꾸지 않는다. 먼저 metric, grain, 기간, 정렬, limit, 필터, 사용 가능 테이블을 확인한다. 기준이 없거나 데이터에 없는 metric은 만들어내지 않는다.

## Decision Protocol

| Step | Check | Required Behavior |
|---:|---|---|
| 1 | Intent | 질문이 creator, campaign ROI, prediction monitor 중 어느 분석인지 분류한다. |
| 2 | Grain | 결과 단위가 creator, campaign, objective, region, snapshot, tier 중 무엇인지 정한다. |
| 3 | Metric | 사용자가 요구한 metric이 rulebook 또는 schema context에 정의되어 있는지 확인한다. |
| 4 | Metric availability | metric이 없으면 SQL을 만들지 말고 `not_answerable`로 응답한다. 가능한 대체 지표가 있으면 reason에 제안한다. |
| 5 | Period | 기간 조건이 있는지 확인한다. 없으면 defaults를 적용한다. |
| 6 | Default disclosure | default 기간이나 대체 metric을 쓰는 경우, 최종 reason 또는 natural-language answer에 반드시 명시한다. |
| 7 | Table selection | rulebook 기준으로 가장 좁고 안전한 allowed table을 고른다. |
| 8 | Filter | boolean flag, threshold, latest snapshot, objective, region 같은 조건을 명시한다. |
| 9 | Sort and limit | ranking/list 질문에는 deterministic `order by`와 explicit `limit`를 둔다. |
| 10 | Validate answerability | allowed schema, metric, period 처리, SQL safety가 모두 충족될 때만 `answerable`로 둔다. |

## Missing-Condition Defaults

| Missing Input | Default | Required Disclosure |
|---|---|---|
| Period missing for creator/campaign summary questions | Full collected dataset | “기간 조건이 없어 전체 수집 기간 기준”이라고 명시한다. |
| Period missing for prediction monitor questions | Latest snapshot only | `max(scoring_snapshot_date)` 기준이라고 명시한다. |
| Top N missing in ranking question | Top 10 | “Top N이 없어 기본 Top 10 적용”이라고 명시한다. |
| Metric is vague, such as “best” | No default metric | `not_answerable`; 구체 metric을 요청한다. |
| Threshold missing for words like high/often | Use rulebook only if defined | rulebook에 정의가 없으면 threshold를 임의로 만들지 않는다. |
| Period requested but selected allowed table has no date column | Not answerable | 기간 필터를 적용할 수 없다고 설명한다. |

## Unavailable Metric Policy

| Requested Metric | Current Status | Required Behavior |
|---|---|---|
| views / 조회수 | Not available in the allowed Text2SQL schema | Do not fabricate. Return `not_answerable` and suggest likes/comments engagement as an alternative. |
| impressions / 노출수 | Not available | Do not fabricate. Suggest supported engagement or campaign ROI metrics. |
| clicks / 클릭수 | Not available | Do not fabricate. Suggest supported engagement or payment conversion metrics. |
| real sales / actual merchant revenue | Not available; current payment data is synthetic | Do not claim real sales. Use synthetic net payment only when appropriate. |
| exact paid sponsorship proof | Not available | Use sponsored candidate wording only. |

## Metric Substitution Policy

- Metric substitution is allowed only when the user explicitly accepts it or the question already names the supported metric.
- “조회수 높은 creator” must not be silently converted to engagement ranking.
- If the user asks for “engagement” or accepts a substitute for views, use likes/comments based metrics.
- When using substitute engagement, say it is not views.

Supported substitute examples:

| User Need | Supported Alternative |
|---|---|
| 조회수 높은 creator | `coalesce(avg_likes_count_clean, 0) + coalesce(avg_comments_count, 0)` as a creator-level engagement proxy, only after user accepts substitution. |
| 조회수 높은 post | Not supported in the current allowed Text2SQL tables. |
| 광고 성과 좋은 campaign | Ask for ROAS, net payment, payment events, or ROI review target if the metric is unspecified. |

## Period Policy

| Table / Domain | Period Behavior |
|---|---|
| `ai_native.ai_creator_sponsored_summary` | No date column in the allowed table. If no period is provided, use full collected dataset. If a specific period is requested, refuse unless a date-enabled model is added. |
| `ai_native.ai_campaign_roi_summary` | Campaign start/end columns exist, but positive eval defaults to all campaign rows unless the question explicitly asks for a period. |
| `marts.mart_campaign_roas_prediction_monitor` | For “latest”, always use `max(scoring_snapshot_date)`. |

## SQL Generation Requirements

- Use PostgreSQL syntax.
- Use only allowed tables and columns from schema context.
- Use `SELECT` or `WITH` only.
- Never generate write SQL.
- Use deterministic `order by` before every `limit`.
- For latest prediction monitor queries, include the latest snapshot filter.
- For unavailable metrics, return `not_answerable` instead of generating approximate SQL.

## Natural-Language Answer Requirements

When rows are returned, the answer must mention:

- metric definition used,
- period/default used,
- ranking direction and limit,
- substitute metric if any,
- synthetic benchmark limitation for ROAS/payment when relevant.

Do not overstate certainty. For keyword-based sponsored detection, say “candidate” or “suspected”, not confirmed advertising.

## Example: Unsupported Views Question

User question:

```text
가장 조회수 높은 크리에이터 10명만 뽑아줘.
```

Correct decision:

- Grain: creator.
- Metric: views.
- Metric availability: views is not available in the allowed Text2SQL schema.
- Period: missing, but metric absence blocks SQL first.
- Result: `not_answerable`.

Correct JSON:

```json
{
  "answerability": "not_answerable",
  "sql": null,
  "expected_tables": [],
  "reason": "Views are not available in the allowed schema. Ask whether to use likes/comments engagement as a substitute and specify a period, or default to the full collected dataset."
}
```

If the user accepts engagement as a substitute:

```sql
select
    creator_username,
    coalesce(avg_likes_count_clean, 0) + coalesce(avg_comments_count, 0) as avg_engagement_proxy
from ai_native.ai_creator_sponsored_summary
order by avg_engagement_proxy desc, creator_username asc
limit 10
```

The natural-language answer must say:

```text
조회수 컬럼이 없어 likes/comments 기반 engagement proxy로 대체했고, 기간 조건이 없어 전체 수집 기간 기준으로 계산했습니다.
```
