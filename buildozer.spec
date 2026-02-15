[app]

title = Cosmic
package.name = cosmic
package.domain = org.zenol.cosmic
source.dir = .
source.include_exts = py,kv,json,txt,md,ttf,otf,png,jpg,jpeg,gif
source.exclude_patterns = **/__pycache__/**,**/*.pyc,**/*.pyo,.git/**,.vscode/**,docs/**,scripts/**,*.zip,.venv/**,.venv_buildozer/**,.buildozer/**,bin/**,artifacts/**
version = 0.1.0

requirements = python3,kivy==2.3.1,https://github.com/kivymd/KivyMD/archive/d668d8b2b3d9eb54517892f613ffe34d9914517a.zip,pillow

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

android.accept_sdk_license = True
android.permissions = INTERNET
android.archs = arm64-v8a, armeabi-v7a
android.minapi = 21
android.api = 34
android.ndk = 25b
android.release_artifact = apk

p4a.branch = master

[buildozer]
log_level = 2
warn_on_root = 1