# SK AX 강의 메모 — AdInsight Agent 적용안

작성일: 2026-05-21
소스: `docs/lecture/SK AX/` 이미지 12장

## 1. 강의 핵심 요약

SK AX 발표의 핵심은 "데이터가 현업에 닿기까지" 필요한 통합 데이터·AI 플랫폼의 운영 원칙이다.

1. **AI 적용을 고려한 데이터 통합·정제**
   - 흩어진 데이터를 단일 형태로 통합한다.
   - 기술 메타데이터와 비즈니스 메타데이터를 결합해 즉시 활용 가능한 구조를 만든다.

2. **역할 기반 데이터 활용 체계**
   - 개별 요청 대응 방식에서 표준 프로세스로 전환한다.
   - 현업, 분석가, ML 엔지니어, 데이터 엔지니어가 같은 플랫폼 안에서 역할별 도구를 쓴다.

3. **운영 가드레일과 지속 모니터링**
   - 사전 정의된 정책으로 보안, 준수, 리소스 사용을 통제한다.
   - 중앙 모니터링으로 비용, 파이프라인 성공/실패, AI 사용량, 리소스를 추적한다.

## 2. 플랫폼 구조를 이 레포에 매핑

강의의 계층 구조는 AdInsight Agent의 현재 설계와 잘 맞는다.

| 강의 개념 | 강의 예시 | AdInsight Agent 적용 |
|---|---|---|
| Source | 내부 배치, 내부 실시간, 외부 API | Apify Instagram, 향후 YouTube/TikTok, SDV 합성 데이터 |
| Ingest & Store | DMS, Glue, S3, MWAA, Redshift | Airflow DAG, Postgres `raw`, 향후 Parquet/partition |
| L0 Lake | 원천 데이터 무손실 수집 및 원본 저장 | `raw.ig_posts.raw_payload`, 원본 JSONB 보존 |
| L1 DW | 분석가 중심 실험용 데이터 | dbt `staging`, `intermediate`, `marts` |
| L2 Mart | BI, LLM 등 현업 서비스 연결 데이터셋 | dbt `ai_native`, Superset dataset, Text2SQL Agent |
| Metadata Catalog | IT Meta + Biz Meta | dbt YAML descriptions, glossary, metric dictionary |
| Self-Service | 자연어 탐색, SQL, Notebook, 리포팅 | Text2SQL Agent, Superset dashboard, weekly LLM report |
| Guardrail | 리소스 표준, 권한, 비용 | read-only SQL, prompt/eval guardrail, token/cost logging |
| Monitoring | pipeline, GenAI/ML, infra | `metrics/run_results.jsonl`, Airflow logs, agent eval metrics |

## 3. AWS 서비스 대응표

이 프로젝트는 로컬 포트폴리오 환경이므로 AWS 서비스를 직접 쓰지 않는 것이 기본이다. 대신 각 Phase를 진행할 때 "이 로컬 구현이 AWS에서는 어떤 managed service에 해당하는가"를 같이 설명한다. 목적은 클라우드 실무 언어로 아키텍처를 설명할 수 있게 만드는 것이다.

