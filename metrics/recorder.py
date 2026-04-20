"""Append-only 메트릭 기록기. 모든 Phase가 측정값을 한 줄씩 누적한다.

사용 예:
    from metrics.recorder import log
    log("p2", "generate_synthetic", rows=20_000_000, size_mb=1450, duration_s=1180, seed=42)

블루프린트 섹션 7 참고.
"""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
from typing import Any

_LOG_PATH = pathlib.Path(__file__).resolve().parent / "run_results.jsonl"


def log(phase: str, step: str, **kv: Any) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "phase": phase,
        "step": step,
        "ts": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        **kv,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


if __name__ == "__main__":
    import sys

    log("p0", "recorder_smoke_test", note="recorder.py invoked directly", argv=sys.argv[1:])
    print(f"smoke test appended → {_LOG_PATH}")
