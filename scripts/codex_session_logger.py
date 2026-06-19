#!/usr/bin/env python3
"""Mirror the active Codex JSONL session into logs/session_*.log.

Codex already writes structured JSONL under ~/.codex/sessions. This helper keeps
the project-local raw log current while a Codex session is running.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_CODEX_SESSIONS_DIR = Path.home() / ".codex" / "sessions"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Continuously mirror a Codex rollout JSONL into logs/session_*.log."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root used to match Codex session cwd. Defaults to the current directory.",
    )
    parser.add_argument(
        "--codex-sessions-dir",
        type=Path,
        default=DEFAULT_CODEX_SESSIONS_DIR,
        help="Codex session root. Defaults to ~/.codex/sessions.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Specific rollout-*.jsonl file to mirror. Defaults to latest session for this repo.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("logs"),
        help="Directory for session_*.log output. Defaults to ./logs.",
    )
    parser.add_argument(
        "--poll-seconds",
        type=float,
        default=0.5,
        help="Polling interval for new JSONL lines. Defaults to 0.5.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Convert current content once and exit instead of watching.",
    )
    parser.add_argument(
        "--since-epoch",
        type=float,
        default=None,
        help="Only auto-discover rollout files modified at or after this Unix epoch.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="Specific output log file. Defaults to output-dir/session_*.log.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Truncate the output log before writing.",
    )
    parser.add_argument(
        "--start-at-end",
        action="store_true",
        help="Start watching at the current end of the source file.",
    )
    return parser.parse_args()


def local_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def latest_rollout_for_repo(
    sessions_dir: Path, repo_root: Path, since_epoch: float | None = None
) -> Path | None:
    repo_root = repo_root.resolve()
    candidates = sorted(
        sessions_dir.glob("**/rollout-*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        if since_epoch is not None and path.stat().st_mtime < since_epoch:
            continue
        if rollout_cwd(path) == repo_root:
            return path
    return None


def rollout_cwd(path: Path) -> Path | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                event = json.loads(line)
                if event.get("type") != "session_meta":
                    continue
                cwd = event.get("payload", {}).get("cwd")
                return Path(cwd).resolve() if cwd else None
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return None


def format_event(event: dict[str, Any]) -> str | None:
    timestamp = event.get("timestamp", "")
    event_type = event.get("type")
    payload = event.get("payload", {})

    if event_type == "session_meta":
        return None

    if event_type == "event_msg":
        message_type = payload.get("type")
        if message_type == "user_message":
            return block(timestamp, "USER", payload.get("message", ""))
        if message_type == "agent_message":
            return block(timestamp, "ASSISTANT", payload.get("message", ""))
        return None
    return None


def block(timestamp: str, label: str, body: str) -> str:
    body = str(body).rstrip()
    if not body:
        body = "(empty)"
    return f"\n[{timestamp}] {label}\n{body}\n"


def mirror(
    source: Path, output: Path, *, poll_seconds: float, once: bool, start_at_end: bool
) -> None:
    offset = source.stat().st_size if start_at_end and source.exists() else 0

    with output.open("a", encoding="utf-8") as log_handle:
        while True:
            if source.exists():
                with source.open("r", encoding="utf-8") as source_handle:
                    source_handle.seek(offset)
                    while line := source_handle.readline():
                        offset = source_handle.tell()
                        if not line.strip():
                            continue
                        try:
                            event = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        formatted = format_event(event)
                        if formatted:
                            log_handle.write(formatted)
                            log_handle.flush()

            if once:
                return
            time.sleep(poll_seconds)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    if args.output_file is None:
        output_path = output_dir / f"session_{local_timestamp()}.log"
    else:
        output_path = args.output_file
        if not output_path.is_absolute():
            output_path = repo_root / output_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("", encoding="utf-8") if args.overwrite else output_path.touch()

    source = args.source
    if source is None:
        print("Waiting for Codex rollout JSONL for this repository...", file=sys.stderr)
        while source is None:
            source = latest_rollout_for_repo(
                args.codex_sessions_dir, repo_root, since_epoch=args.since_epoch
            )
            if source is None:
                time.sleep(args.poll_seconds)
    else:
        source = source.expanduser().resolve()

    print(f"Mirroring Codex session: {source}", file=sys.stderr)
    print(f"Project raw log: {output_path}", file=sys.stderr)
    try:
        mirror(
            source,
            output_path,
            poll_seconds=args.poll_seconds,
            once=args.once,
            start_at_end=args.start_at_end,
        )
    except KeyboardInterrupt:
        print("\nStopped Codex session logger.", file=sys.stderr)
    return os.EX_OK


if __name__ == "__main__":
    raise SystemExit(main())