| 프로젝트 구성요소 | 로컬 구현 | AWS 대응 서비스 | 핵심 차이 |
|---|---|---|---|
| 외부 API 수집 | Apify SDK, Python collector | AWS Lambda, AWS Glue Python Shell, Amazon EventBridge Scheduler | 로컬은 직접 실행·디버깅이 쉽고, AWS는 스케줄·확장·권한 관리가 managed로 제공된다. |
| 오케스트레이션 | Apache Airflow in Docker | Amazon MWAA | 로컬 Airflow는 비용이 낮고 학습에 좋지만, MWAA는 scheduler/worker 운영, 로그, IAM 연동을 AWS가 관리한다. |
| 원본 저장 L0 | Postgres `raw` schema, JSONB | Amazon S3, AWS Lake Formation, AWS Glue Data Catalog | Postgres raw는 단일 DB에서 빠르게 실험하기 좋고, S3 lake는 대용량·저비용·객체 저장과 카탈로그/권한 분리에 강하다. |
| 데이터 웨어하우스 L1 | Postgres + dbt | Amazon Redshift, Amazon Athena | Postgres는 로컬 재현성이 높고, Redshift/Athena는 대규모 분석, 분산 쿼리, 스토리지 분리에 강하다. |
| 변환 | dbt-postgres | AWS Glue, dbt on ECS/MWAA, Redshift SQL | dbt는 SQL 모델·테스트·문서화가 강하고, Glue는 Spark 기반 대규모 ETL과 AWS 통합이 강하다. |
| 메타데이터 카탈로그 | dbt YAML, glossary, docs | AWS Glue Data Catalog, Amazon DataZone, SageMaker Unified Studio Catalog | 로컬 메타데이터는 Agent context로 쓰기 쉽고, AWS 카탈로그는 조직 단위 검색·권한·승인 워크플로에 강하다. |
| BI 대시보드 | Apache Superset | Amazon QuickSight | Superset은 오픈소스 커스터마이징과 포트폴리오 증거에 좋고, QuickSight는 AWS 권한·SPICE·관리형 배포가 장점이다. |
| Text2SQL Agent | LangChain/LangGraph, pgvector | Amazon Bedrock Agent, Amazon Bedrock Knowledge Bases | 로컬 Agent는 내부 동작을 직접 설계·평가하기 좋고, Bedrock은 모델 접근, KB 연동, 보안 경계가 managed로 제공된다. |
| Vector DB | pgvector | Amazon OpenSearch Service, Aurora/RDS PostgreSQL pgvector, Bedrock Knowledge Bases | pgvector는 단일 Postgres 스택으로 단순하고, OpenSearch/Bedrock KB는 검색 규모와 운영 관리에 강하다. |
| ML/AI 실험 | Python scripts, notebooks 예정 | Amazon SageMaker AI, SageMaker Unified Studio | 로컬은 비용과 반복 속도가 좋고, SageMaker는 학습/배포/실험 관리/권한 통합이 강하다. |
| 모니터링 | `metrics/run_results.jsonl`, Airflow logs | Amazon CloudWatch, CloudTrail, Cost Explorer | 로컬 메트릭은 포트폴리오 기록에 적합하고, AWS는 조직 단위 로그·감사·비용 가시화를 제공한다. |
| 권한·가드레일 | read-only validator, env secret, SQL 제한 | IAM, Lake Formation, Service Control Policies, Bedrock Guardrails | 로컬은 코드 기반 정책이고, AWS는 계정·역할·리소스 단위 정책 강제가 가능하다. |

Phase를 진행할 때 설명 형식:

1. **현재 구현**: 이번에 만든 로컬 컴포넌트가 무엇인지 설명한다.
2. **AWS 대응**: 실제 AWS에서는 어떤 서비스 조합으로 대체되는지 설명한다.
3. **차이점**: 로컬 구현의 장점과 한계, AWS managed service의 장점과 trade-off를 말한다.
4. **포트폴리오 문장**: 면접에서 사용할 수 있는 한 문장으로 정리한다.

예시:

> "이번 `raw.ig_posts` 적재는 로컬에서는 Postgres `raw` schema와 JSONB로 구현하지만, AWS에서는 S3 + Glue Data Catalog + Lake Formation에 가까운 L0 lake 역할입니다. 로컬 Postgres는 재현성과 디버깅이 좋고, AWS lake는 대용량 원본 보존, 권한 분리, 카탈로그 검색에 강합니다."

## 4. 즉시 반영할 설계 원칙

### 4.1 L0/L1/L2 이름으로 현재 Phase 재해석

현재 Phase 2 Stage 1은 `raw.ig_posts` 적재이므로 강의 기준의 **L0 Lake** 구축이다.

- `raw.ig_posts`는 원본 보존 레이어로 유지한다.
- `raw_payload JSONB`를 반드시 유지한다.
- `likes_count = -1` 같은 외부 API 특이값은 raw에서 바꾸지 않고 staging에서 정규화한다.
- 수집 경로 추적을 위해 `source_hashtag`, `collected_at`, `updated_at`을 유지한다.

이후 Phase는 다음처럼 말할 수 있다.

| 프로젝트 Phase | 강의식 표현 | 산출물 |
|---|---|---|
| Phase 2 | L0 원천 수집·원본 저장 | `raw.ig_posts`, idempotent loader, Airflow load task |
| Phase 3 | L1 분석용 DW | dbt staging/intermediate/marts, tests, docs |
| Phase 4 | L2 AI-Native Mart | LLM 친화 OBT, semantic metadata, schema embeddings |
| Phase 5 | Self-Service BI | Superset dashboards |
| Phase 6 | Self-Service AI | Text2SQL Agent, eval, guardrail |
| Phase 8 | 운영 통제 | CI, data quality, monitoring, freshness |

### 4.2 메타데이터를 기능으로 취급

강의에서 가장 이식 가치가 큰 부분은 "메타데이터 기반 데이터 탐색"이다. 이 프로젝트에서는 메타데이터를 문서가 아니라 Agent 품질을 올리는 기능으로 설계해야 한다.

