from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_AUDIT_LOG_PATH = Path("logs/text2sql_audit.jsonl")


def write_text2sql_audit(
    record: dict[str, Any],
    path: Path = DEFAULT_AUDIT_LOG_PATH,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    audit_record = {
        "ts": datetime.now(UTC).isoformat(),
        **record,
    }

    with path.open("a", encoding="utf-8") as audit_file:
        audit_file.write(json.dumps(audit_record, ensure_ascii=False) + "\n")
