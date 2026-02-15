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
has_filetype_in_zip() {
  local zip_path="$1"
  unzip -Z1 "$zip_path" 2>/dev/null | grep -Eiq '(^|/)(filetype/|filetype\.py$|filetype-[^/]+\.dist-info/)'
}

FILETYPE_FOUND=0

if has_filetype_in_zip "$LATEST_APK"; then
  FILETYPE_FOUND=1
elif unzip -Z1 "$LATEST_APK" | grep -q '^assets/private.mp3$'; then
  TMP_PRIVATE="$(mktemp)"
  unzip -p "$LATEST_APK" assets/private.mp3 > "$TMP_PRIVATE"
  if has_filetype_in_zip "$TMP_PRIVATE"; then
    FILETYPE_FOUND=1
  fi
  rm -f "$TMP_PRIVATE"
fi

if [ "$FILETYPE_FOUND" -eq 0 ]; then
  if find "$ROOT_DIR/.buildozer" -type f \( -name "filetype.py" -o -path "*/filetype/__init__.py" -o -path "*/filetype-*.dist-info/*" \) | grep -q .; then
    FILETYPE_FOUND=1
  fi
fi

if [ "$FILETYPE_FOUND" -eq 0 ]; then
  echo "APK validation failed: python module 'filetype' was not found in APK or build payload." >&2
  exit 1
fi

mkdir -p "$ROOT_DIR/artifacts/apk"
cp "$LATEST_APK" "$ROOT_DIR/artifacts/apk/Cosmic-debug.apk"

echo "artifacts/apk/Cosmic-debug.apk"
