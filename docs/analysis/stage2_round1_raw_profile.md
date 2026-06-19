# Stage 2 Round 1 Raw Data Profile

**Date**: 2026-05-27
**Phase**: Phase 2 — Stage 2 Round 1 결과 해석
**Dataset**: `raw.ig_posts`, `raw.ig_post_sources`
**DAG run**: `ig_collect_round1` / `manual__2026-05-27T07:52:48+00:00`

## 1. 목적

Round 1의 목적은 단순히 데이터를 많이 모으는 것이 아니라, Instagram 수집 파이프라인이 실제 운영 흐름처럼 동작하는지 확인하는 것이다.

이번 프로파일링은 아래 질문에 답한다.

- Airflow DAG는 성공했는가?
- raw layer에 멱등 적재가 되었는가?
- seed별 수집량은 충분한가?
- raw 데이터에서 바로 보이는 품질 리스크는 무엇인가?
- 다음 수집 전에 어떤 판단을 해야 하는가?

## 2. 실행 요약

| 항목 | 값 |
|---|---:|
| requested posts | 2,000 |
| collected items | 49 |
| inserted posts | 29 |
| updated posts | 20 |
| final `raw.ig_posts` | 49 |
| final `raw.ig_post_sources` | 49 |
| DAG state | success |

해석:

- **파이프라인 건강성은 확인됨**: DAG trigger, Apify call, raw upsert, source lineage insert, metrics 기록까지 성공했다.
- **데이터 충분성은 부족함**: `resultsLimit` 합계 2,000건 대비 실제 반환은 49건이다.
- **멱등성은 작동함**: 기존 Stage 1 smoke 20건은 `updated=20`으로 처리됐고, 신규 29건만 insert됐다.

## 3. 기준 SQL

### 3.1 source별 수집량

```sql
SELECT
    source_hashtag,
    COUNT(*) AS source_links,
    COUNT(DISTINCT post_id) AS distinct_posts
FROM raw.ig_post_sources
GROUP BY source_hashtag
ORDER BY source_hashtag;
```

결과:

| source_hashtag | source_links | distinct_posts |
|---|---:|---:|
| 뷰티 | 18 | 18 |
| 올리브영 | 1 | 1 |
| 다이소화장품 | 30 | 30 |

관찰:

- `#올리브영`은 요청 1,000건 대비 1건만 반환됐다.
- `#다이소화장품`은 Stage 1의 기존 20건과 신규 10건이 합쳐져 30건이 됐다.
- seed 간 동일 게시물 중복은 현재 없다.

### 3.2 raw 품질 요약

```sql
SELECT
    COUNT(*) AS posts,
    COUNT(*) FILTER (WHERE caption IS NULL OR btrim(caption) = '') AS empty_caption,
    COUNT(*) FILTER (WHERE likes_count = -1) AS hidden_likes,
    COUNT(*) FILTER (WHERE posted_at IS NULL) AS missing_posted_at,
    COUNT(DISTINCT owner_username) AS distinct_owners
FROM raw.ig_posts;
```

결과:

| posts | empty_caption | hidden_likes | missing_posted_at | distinct_owners |
|---:|---:|---:|---:|---:|
| 49 | 2 | 16 | 0 | 46 |

관찰:

- caption이 비어 있는 게시물이 2건 있다.
- `likes_count = -1`인 게시물이 16건이다. raw에서는 원본을 보존하고, staging에서 `NULL` 또는 별도 flag로 정리한다.
- `posted_at` 누락은 없다.
- 작성자 46명 / 게시물 49건이라 특정 계정 쏠림은 크지 않다.

### 3.3 게시물 유형 분포

```sql
SELECT
    post_type,
    product_type,
    COUNT(*) AS posts
FROM raw.ig_posts
GROUP BY post_type, product_type
ORDER BY posts DESC, post_type;
```

결과:

| post_type | product_type | posts |
|---|---|---:|
| Sidecar | carousel_container | 43 |
| Image | feed | 6 |

관찰:

- 대부분 carousel 게시물이다.
- `Video` 또는 `clips` 타입은 이번 49건에는 없다.
- 향후 staging에서는 carousel 여부가 engagement 해석에 영향을 줄 수 있다.

### 3.4 광고/협찬 키워드와 caption 패턴

```sql
SELECT
    COUNT(*) FILTER (
        WHERE caption ~* '(광고|협찬|제품제공|제품지원|AD|sponsored)'
    ) AS ad_keyword_posts,
    COUNT(*) FILTER (WHERE caption ~ '#') AS hashtag_caption_posts,
    COUNT(*) FILTER (WHERE caption ~ '@') AS mention_caption_posts
FROM raw.ig_posts;
```

결과:

| ad_keyword_posts | hashtag_caption_posts | mention_caption_posts |
|---:|---:|---:|
| 20 | 41 | 22 |

관찰:

- 광고/협찬 후보 게시물이 20건이다.
- caption 내 hashtag가 있는 게시물은 41건이다.
- mention이 있는 게시물은 22건이다.
- 다음 staging 단계에서 `is_sponsored_candidate`, `caption_hashtag_count`, `mention_count` 같은 파생 컬럼 후보가 생긴다.

