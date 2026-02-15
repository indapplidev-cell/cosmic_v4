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

# Verify that the filetype module is actually bundled in the APK.
if ! unzip -l "$LATEST_APK" | grep -E -q 'filetype(/|\\.|__init__)'; then
  echo "APK validation failed: python module 'filetype' was not found in APK contents." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/artifacts/apk"
cp "$LATEST_APK" "$ROOT_DIR/artifacts/apk/Cosmic-debug.apk"

echo "artifacts/apk/Cosmic-debug.apk"
