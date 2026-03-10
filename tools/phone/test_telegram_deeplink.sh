#!/usr/bin/env bash
set -euo pipefail

# EN: Validate Telegram deep-link opening on Android device via adb shell am start.
# RU: Проверить открытие Telegram deep-link на Android через adb shell am start.
#
# EN usage:
#   bash tools/phone/test_telegram_deeplink.sh pswprotect_bot AbCdEf0123Token
# RU использование:
#   bash tools/phone/test_telegram_deeplink.sh pswprotect_bot AbCdEf0123Token

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <bot_username> <start_token>" >&2
  exit 2
fi

BOT_USERNAME="$1"
START_TOKEN="$2"
TG_URL="tg://resolve?domain=${BOT_USERNAME}&start=${START_TOKEN}"
WEB_URL="https://t.me/${BOT_USERNAME}?start=${START_TOKEN}"

mkdir -p logs/phone
OUT="logs/phone/telegram_deeplink_test.txt"
: > "$OUT"

{
  echo "=== telegram deeplink test ==="
  echo "time_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "tg_url=${TG_URL}"
  echo "web_url=${WEB_URL}"
  echo
  echo "--- adb devices ---"
  adb devices -l
  echo
  echo "--- am start tg:// ---"
  set +e
  adb shell am start -W -a android.intent.action.VIEW -d "${TG_URL}"
  TG_EXIT=$?
  set -e
  echo "tg_exit=${TG_EXIT}"
  echo
  if [[ ${TG_EXIT} -ne 0 ]]; then
    echo "--- am start https:// fallback ---"
    set +e
    adb shell am start -W -a android.intent.action.VIEW -d "${WEB_URL}"
    WEB_EXIT=$?
    set -e
    echo "web_exit=${WEB_EXIT}"
  else
    echo "web_exit=skipped"
  fi
} | tee -a "$OUT"

echo "Saved report: $OUT"