추가할 메타데이터:

- **IT Meta**: schema, table, column, data type, primary key, freshness, row count
- **Biz Meta**: 한국어 설명, 광고/인플루언서 도메인 용어, 계산식, 예시 질문
- **Agent Meta**: synonyms, safe SQL constraints, allowed joins, grain, metric owner

우선순위:

1. `dbt/models/staging/schema.yml`에 컬럼 설명과 테스트 추가
2. `dbt/models/marts/schema.yml`에 metric definition 추가
3. `dbt/models/ai_native/schema.yml`에 `meta.synonyms`, `meta.example_questions`, `meta.grain` 추가
4. Phase 6에서 이 YAML을 읽어 schema retriever와 prompt context로 사용

### 4.3 역할 기반 self-service를 포트폴리오 스토리로 만들기

강의의 역할 구분을 이 프로젝트 데모 시나리오로 바꾼다.

| 역할 | 프로젝트 데모 |
|---|---|
| 현업 사용자 | "올리브영 관련 게시물 중 반응률 높은 크리에이터는?" 자연어 질문 |
| 분석가 | dbt mart/Superset에서 CTR, ER, ROAS 비교 |
| ML 엔지니어 | caption, hashtag embedding 생성 및 추천 feature 활용 |
| 데이터 엔지니어 | Airflow DAG, idempotent loader, dbt test, lineage 관리 |

면접용 핵심 문장:

> "이 프로젝트는 단순 Text2SQL 데모가 아니라, raw 원본 보존부터 semantic metadata, BI mart, AI-native mart, guardrail, eval까지 이어지는 self-service analytics 플랫폼으로 설계했습니다."

## 5. Phase별 적용 로드맵

### Phase 2 Stage 1: L0 원본 저장 안정화

해야 할 일:

- `raw.ig_posts` DDL을 L0 원본 저장 레이어로 명확히 문서화
- `INSERT ... ON CONFLICT` 멱등 loader 검증
- 같은 입력 5회 적재 후 row count 변화 없음 확인
- `metrics/run_results.jsonl`에 다음 항목 기록
  - `rows_inserted`
  - `rows_updated`
  - `row_count_after`
  - `idempotency_runs`
  - `duration_s`

포트폴리오 표현:

> "L0 raw layer에서 외부 API 응답을 JSONB로 원본 보존하고, PK 기반 upsert로 재실행 안전성을 검증했습니다."

AWS 대응 설명:

- 로컬: `raw.ig_posts`, Postgres JSONB, Airflow DAG, Python loader
- AWS: Amazon S3 + AWS Glue Data Catalog + Lake Formation, 또는 작은 규모에서는 Amazon RDS/Aurora PostgreSQL
- 차이: 로컬 Postgres는 단일 DB에서 빠르게 실험할 수 있고, AWS lake는 대용량 원본 보존·카탈로그·권한 분리에 적합하다.

### Phase 3: L1 분석용 DW와 dbt 메타데이터

해야 할 일:

- `stg_ig_posts`에서 타입 정규화, `likes_count = -1` 처리, 해시태그/멘션 추출
- `int_creator_daily_engagement` 같은 중간 모델 생성
- `mart_creator_performance`, `mart_hashtag_performance` 생성
- dbt schema YAML에 한국어 description과 tests 추가
- description coverage를 메트릭으로 기록

포트폴리오 표현:

> "raw API 응답을 분석가가 바로 쓸 수 있는 L1 DW 모델로 정제하고, dbt metadata를 통해 데이터 리터러시와 Agent 검색 정확도를 같이 개선했습니다."

AWS 대응 설명:

- 로컬: dbt-postgres, Postgres staging/intermediate/marts
- AWS: Amazon Redshift, Amazon Athena, AWS Glue
- 차이: 로컬 dbt는 모델링·테스트·문서화를 직접 보여주기 좋고, Redshift/Athena/Glue는 대규모 분산 처리와 managed 운영에 강하다.

### Phase 4: L2 AI-Native Mart와 메타데이터 카탈로그

해야 할 일:

- `ai_native.creator_campaign_context` 같은 LLM-facing OBT 생성
- 컬럼명을 Agent가 오해하지 않도록 denormalized + explicit naming 적용
- `schema.yml`에 `synonyms`, `example_questions`, `grain`, `business_definition` 추가
- dbt YAML 기반 schema index를 pgvector에 적재

포트폴리오 표현:

> "BI용 mart와 별도로 LLM이 이해하기 쉬운 AI-Native mart를 만들고, 비즈니스 메타데이터를 retrieval context로 연결했습니다."

