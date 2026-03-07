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

require_var "PHONE_IP"
require_var "ADB_PORT"

adb disconnect "${PHONE_IP}:${ADB_PORT}" || true
adb kill-server || true

echo "Disconnected: ${PHONE_IP}:${ADB_PORT}"
