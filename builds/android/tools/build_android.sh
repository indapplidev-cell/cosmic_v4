#!/usr/bin/env bash
set -euo pipefail

mkdir -p builds/android/logs
LOG_FILE="builds/android/logs/build_android.log"

TARGET="${1:-}"
MODE="${2:-}"

if [[ "${TARGET}" != "android" || "${MODE}" != "debug" ]]; then
  echo "Usage: bash builds/android/tools/build_android.sh android debug" >&2
  exit 2
fi

if [[ ! -f "buildozer.spec" ]]; then
  echo "ERROR: buildozer.spec not found in repository root." >&2
  exit 1
fi

# Keep APP_* values deterministic if workflow exported them.
export APP_ANDROID_API="${APP_ANDROID_API:-${ANDROID_API:-}}"
export APP_ANDROID_NDK="${APP_ANDROID_NDK:-${ANDROID_NDK:-}}"
export APP_ANDROID_BUILD_TOOLS_VERSION="${APP_ANDROID_BUILD_TOOLS_VERSION:-${ANDROID_BUILD_TOOLS:-}}"

set +e
buildozer -v "${TARGET}" "${MODE}" 2>&1 | tee "${LOG_FILE}"
BUILD_EXIT=${PIPESTATUS[0]}
set -e

if [[ ${BUILD_EXIT} -ne 0 ]]; then
  echo "Build failed. See log: ${LOG_FILE}" >&2
  exit "${BUILD_EXIT}"
fi

APK_PATH="$(find . -type f \( -name '*debug*.apk' -o -name '*.apk' \) | grep -E '/(bin|outputs/apk)/' | head -n 1 || true)"
if [[ -n "${APK_PATH}" ]]; then
  echo "APK found at: ${APK_PATH}"
else
  echo "APK not found after successful build command."
fi
