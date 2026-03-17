#!/usr/bin/env bash
set -euo pipefail

cd /mnt/d/disk_E/course_py/game/game_galaxy_code_python/cosmic_v4

if [ ! -d .venv_buildozer_local ]; then
  python3 -m venv .venv_buildozer_local
fi

source .venv_buildozer_local/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install buildozer cython==0.29.36

export BUILDOZER_HOME="$PWD/_buildozer_home"
# EN: Let pip (including p4a internal pip calls) see locally built wheels first.
# RU: Даём pip (включая внутренние вызовы p4a) видеть локальные wheel-файлы в первую очередь.
export PIP_FIND_LINKS="$PWD/android_build_env/wheels"
# EN: Prefer the Android toolchain and mask the host `link` binary that breaks
# FreeType/libtool configure checks during clean GitHub-backed builds.
# RU: Отдаём приоритет Android toolchain и маскируем host-бинарник `link`,
# который ломает проверки FreeType/libtool при чистой GitHub-сборке.
export PATH="$PWD/build-tools/linux-shims:$PATH"

python scripts/run_buildozer_with_spec.py -v android debug

mkdir -p artifacts
APK_PATH="$(ls -1t _buildozer_cfg/bin/*.apk | head -n 1)"
cp "$APK_PATH" artifacts/Cosmic-debug.apk
sha256sum artifacts/Cosmic-debug.apk > artifacts/Cosmic-debug.apk.sha256
echo "APK_READY:$APK_PATH"
