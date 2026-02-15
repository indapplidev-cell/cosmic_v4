#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

"$ROOT_DIR/scripts/android/venv_buildozer.sh"

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv_buildozer/bin/activate"

cd "$ROOT_DIR"

if command -v adb >/dev/null 2>&1; then
  ADB_BIN="$(command -v adb)"
else
  ADB_BIN="$ROOT_DIR/.buildozer/android/platform/android-sdk/platform-tools/adb"
fi

if [ ! -x "$ADB_BIN" ]; then
  echo "adb not found. Install with: sudo apt-get install -y adb" >&2
  exit 1
fi

"$ADB_BIN" devices
buildozer -v android debug deploy run

# EN: Stream logs for 60s and stop automatically.
# RU: Показывает лог 60 секунд и завершает автоматически.
if command -v timeout >/dev/null 2>&1; then
  timeout 60s "$ADB_BIN" logcat | grep -i -E "python|kivy|cosmic" || true
else
  buildozer android logcat
fi