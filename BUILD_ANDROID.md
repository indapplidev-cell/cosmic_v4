# Android Build

## Canonical GitHub flow
1. EN: Use GitHub Actions workflow `.github/workflows/android.yml` as the canonical Android build entrypoint.
   RU: Использовать GitHub Actions workflow `.github/workflows/android.yml` как каноническую точку входа для Android-сборки.
2. EN: Run the workflow on the target branch with `gh workflow run android.yml --ref <branch>`.
   RU: Запускать workflow на нужной ветке командой `gh workflow run android.yml --ref <branch>`.
3. EN: Wait for job `build-android-debug` to finish and use its uploaded artifact `android-debug-apk`.
   RU: Дождаться завершения job `build-android-debug` и использовать его артефакт `android-debug-apk`.

## Known-good baseline
- EN: Verified successful GitHub build: workflow `android.yml`, run `23210899949`, branch `rename-cosmic-to-escape2mars`, commit `679de1f9f2fd6a68dc6463b1c4f65a5173e54809`, date `2026-03-17`.
- RU: Подтверждённая успешная GitHub-сборка: workflow `android.yml`, run `23210899949`, ветка `rename-cosmic-to-escape2mars`, коммит `679de1f9f2fd6a68dc6463b1c4f65a5173e54809`, дата `2026-03-17`.
- EN: Do not use `.github/workflows/android-debug.yml` as the reference build path; in its current state it points to missing helper scripts and fails before APK build.
- RU: Не использовать `.github/workflows/android-debug.yml` как эталонный путь сборки; в текущем состоянии он ссылается на отсутствующие helper-скрипты и падает до сборки APK.

## Build inputs that worked
- EN: Repository-root `buildozer.spec` is the build spec used by `android.yml`.
- RU: Для `android.yml` используется корневой `buildozer.spec`.
- EN: The working Android requirements line is `python3==3.11.9,hostpython3==3.11.9,android,kivy,kivy-garden,...,kivymd==2.0.1.dev0,...`.
- RU: Рабочая строка Android requirements: `python3==3.11.9,hostpython3==3.11.9,android,kivy,kivy-garden,...,kivymd==2.0.1.dev0,...`.
- EN: `p4a.commit` is pinned to `957a3e5f8c270f7aa648ba185e5a68c1077a798d`.
- RU: `p4a.commit` зафиксирован на `957a3e5f8c270f7aa648ba185e5a68c1077a798d`.

## Practical note
- EN: If a future Android build is needed, start from `android.yml` first and treat this file as the reference snapshot of the last successful GitHub build.
- RU: Если понадобится следующая Android-сборка, сначала использовать `android.yml` и считать этот файл опорным снимком последней успешной GitHub-сборки.
