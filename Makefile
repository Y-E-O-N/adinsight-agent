.PHONY: help up down logs ps psql airflow-cli superset-init dbt-run dbt-test dbt-docs test fmt lint sync clean

# 기본 타깃: help
help:
	@echo "AdInsight Agent — Make targets"
	@echo ""
	@echo "  make sync          # uv 가상환경 생성 + 의존성 설치"
	@echo "  make up            # docker compose up -d (Phase 1 이후 활성화)"
	@echo "  make down          # docker compose down"
	@echo "  make logs          # 실시간 로그"
	@echo "  make ps            # 컨테이너 상태"
	@echo "  make psql          # Postgres psql 접속"
	@echo "  make airflow-cli cmd='dags list'"
	@echo "  make superset-init # Superset 초기 admin / DB 마이그레이션"
	@echo "  make dbt-run       # dbt run (전체 모델)"
	@echo "  make dbt-test      # dbt test"
	@echo "  make dbt-docs      # dbt docs generate"
	@echo "  make test          # pytest"
	@echo "  make fmt           # ruff format + sqlfluff fix"
	@echo "  make lint          # ruff check + sqlfluff lint"

sync:
	uv sync

up:
	docker compose up -d
	@echo "Airflow:  http://localhost:8080"
	@echo "Superset: http://localhost:8088"

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker compose logs -f --tail=100

psql:
	docker compose exec postgres psql -U postgres -d adinsight

airflow-cli:
	docker compose exec airflow-webserver airflow $(cmd)

superset-init:
	docker compose exec superset superset fab create-admin \
		--username admin --password admin \
		--firstname Admin --lastname User --email admin@example.com
	docker compose exec superset superset db upgrade
	docker compose exec superset superset init

dbt-run:
	docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt run"

dbt-test:
	docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt test"

dbt-docs:
	docker compose exec airflow-worker bash -c "cd /opt/dbt && dbt docs generate"

test:
	uv run pytest -q

fmt:
	uv run ruff format .
	uv run sqlfluff fix dbt/models || true

lint:
	uv run ruff check .
	uv run sqlfluff lint dbt/models || true

clean:
	@echo "이 타깃은 컨테이너·볼륨을 삭제합니다. 정말 실행하려면 'make clean-confirm' 사용"

clean-confirm:
	docker compose down -v
	rm -rf .venv .ruff_cache .pytest_cache dbt/target
