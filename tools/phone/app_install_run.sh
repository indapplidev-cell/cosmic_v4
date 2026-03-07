#!/usr/bin/env bash
set -euo pipefail

require_var() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    read -r -p "$name: " value
  fi
  if [[ -z "$value" ]]; then
    echo "ERROR: $name is required" >&2
    exit 1
  fi
  export "$name=$value"
}

require_var "APK_PATH"
require_var "PACKAGE_NAME"

if [[ ! -f "$APK_PATH" ]]; then
  echo "ERROR: APK_PATH file not found: $APK_PATH" >&2
  exit 2
fi

adb install -r "$APK_PATH"
adb shell monkey -p "$PACKAGE_NAME" -c android.intent.category.LAUNCHER 1