AWS 대응 설명:

- 로컬: dbt `ai_native`, dbt YAML metadata, pgvector schema index
- AWS: SageMaker Unified Studio Catalog, AWS Glue Data Catalog, Amazon DataZone, Bedrock Knowledge Bases
- 차이: 로컬은 Agent가 실제로 어떤 metadata를 쓰는지 투명하게 구현할 수 있고, AWS는 조직 단위 카탈로그·권한·검색·KB 연동을 managed로 제공한다.

### Phase 5~6: Self-Service BI/AI

해야 할 일:

- Superset dashboard는 현업 self-service BI 역할로 배치
- Text2SQL Agent는 메타데이터 기반 self-service AI 역할로 배치
- 자연어 질문, 생성 SQL, 실행 결과, latency, cost를 eval 결과로 저장
- read-only validator, DDL/DML 차단, row limit 강제

포트폴리오 표현:

> "현업은 자연어로 질문하고, 분석가는 SQL과 dashboard로 검증하며, Agent는 허용된 read-only 범위 안에서만 실행되도록 설계했습니다."

AWS 대응 설명:

- 로컬: Superset, LangChain/LangGraph Text2SQL Agent, pgvector
- AWS: Amazon QuickSight, Amazon Bedrock Agent, Bedrock Knowledge Bases, Amazon OpenSearch Service
- 차이: 로컬은 Agent 설계와 실패 분석을 직접 보여주기 좋고, AWS는 모델·검색·BI·권한을 managed 서비스로 통합하기 쉽다.

### Phase 8: 운영 통제와 모니터링

해야 할 일:

- Airflow DAG 성공/실패, row count, duration을 `metrics/run_results.jsonl`에 일관되게 기록
- dbt test/freshness 결과를 포트폴리오 메트릭으로 정리
- Agent query별 token/cost/latency/refuse 여부 기록
- `metrics/portfolio_metrics.md`에 운영 지표 요약

포트폴리오 표현:

> "데이터 파이프라인과 AI 활용을 같은 운영 관측 체계로 묶어, 실패 감지와 비용 가시화를 프로젝트 단위로 구현했습니다."

AWS 대응 설명:

- 로컬: `metrics/run_results.jsonl`, Airflow logs, dbt test results, agent eval logs
- AWS: Amazon CloudWatch, CloudTrail, Cost Explorer, MWAA logs, Bedrock invocation logs
- 차이: 로컬은 포트폴리오 증거를 append-only 파일로 남기기 좋고, AWS는 운영 로그·감사·비용 분석을 중앙화할 수 있다.

## 6. 레포에 추가하면 좋은 산출물

우선순위 높은 문서:

1. `docs/architecture.md`
   - L0/L1/L2 + self-service + monitoring 구조를 한 장으로 설명
2. `docs/data_catalog_plan.md`
   - IT Meta, Biz Meta, Agent Meta 정의
3. `docs/adr/003-ai-native-layer.md`
   - BI mart와 AI-native mart를 분리하는 이유
4. `docs/request_flow.md`
   - 자연어 질문이 metadata retrieval, SQL generation, validation, execution으로 흐르는 과정
5. `metrics/query_optimization_log.md`
   - 운영 가시성과 쿼리 최적화 실험 기록

## 7. 지금 당장 Phase 2 Stage 1에 반영할 체크리스트

- [ ] `raw.ig_posts`를 L0 raw layer로 README 또는 architecture 문서에 명명
- [ ] `raw_payload JSONB` 원본 보존 원칙 유지
- [ ] upsert loader에서 inserted/updated/total을 메트릭으로 남김
- [ ] Airflow DAG에 collect task와 load task를 분리해 job 성공/실패를 관측 가능하게 만듦
- [ ] 멱등 5회 검증 결과를 `metrics/run_results.jsonl`과 `docs/portfolio_draft.md`에 기록
- [ ] Phase 3 진입 시 dbt YAML description coverage를 측정할 수 있게 설계
- [ ] 작업 설명에 로컬 구현, AWS 대응 서비스, 차이점, 면접용 한 문장을 함께 기록

## 8. 최종 포트폴리오 메시지

이 강의 내용을 반영하면 AdInsight Agent의 포트폴리오 메시지는 다음처럼 강화된다.

> "AdInsight Agent는 인플루언서 광고 데이터를 수집하는 ETL 프로젝트를 넘어, L0 원본 저장, L1 분석 모델, L2 AI-Native Mart, 메타데이터 카탈로그, self-service BI/AI, 운영 모니터링을 갖춘 현업형 데이터·AI 플랫폼입니다."
