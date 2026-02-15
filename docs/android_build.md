# Android Debug APK (WSL2/Ubuntu)

## A) Сборка в WSL2 Ubuntu 24.04
1. `chmod +x scripts/android/*.sh`
2. `./scripts/android/bootstrap_ubuntu.sh`
3. `./scripts/android/build_debug.sh`

Результат: `artifacts/apk/Cosmic-debug.apk`

## B) Как забрать APK из WSL в Windows
- Файл в WSL: `~/PROJECT/artifacts/apk/Cosmic-debug.apk`
- В проводнике Windows: `\\wsl$\Ubuntu-24.04\home\<linux_user>\...\artifacts\apk\Cosmic-debug.apk`
- Скопируй файл в любую папку Windows (например, `Downloads`).

## C) Как установить на телефон вручную (без ADB)
- Скопируй `Cosmic-debug.apk` на телефон (например, в `Download`) через MTP/кабель.
- На телефоне: файловый менеджер -> `Downloads` -> `Cosmic-debug.apk` -> `Install`.
- При необходимости разрешить установку из неизвестных источников.