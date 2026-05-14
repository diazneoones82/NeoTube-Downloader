# NeoTube Downloader for Windows

NeoTube Downloader is a Neo Apps Windows desktop downloader with a native
WebView window. The existing environment variables and yt-dlp options still
work.

## Build

```powershell
.\desktop\build_windows.ps1
```

The output is written to:

```text
dist\NeoTube Downloader Standalone\NeoTube Downloader.exe
```

## Configuration

At startup the EXE reads `.env` from the same directory as the EXE. Real process
environment variables take precedence over values in `.env`.

The desktop app shows a startup folder selector before the downloader starts.
The chosen folder becomes `DOWNLOAD_DIR`. If you check "Remember this folder",
the desktop app stores that choice in
`%USERPROFILE%\Neo Apps\NeoTube Downloader\.neotube\desktop-settings.json`.
By default the desktop app also puts temporary files under the selected download
folder (`.neotube-temp`) to avoid Windows cross-drive progress issues.

All downloader environment variables are supported, including:

- `MAX_CONCURRENT_DOWNLOADS`
- `DELETE_FILE_ON_TRASHCAN`
- `DEFAULT_OPTION_PLAYLIST_ITEM_LIMIT`
- `SUBSCRIPTION_DEFAULT_CHECK_INTERVAL`
- `SUBSCRIPTION_SCAN_PLAYLIST_END`
- `SUBSCRIPTION_MAX_SEEN_IDS`
- `CLEAR_COMPLETED_AFTER`
- `DOWNLOAD_DIR`
- `AUDIO_DOWNLOAD_DIR`
- `CUSTOM_DIRS`
- `CREATE_CUSTOM_DIRS`
- `CUSTOM_DIRS_EXCLUDE_REGEX`
- `DOWNLOAD_DIRS_INDEXABLE`
- `STATE_DIR`
- `TEMP_DIR`
- `OUTPUT_TEMPLATE`
- `OUTPUT_TEMPLATE_CHAPTER`
- `OUTPUT_TEMPLATE_PLAYLIST`
- `OUTPUT_TEMPLATE_CHANNEL`
- `YTDL_OPTIONS`
- `YTDL_OPTIONS_FILE`
- `YTDL_OPTIONS_PRESETS`
- `YTDL_OPTIONS_PRESETS_FILE`
- `ALLOW_YTDL_OPTIONS_OVERRIDES`
- `HOST`
- `PORT`
- `URL_PREFIX`
- `PUBLIC_HOST_URL`
- `PUBLIC_HOST_AUDIO_URL`
- `HTTPS`
- `CERTFILE`
- `KEYFILE`
- `CORS_ALLOWED_ORIGINS`
- `PUID`, `PGID`, `UID`, `GID`, `UMASK`
- `DEFAULT_THEME`
- `LOGLEVEL`
- `ENABLE_ACCESSLOG`

Desktop-only defaults are applied only when a variable is not already set:

- `HOST=127.0.0.1`
- `DOWNLOAD_DIR=%USERPROFILE%\Neo Apps\NeoTube Downloader\Downloads`
- `STATE_DIR=%USERPROFILE%\Neo Apps\NeoTube Downloader\.neotube`
- `TEMP_DIR=%USERPROFILE%\Neo Apps\NeoTube Downloader\Temp`
- `YTDL_OPTIONS={"concurrent_fragment_downloads": 8, "retries": 10, "fragment_retries": 10, "continuedl": true, "noprogress": false}`
- `MAX_CONCURRENT_DOWNLOADS=4`
- `PORT=8081`, or a free local port if 8081 is already in use

## Notes

NeoTube Downloader uses yt-dlp behavior. Some conversions require `ffmpeg` to
be available. The desktop build bundles `ffmpeg.exe` and `ffprobe.exe` and sets
`ffmpeg_location` automatically, so MP3 conversion works without a separate
system install.

Startup diagnostics are written to `neotube-downloader.log` beside the EXE.
