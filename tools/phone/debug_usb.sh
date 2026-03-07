#!/usr/bin/env bash
set -euo pipefail

USE_SCRCPY=0
if [[ "${1:-}" == "--scrcpy" ]]; then
  USE_SCRCPY=1
fi

PACKAGE_NAME="${PACKAGE_NAME:-}"
APK_PATH="${APK_PATH:-}"

if [[ -z "$PACKAGE_NAME" ]]; then
  echo "ERROR: PACKAGE_NAME is required (export PACKAGE_NAME=...)" >&2
  exit 1
fi

adb kill-server || true
adb start-server

SERIAL="$(adb devices | awk 'NR>1 && $2=="device"{print $1; exit}')"
if [[ -z "$SERIAL" ]]; then
  echo "ERROR: no authorized adb device found (USB). Check cable and RSA prompt." >&2
  adb devices -l || true
  exit 2
fi

echo "Using device: $SERIAL"

if [[ -n "$APK_PATH" ]]; then
  if [[ ! -f "$APK_PATH" ]]; then
    echo "ERROR: APK_PATH file not found: $APK_PATH" >&2
    exit 3
  fi
  adb -s "$SERIAL" install -r "$APK_PATH"
fi

adb -s "$SERIAL" shell monkey -p "$PACKAGE_NAME" -c android.intent.category.LAUNCHER 1

mkdir -p logs/phone
adb -s "$SERIAL" logcat -c

if [[ "$USE_SCRCPY" -eq 1 ]]; then
  scrcpy --serial "$SERIAL" --stay-awake --turn-screen-off --window-title "Phone USB Debug" &
fi

adb -s "$SERIAL" logcat -v time | tee "logs/phone/logcat_$(date +%Y%m%d_%H%M%S).txt"
