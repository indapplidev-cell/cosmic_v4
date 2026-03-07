#!/usr/bin/env bash
set -euo pipefail

require_var() {
  local name="$1"
  local hidden="${2:-0}"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    if [[ "$hidden" == "1" ]]; then
      read -r -s -p "$name: " value
      echo
    else
      read -r -p "$name: " value
    fi
  fi
  if [[ -z "$value" ]]; then
    echo "ERROR: $name is required" >&2
    exit 1
  fi
  export "$name=$value"
}

require_var "PHONE_IP"
require_var "PAIR_PORT"
require_var "PAIR_CODE" "1"
require_var "ADB_PORT"

adb kill-server
adb start-server

printf "%s\n" "$PAIR_CODE" | adb pair "${PHONE_IP}:${PAIR_PORT}"
adb connect "${PHONE_IP}:${ADB_PORT}"
adb devices -l

if ! adb devices | awk -v serial="${PHONE_IP}:${ADB_PORT}" '$1==serial && $2=="device"{ok=1} END{exit !ok}'; then
  echo "ERROR: device ${PHONE_IP}:${ADB_PORT} is not in 'device' state" >&2
  exit 2
fi

echo "Connected: ${PHONE_IP}:${ADB_PORT}"
