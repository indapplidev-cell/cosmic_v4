# Android Build

## Canonical flow
1. EN: Fill/update the local wheelhouse: `../builds/android/tools/sync_wheelhouse.sh`
   RU: Наполнить/обновить локальный wheelhouse: `../builds/android/tools/sync_wheelhouse.sh`
2. EN: Bootstrap the WSL builder venv only from the wheelhouse: `../builds/android/tools/bootstrap_builder_venv.sh`
   RU: Поднять WSL builder venv только из wheelhouse: `../builds/android/tools/bootstrap_builder_venv.sh`
3. EN: Run readiness checks: `../builds/android/tools/doctor_android.sh`
   RU: Запустить проверку готовности: `../builds/android/tools/doctor_android.sh`
4. EN: Start the offline build: `../builds/android/tools/build_android.sh`
   RU: Запустить офлайн-сборку: `../builds/android/tools/build_android.sh`

## Source of truth
- EN: Toolchain pins live in `builds/android/ANDROID_TOOLCHAIN.lock`.
- RU: Зафиксированные версии toolchain лежат в `builds/android/ANDROID_TOOLCHAIN.lock`.
- EN: Pure-Python Android wheels live in `builds/android/wheelhouse` and are hashed in `builds/android/wheelhouse/WHEELHOUSE.lock`.
- RU: Pure-Python Android wheels лежат в `builds/android/wheelhouse`, а их хэши фиксируются в `builds/android/wheelhouse/WHEELHOUSE.lock`.
- EN: KivyMD 2.x is delivered only as `builds/android/wheelhouse/kivymd-2.0.1.dev0-py3-none-any.whl`.
- RU: KivyMD 2.x доставляется только как `builds/android/wheelhouse/kivymd-2.0.1.dev0-py3-none-any.whl`.
