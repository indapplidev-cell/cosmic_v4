[app]

title = Cosmic
package.name = cosmic
package.domain = org.zenol
source.dir = .
source.include_exts = py,kv,json,md,png,jpg,jpeg,gif,atlas,ttf,otf,mp3,wav
version = 0.1.0

requirements = python3==3.11.9,hostpython3==3.11.9,android,kivy,kivy-garden,pyjnius==1.6.1,asyncgui==0.6.3,asynckivy==0.6.4,certifi==2026.1.4,charset-normalizer==3.4.4,docutils==0.22.4,filetype==1.2.0,idna==3.11,kivymd==2.0.1.dev0,materialshapes==0.3,materialyoucolor==3.0.1,packaging==26.0,pillow==12.1.0,Pygments==2.19.2,requests==2.32.5,setuptools==80.10.2,urllib3==2.6.3,wheel==0.46.3

orientation = landscape
fullscreen = 0

icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png

android.accept_sdk_license = True
android.permissions = INTERNET, ACCESS_NETWORK_STATE
android.archs = arm64-v8a, armeabi-v7a
android.minapi = 21
android.api = 34
android.debug_artifact = apk
android.release_artifact = apk

android.add_src = src/android
android.gradle_dependencies = com.google.android.gms:play-services-ads:23.0.0
android.enable_androidx = True
android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-3940256099942544~3347511713

p4a.commit = 957a3e5f8c270f7aa648ba185e5a68c1077a798d

[buildozer]
log_level = 2
warn_on_root = 1
