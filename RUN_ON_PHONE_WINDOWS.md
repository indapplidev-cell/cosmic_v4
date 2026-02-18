# Run On Phone (Windows + ADB Wi-Fi)

```powershell
adb pair 192.168.1.50:37261
adb connect 192.168.1.50:5555
adb devices
```

```powershell
adb install -r "D:\disk_E\course_py\game\game_galaxy_code_python\android_build_env\output\Cosmic-debug.apk"
```

```powershell
adb shell monkey -p org.zenol.cosmic.cosmic -c android.intent.category.LAUNCHER 1
```

```powershell
adb logcat -c
adb shell am force-stop org.zenol.cosmic.cosmic
adb shell monkey -p org.zenol.cosmic.cosmic -c android.intent.category.LAUNCHER 1
adb logcat -d -v time > D:\disk_E\course_py\game\game_galaxy_code_python\android_build_env\logs\logcat.txt
```
