# NeoTube Downloader Android Standalone

This APK is a Neo Apps standalone Android build. It embeds the Python backend
with Chaquopy, starts the local server inside the app, and opens the built
NeoTube UI in a native WebView.

Downloads are stored in the app-specific Android downloads directory returned
by `getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)`.

## Build

```powershell
gradle -p android assembleDebug
```

The APK is written to:

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

## Notes

The Android build uses an in-process download worker because Android's embedded
Python runtime does not support the desktop app's multiprocessing worker model.
No separate desktop server is required.

The APK includes the MobileFFmpeg AAR used by the Android backend for conversion
support. Keep `android/app/libs/mobile-ffmpeg-full-gpl-4.4.LTS.aar` in place
before building.