### 3.5 source별 품질 차이

```sql
SELECT
    s.source_hashtag,
    COUNT(*) AS links,
    COUNT(*) FILTER (WHERE p.caption IS NULL OR btrim(p.caption) = '') AS empty_caption,
    COUNT(*) FILTER (WHERE p.likes_count = -1) AS hidden_likes,
    COUNT(*) FILTER (
        WHERE p.caption ~* '(광고|협찬|제품제공|제품지원|AD|sponsored|gift)'
    ) AS ad_keyword_posts,
    COUNT(DISTINCT p.owner_username) AS distinct_owners
FROM raw.ig_post_sources s
JOIN raw.ig_posts p ON p.id = s.post_id
GROUP BY s.source_hashtag
ORDER BY s.source_hashtag;
```

결과:

| source_hashtag | links | empty_caption | hidden_likes | ad_keyword_posts | distinct_owners |
|---|---:|---:|---:|---:|---:|
| 뷰티 | 18 | 2 | 4 | 4 | 16 |
| 올리브영 | 1 | 0 | 0 | 0 | 1 |
| 다이소화장품 | 30 | 0 | 12 | 17 | 29 |

관찰:

- `#다이소화장품`은 광고/협찬 후보 비중이 높다.
- `#뷰티`는 더 넓은 seed라 잡음이 섞일 가능성이 있다.
- `#올리브영`은 현재 반환량이 너무 낮아 분석 seed로 쓰기 어렵다.

### 3.6 반복 작성자

```sql
SELECT
    p.owner_username,
    COUNT(*) AS posts,
    array_agg(DISTINCT s.source_hashtag ORDER BY s.source_hashtag) AS sources
FROM raw.ig_posts p
JOIN raw.ig_post_sources s ON s.post_id = p.id
GROUP BY p.owner_username
HAVING COUNT(*) > 1
ORDER BY posts DESC, p.owner_username;
```

결과:

| owner_username | posts | sources |
|---|---:|---|
| mienne_.92 | 2 | {뷰티} |
| sewooda.co | 2 | {뷰티} |
| tag_official_kr | 2 | {다이소화장품} |

관찰:

- 현재는 계정 반복 쏠림이 크지 않다.
- `tag_official_kr`처럼 공식/브랜드 성격 계정은 향후 blacklist 또는 account type 분류 후보가 된다.

## 4. 운영 관점 해석

이번 Round 1은 실패가 아니다. 다만 성공 기준을 둘로 나누어 봐야 한다.

| 평가 축 | 결과 | 의미 |
|---|---|---|
| pipeline health | 성공 | Airflow, Apify call, Postgres upsert, lineage, metrics 기록이 연결됨 |
| data sufficiency | 부족 | 요청량 대비 실제 반환량이 낮아 seed/Actor 전략 재검토 필요 |
| idempotency | 성공 | 기존 20건 update, 신규 29건 insert |
| raw observability | 개선됨 | seed별 수집량, hidden likes, sponsored 후보를 SQL로 확인 가능 |

로컬 구현과 AWS 대응:

| 로컬 구현 | AWS 대응 서비스 | 차이 |
|---|---|---|
| Airflow Docker Compose | Amazon MWAA | 로컬은 직접 컨테이너 운영, MWAA는 managed scheduler/worker 제공 |
| Postgres raw schema | Amazon RDS 또는 Redshift raw/staging schema | 로컬은 단일 Postgres, AWS는 운영 DB/분석 DW 분리 가능 |
| `metrics/run_results.jsonl` | CloudWatch Logs / S3 audit log | 로컬은 파일 append, AWS는 중앙 로그/객체 저장소에 적재 |
| Apify API call | 외부 SaaS API integration | AWS 안의 managed service가 아니라 외부 데이터 공급원 |

## 5. 다음 판단

당장 추가 자료 수집이 목표가 아니라면, 다음 작업은 수집량을 늘리는 것이 아니라 **현재 49건으로 분석 기준을 설계하는 것**이다.

추천 순서:

1. raw에서 staging으로 넘길 컬럼 후보를 정한다.
2. `likes_count = -1` 처리 규칙을 정한다.
3. 광고/협찬 후보 탐지 규칙을 정한다.
4. 공식 계정/브랜드 계정 노이즈 처리 기준을 정한다.
5. 그 다음에 필요하면 seed 확장 또는 Actor 옵션 점검으로 돌아간다.

## 6. 이번 단계에서 배운 개념

- **데이터 프로파일링**: 적재된 raw 데이터를 SQL로 요약해 품질, 분포, 누락, 이상치를 확인하는 작업.
- **Pipeline health vs data sufficiency**: DAG 성공과 분석 가능한 데이터셋 확보는 다른 성공 기준이다.
- **Lineage**: `raw.ig_post_sources`를 통해 게시물이 어떤 seed hashtag에서 왔는지 추적한다.
- **Raw 보존 원칙**: `likes_count = -1`처럼 이상해 보이는 값도 raw에서는 바꾸지 않고, staging에서 의미 있는 컬럼으로 정리한다.
