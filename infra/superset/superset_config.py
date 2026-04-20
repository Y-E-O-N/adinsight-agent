# =============================================================================
# infra/superset/superset_config.py
# ----------------------------------------------------------------------------
# Superset 시작 시 /app/pythonpath/ 경로에서 자동 import 됨.
# 모든 시크릿은 환경변수로 주입 — 코드에 하드코딩 금지.
# =============================================================================
import os

# ---------------------------------------------------------------------------
# 메타데이터 DB — Superset 대시보드·차트·유저 정보 저장
# ---------------------------------------------------------------------------
_db_user = os.environ.get("POSTGRES_USER", "postgres")
_db_password = os.environ.get("POSTGRES_PASSWORD", "")
_db_host = os.environ.get("POSTGRES_HOST", "postgres")
_db_port = os.environ.get("POSTGRES_PORT", "5432")
_db_name = os.environ.get("SUPERSET_DB", "superset_meta")

SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://{_db_user}:{_db_password}"
    f"@{_db_host}:{_db_port}/{_db_name}"
)

# ---------------------------------------------------------------------------
# 세션 암호화 키 — 없으면 Superset 기동 거부. 운영에서는 반드시 강한 랜덤 값.
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me-in-production")

# ---------------------------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------------------------
ROW_LIMIT = 10000
SUPERSET_WEBSERVER_PORT = 8088
WTF_CSRF_ENABLED = True

# ---------------------------------------------------------------------------
# 기능 플래그 — Phase 5 대시보드 구축 시 추가 활성화 예정
# ---------------------------------------------------------------------------
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,   # 대시보드 네이티브 필터 UI
    "ALERT_REPORTS": False,             # 알림, 리포트 (phase 7에서 활성화)
}