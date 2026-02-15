#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

"$ROOT_DIR/scripts/android/venv_buildozer.sh"

# shellcheck disable=SC1091
source "$ROOT_DIR/.venv_buildozer/bin/activate"

python "$ROOT_DIR/scripts/android/generate_assets.py"

cd "$ROOT_DIR"
buildozer -v android debug

LATEST_APK="$(ls -1t "$ROOT_DIR"/bin/*.apk 2>/dev/null | head -n 1 || true)"
if [ -z "$LATEST_APK" ]; then
  echo "No APK produced in $ROOT_DIR/bin" >&2
  exit 1
fi

# Verify that the filetype module is bundled in the Python payload.
TMP_PRIVATE=""
cleanup_tmp() {
  if [ -n "${TMP_PRIVATE:-}" ] && [ -f "$TMP_PRIVATE" ]; then
    rm -f "$TMP_PRIVATE"
  fi
}
trap cleanup_tmp EXIT

if unzip -l "$LATEST_APK" | grep -q "assets/private.mp3"; then
  TMP_PRIVATE="$(mktemp)"
  unzip -p "$LATEST_APK" assets/private.mp3 > "$TMP_PRIVATE"
  if ! unzip -l "$TMP_PRIVATE" | grep -E -q '(^|/)filetype(/|\\.|__init__)'; then
    echo "APK validation failed: python module 'filetype' was not found in assets/private.mp3." >&2
    exit 1
  fi
elif ! unzip -l "$LATEST_APK" | grep -E -q '(^|/)filetype(/|\\.|__init__)'; then
  echo "APK validation failed: python module 'filetype' was not found in APK contents." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/artifacts/apk"
cp "$LATEST_APK" "$ROOT_DIR/artifacts/apk/Cosmic-debug.apk"

echo "artifacts/apk/Cosmic-debug.apk"
