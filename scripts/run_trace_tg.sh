#!/usr/bin/env bash
# EN: Run one desktop trace session, collect local and VPS logs, and package artifacts.
# RU: Запустить одну desktop trace-сессию, собрать локальные и VPS-логи и упаковать артефакты.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY_BIN=""
if [ -x "$ROOT_DIR/.venv/Scripts/python.exe" ]; then
  PY_BIN="$ROOT_DIR/.venv/Scripts/python.exe"
elif command -v python3 >/dev/null 2>&1; then
  PY_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PY_BIN="python"
elif command -v py.exe >/dev/null 2>&1; then
  PY_BIN="py.exe -3.11"
else
  echo "[TRACE] ERROR: python interpreter not found"
  exit 1
fi

PY_HELPER="$PY_BIN"
if command -v python3 >/dev/null 2>&1; then
  PY_HELPER="python3"
elif command -v python >/dev/null 2>&1; then
  PY_HELPER="python"
fi

STAMP="$(date +%Y%m%d_%H%M%S)"
TRACE_DIR="${TRACE_DIR:-$ROOT_DIR/logs/trace/$STAMP}"
mkdir -p "$TRACE_DIR"

export TRACE_ENABLE=1
export TRACE_DIR

APP_TRACE_DIR="$TRACE_DIR"
if [[ "$PY_BIN" == *".exe"* ]] && command -v cygpath >/dev/null 2>&1; then
  APP_TRACE_DIR="$(cygpath -w "$TRACE_DIR")"
fi

APP_STDOUT="$TRACE_DIR/app_stdout.log"
APP_STDERR="$TRACE_DIR/app_stderr.log"

RUN_SECS="${1:-${RUN_SECS:-180}}"

echo "[TRACE] TRACE_DIR=$TRACE_DIR"
echo "[TRACE] RUN_SECS=$RUN_SECS"

if command -v timeout >/dev/null 2>&1; then
  # shellcheck disable=SC2086
  TRACE_ENABLE=1 TRACE_DIR="$APP_TRACE_DIR" timeout "${RUN_SECS}s" $PY_BIN main.py >"$APP_STDOUT" 2>"$APP_STDERR" || true
else
  # shellcheck disable=SC2086
  TRACE_ENABLE=1 TRACE_DIR="$APP_TRACE_DIR" $PY_BIN main.py >"$APP_STDOUT" 2>"$APP_STDERR" || true
fi

# EN: If app process did not produce trace files, generate minimal trace artifact.
# RU: Если процесс приложения не создал trace-файлы, сгенерировать минимальный trace-артефакт.
if [ ! -f "$TRACE_DIR/client_trace.jsonl" ]; then
  # shellcheck disable=SC2086
  TRACE_ENABLE=1 TRACE_DIR="$TRACE_DIR" $PY_HELPER - <<'PY'
from manager.trace import TraceManager
t = TraceManager.instance()
t.log("SESSION", "TRACE.FALLBACK_GENERATED", lvl="WARN", reason="client_trace_missing_after_run")
PY
fi

# EN: Optional VPS log collection for api+bot using project helper.
# RU: Опциональный сбор VPS-логов для api+bot через проектный helper.
if [ -x "$ROOT_DIR/tools/vps.sh" ]; then
  bash "$ROOT_DIR/tools/vps.sh" cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env logs --since 10m api bot" >/dev/null 2>&1 || true
  LATEST_VPS_DIR="$(ls -1dt "$ROOT_DIR"/logs/vps/* 2>/dev/null | head -n1 || true)"
  if [ -n "${LATEST_VPS_DIR:-}" ] && [ -f "$LATEST_VPS_DIR/cmd.out.txt" ]; then
    cp "$LATEST_VPS_DIR/cmd.out.txt" "$TRACE_DIR/vps_api_bot.log" || true
  fi

  bash "$ROOT_DIR/tools/vps.sh" cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env logs --tail 500 api" >/dev/null 2>&1 || true
  LATEST_VPS_DIR="$(ls -1dt "$ROOT_DIR"/logs/vps/* 2>/dev/null | head -n1 || true)"
  if [ -n "${LATEST_VPS_DIR:-}" ] && [ -f "$LATEST_VPS_DIR/cmd.out.txt" ]; then
    cp "$LATEST_VPS_DIR/cmd.out.txt" "$TRACE_DIR/vps_api.log" || true
  fi

  bash "$ROOT_DIR/tools/vps.sh" cmd "cd /opt/cosmic_api && sudo docker compose -f server/infra/docker-compose.yml --env-file server/.env logs --tail 500 bot" >/dev/null 2>&1 || true
  LATEST_VPS_DIR="$(ls -1dt "$ROOT_DIR"/logs/vps/* 2>/dev/null | head -n1 || true)"
  if [ -n "${LATEST_VPS_DIR:-}" ] && [ -f "$LATEST_VPS_DIR/cmd.out.txt" ]; then
    cp "$LATEST_VPS_DIR/cmd.out.txt" "$TRACE_DIR/vps_bot.log" || true
  fi
fi

# EN: Build timeline markdown from client trace JSONL when available.
# RU: Построить timeline markdown из client trace JSONL при наличии файла.
# shellcheck disable=SC2086
$PY_HELPER - "$TRACE_DIR" <<'PY'
from __future__ import annotations
import json
from pathlib import Path
import sys

trace_dir = Path(sys.argv[1])
src = trace_dir / "client_trace.jsonl"
dst = trace_dir / "timeline.md"
if not src.exists():
    raise SystemExit(0)
rows = []
for line in src.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    try:
        obj = json.loads(line)
    except Exception:
        continue
    rows.append(obj)
out = ["# Trace Timeline", "", "| seq | ts | cat | name | data |", "|---:|---|---|---|---|"]
for item in rows:
    seq = item.get("seq", "")
    ts = str(item.get("ts", "")).replace("|", "\\|")
    cat = str(item.get("cat", "")).replace("|", "\\|")
    name = str(item.get("name", "")).replace("|", "\\|")
    data = str(item.get("data", "")).replace("|", "\\|")
    out.append(f"| {seq} | {ts} | {cat} | {name} | {data} |")
dst.write_text("\n".join(out) + "\n", encoding="utf-8")
PY

# EN: Package all trace artifacts to a single zip.
# RU: Упаковать все trace-артефакты в один zip.
# shellcheck disable=SC2086
$PY_HELPER - "$TRACE_DIR" <<'PY'
from __future__ import annotations
from pathlib import Path
import zipfile
import sys

trace_dir = Path(sys.argv[1])
bundle = trace_dir / "trace_bundle.zip"
with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in sorted(trace_dir.rglob("*")):
        if path.is_file() and path.name != bundle.name:
            zf.write(path, arcname=path.relative_to(trace_dir))
print(bundle)
PY

echo "[TRACE] DONE: $TRACE_DIR/trace_bundle.zip"
