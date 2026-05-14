# NeoTube Downloader

NeoTube Downloader is a Neo Apps media downloader built on `yt-dlp`.
It provides a web UI plus Windows desktop, Android, and iOS app shells for saving videos, audio, captions, and thumbnails.

## Apps

- **Windows desktop:** packaged as a standalone EXE with Python, FFmpeg, and required runtime DLLs bundled.
- **Android:** standalone APK with bundled Python backend, WebView UI, selectable download folder, and MobileFFmpeg conversion support.
- **iOS:** SwiftUI/WKWebView app project for connecting to a reachable NeoTube server.
- **Web/server:** Python `aiohttp` backend with Angular frontend.

## Key Features

- Download videos, audio, captions, and thumbnails.
- Choose codecs and formats including H.264, H.265, AV1, MP4, VP9, M4A, MP3, Opus, WAV, and FLAC where the platform build supports them.
- Queue downloads, retry failures, and manage completed items.
- Select custom download folders.
- Use advanced `yt-dlp` options and presets.
- Upload cookies for authenticated downloads.
- Brand footer as `NEO Apps : Desktop`, `NEO Apps : Android`, or `NEO Apps : iOS`.

## Windows Build

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\desktop\build_windows.ps1
```

Output:

```text
dist\NeoTube Downloader Standalone\NeoTube Downloader.exe
```

## Android Build

```powershell
& '<path-to-gradle>\gradle.bat' -p android assembleDebug
```

Output:

```text
android\app\build\outputs\apk\debug\app-debug.apk
```

`android\local.properties` is intentionally ignored because it contains the local Android SDK path.

## iOS Build

Open the Xcode project on macOS:

```bash
open ios/NeoTubeDownloader.xcodeproj
```

Set your Apple signing team, then build and run from Xcode.

## Web Development

Frontend:

```bash
cd ui
pnpm install --frozen-lockfile
pnpm run build
```

Backend:

```bash
uv sync --frozen --group dev
uv run pytest app/tests/
```

## Common Environment Variables

- `DOWNLOAD_DIR`: primary download folder.
- `AUDIO_DOWNLOAD_DIR`: audio-only download folder.
- `STATE_DIR`: persistent queue/history/subscription storage.
- `TEMP_DIR`: temporary download folder.
- `MAX_CONCURRENT_DOWNLOADS`: number of parallel downloads.
- `YTDL_OPTIONS`: JSON object of global `yt-dlp` options.
- `YTDL_OPTIONS_FILE`: JSON file containing global `yt-dlp` options.
- `YTDL_OPTIONS_PRESETS`: JSON object of named option presets.
- `ALLOW_YTDL_OPTIONS_OVERRIDES`: show per-download custom options in the UI.
- `HOST`, `PORT`, `URL_PREFIX`: web server binding and base path.
- `PUBLIC_HOST_URL`, `PUBLIC_HOST_AUDIO_URL`: completed-file link bases.
- `HTTPS`, `CERTFILE`, `KEYFILE`: HTTPS configuration.
- `DEFAULT_THEME`: `light`, `dark`, or `auto`.
- `LOGLEVEL`: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`, or `NONE`.

## Notes

NeoTube Downloader depends on `yt-dlp`, so keeping the Python dependencies current is important when video sites change.

Contributor: diazneoones82
