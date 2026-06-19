# Data Generation

이 디렉터리는 AdInsight Agent의 합성 데이터를 생성한다.

## Phase 2C 목적

Phase 2C의 합성 결제 데이터는 실제 결제 성과를 주장하기 위한 데이터가 아니다.
실제 결제 데이터에 접근할 수 없는 상황에서, 광고 집행부터 결제 전환까지의
ETL, dbt 모델링, ROAS 계산, ML feature 생성, Text2SQL 평가 흐름을 검증하기 위한
재현 가능한 synthetic benchmark다.

## 현재 생성 범위

- `data_generation/generators/payment_events.py`
  - `raw.syn_post_campaign_attributions` 1건 기준 synthetic payment event를 생성한다.
  - 실제 Apify 수집 데이터에서 계산한 `observed_engagement_count/tier`와 campaign budget으로 기대 결제 건수를 계산한다.
  - 현재 Apify 공개 수집 데이터에서 안정적으로 제공되지 않는 views/impressions/clicks는 사용하지 않는다.
  - 실제 결제 건수는 Poisson 분포로 샘플링한다.
  - 결제 금액은 lognormal 분포로 샘플링한다.

현재 smoke generator는 `SEED = 1125`를 사용한다. 전체 Phase 2C generator로 확장할 때는
프로젝트 문서의 seed 정책과 맞춰 하나의 seed 값으로 통일한다.

## 모델링 가정

현재 `payment_events.py`의 결제 전환 수식은 아래 가설을 사용한다.

| 가정 | 코드 표현 | 의미 |
|---|---|---|
| 관측 engagement가 높으면 결제 발생 가능성이 높다 | `PAYMENT_TIER_BASE_RATES` + `log1p(observed_engagement_count)` | likes/comments만으로 만든 약한 구매 관심 proxy다. |
| 광고비 규모가 크면 결제 발생 기회가 늘어난다 | `sqrt(campaign_budget_krw / reference_budget)` | 예산 효과는 선형이 아니라 완만하게 증가한다고 둔다. |
| 캠페인 목적에 따라 결제 기대값이 다르다 | `PAYMENT_OBJECTIVE_MULTIPLIERS` | conversion > traffic > awareness 순서로 결제 근접도가 높다고 둔다. |
| 카테고리별 전환 성향이 다르다 | `CATEGORY_CONVERSION_MULTIPLIERS` | beauty/fashion/food 카테고리의 구매 전환 차이를 둔다. |
| 실제 paid partnership 표식이 있으면 전환 가능성이 조금 높다 | `PAYMENT_PAID_PARTNERSHIP_MULTIPLIER` | 광고/협찬 표식이 있는 게시물은 캠페인 연결 가능성이 높다고 둔다. |

현재 카테고리 배수는 아래 범위만 사용한다.

```python
CATEGORY_MULTIPLIERS = {
    "beauty": 1.8,
    "fashion": 1.3,
    "food": 1.1,
}
```

현재 지역/통화 매핑은 아래 범위만 사용한다.

```python
REGION_CURRENCY = {
    "KR": ("KRW", 1.0),
    "JP": ("JPY", 9.5),
}
```

## 분포 선택

| 값 | 분포 | 이유 |
|---|---|---|
| 결제 건수 | Poisson | 게시물 단위 기간 안에서 발생하는 event count로 본다. |
| 결제 금액 | Lognormal | 결제 금액은 0보다 크고, 소액이 많으며, 고액 결제가 드문 오른쪽 꼬리 분포다. |
| 환불 여부 | Bernoulli | 각 결제 이벤트가 환불되는 yes/no 사건이다. |

## 한계와 검증 계획

이 합성 데이터의 가정은 실제 비즈니스 법칙이 아니다. 실제 데이터가 들어오면 아래를
검증해야 한다.

- observed engagement tier와 conversion/payment count의 관계가 실제로 양의 상관을 갖는지 확인한다.
- campaign budget과 payment count의 관계가 현재처럼 완만한 증가 형태인지 확인한다.
- campaign objective별 결제 근접도 차이가 실제로 유지되는지 확인한다.
- beauty/fashion/food 카테고리 배수가 실제 결제 데이터에서도 유지되는지 calibration한다.
- Poisson 분포보다 분산이 큰 과분산이 관측되면 negative binomial 분포로 교체한다.

면접/README에서는 이 데이터를 실제 결제 데이터처럼 설명하지 않는다. 이 데이터는
분포 가정을 명시한 synthetic benchmark이며, 실제 운영 데이터로 전환할 때는 계수와
분포를 재검증해야 한다.

## 검증 명령

```bash
uv run python data_generation/generators/payment_events.py
uv run python data_generation/generators/payment_events.py --from-postgres --limit 100 --write-postgres
uv run ruff check data_generation/generators/payment_events.py
```
