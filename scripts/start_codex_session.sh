#!/usr/bin/env bash
set -euo pipefail

script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
session_root="$PWD"
started_at="$(date +%s)"
codex_bin="${CODEX_BIN:-/opt/homebrew/bin/codex}"

if [[ ! -x "$codex_bin" ]]; then
  codex_bin="$(command -v codex)"
fi

python3 "$script_root/scripts/codex_session_logger.py" \
  --repo-root "$session_root" \
  --output-dir "$session_root/logs" \
  --since-epoch "$started_at" &
logger_pid="$!"

cleanup() {
  if kill -0 "$logger_pid" >/dev/null 2>&1; then
    kill "$logger_pid" >/dev/null 2>&1 || true
    wait "$logger_pid" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT INT TERM

"$codex_bin" "$@"
