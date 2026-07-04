# AWS Infrastructure Skeleton

This directory documents the intended AWS deployment boundary for AdInsight.

Current status: **documentation skeleton only**. No Terraform/CDK resources are applied from this repo yet.

## Target Modules

```text
infra/aws/
├── README.md
├── network/          # VPC, subnets, security groups
├── data/             # RDS/Redshift, S3 raw/artifact buckets
├── orchestration/    # MWAA or scheduled ECS tasks
├── serving/          # ECR, ECS Fargate, ALB
├── observability/    # CloudWatch dashboards/alarms
└── bi/               # QuickSight dataset/dashboard notes
```

## Local-to-AWS Mapping

| Local | AWS target |
|---|---|
| `docker-compose.yml` API service | ECS Fargate service |
| `infra/api/Dockerfile` | ECR image source |
| `api/main.py` | FastAPI container entrypoint |
| `agent/model_artifacts/*.json` | S3 versioned model artifact |
| `agent/eval/text2sql_questions.yml` | S3 versioned Text2SQL registry artifact |
| Airflow DAGs in `dags/` | MWAA DAG bucket |
| Postgres schemas | RDS PostgreSQL first, Redshift optional |
| Superset dashboard | QuickSight dashboard |
| `metrics/run_results.jsonl` | CloudWatch logs/metrics and S3 audit log |

## Environment Contract

The API container should receive these values from Secrets Manager or task environment:

```text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
MODEL_ARTIFACT_PATH or MODEL_ARTIFACT_S3_URI
TEXT2SQL_REGISTRY_PATH or TEXT2SQL_REGISTRY_S3_URI
```

## First Deployable Slice

1. Build and push `infra/api/Dockerfile` to ECR.
2. Provision a small RDS PostgreSQL instance or restore a seeded snapshot.
3. Deploy FastAPI on ECS Fargate behind ALB.
4. Mount/read model and Text2SQL registry artifacts from S3.
5. Verify:
   - `GET /health`
   - `POST /predict/campaign-roas`
   - `POST /query`

## Non-Goals For Now

- No always-on Redshift until data volume/query load justifies it.
- No SageMaker endpoint for the current 25-row benchmark model.
- No Kinesis/MSK streaming for the first cloud slice.
- No production auth/multi-tenant isolation until the serving PoC is stable.
