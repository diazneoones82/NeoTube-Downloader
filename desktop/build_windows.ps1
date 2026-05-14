$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = $env:PYTHON
if (-not $Python) {
  $LocalPython = Join-Path $RepoRoot "build\tools\Python313\python.exe"
  if (Test-Path $LocalPython) {
    $Python = $LocalPython
  } else {
    $Python = "C:\Users\Admin\AppData\Local\Python\bin\python.exe"
  }
}

if (-not (Test-Path $Python)) {
  throw "Python was not found. Set the PYTHON environment variable to a Python 3.13+ executable."
}

Push-Location $RepoRoot
try {
  $FfmpegBin = Join-Path $RepoRoot "build\tools\ffmpeg\bin"
  $FfmpegExe = Join-Path $FfmpegBin "ffmpeg.exe"
  if (-not (Test-Path $FfmpegExe)) {
    $ToolsDir = Join-Path $RepoRoot "build\tools"
    $FfmpegZip = Join-Path $ToolsDir "ffmpeg-release-essentials.zip"
    New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
    Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $FfmpegZip
    Expand-Archive -LiteralPath $FfmpegZip -DestinationPath $ToolsDir -Force
    $ExtractedBin = Get-ChildItem -Path $ToolsDir -Directory -Filter "ffmpeg-*-essentials_build" |
      Sort-Object LastWriteTime -Descending |
      Select-Object -First 1 |
      ForEach-Object { Join-Path $_.FullName "bin" }
    if (-not $ExtractedBin -or -not (Test-Path (Join-Path $ExtractedBin "ffmpeg.exe"))) {
      throw "Could not locate ffmpeg.exe after extracting $FfmpegZip"
    }
    New-Item -ItemType Directory -Force -Path $FfmpegBin | Out-Null
    Copy-Item -LiteralPath (Join-Path $ExtractedBin "ffmpeg.exe") -Destination $FfmpegBin -Force
    Copy-Item -LiteralPath (Join-Path $ExtractedBin "ffprobe.exe") -Destination $FfmpegBin -Force
    Remove-Item -LiteralPath $FfmpegZip -Force
  }

  if (-not (Test-Path "ui\dist\neotube\browser\index.html")) {
    if (Get-Command pnpm -ErrorAction SilentlyContinue) {
      Push-Location "ui"
      pnpm install --frozen-lockfile
      pnpm run build
      Pop-Location
    } else {
      throw "Frontend assets are missing and pnpm is not available. Install pnpm, then run: cd ui; pnpm install --frozen-lockfile; pnpm run build"
    }
  }

  & $Python -m pip install --upgrade `
    aiohttp `
    "python-socketio>=5.0,<6.0" `
    "yt-dlp[default,curl-cffi,deno]" `
    mutagen `
    curl-cffi `
    watchfiles `
    pywebview `
    pyinstaller

  & $Python -m PyInstaller --clean --noconfirm "desktop\neotube_desktop.spec"

  $DistDir = Join-Path "dist" "NeoTube Downloader Standalone"
  New-Item -ItemType Directory -Force -Path $DistDir | Out-Null
  $StandaloneExe = Join-Path "dist" "NeoTube Downloader.exe"
  $PortableExe = Join-Path $DistDir "NeoTube Downloader.exe"
  if (-not (Test-Path $StandaloneExe)) {
    throw "PyInstaller did not create $StandaloneExe"
  }
  Copy-Item -LiteralPath $StandaloneExe -Destination $PortableExe -Force

  $EnvTemplate = Join-Path $DistDir ".env.example"
  @"
# NeoTube Downloader reads this file on startup. Real environment variables still win.
# All downloader options are supported, including:
# DOWNLOAD_DIR, AUDIO_DOWNLOAD_DIR, STATE_DIR, TEMP_DIR, OUTPUT_TEMPLATE,
# YTDL_OPTIONS, YTDL_OPTIONS_FILE, YTDL_OPTIONS_PRESETS,
# YTDL_OPTIONS_PRESETS_FILE, ALLOW_YTDL_OPTIONS_OVERRIDES, HOST, PORT,
# URL_PREFIX, PUBLIC_HOST_URL, PUBLIC_HOST_AUDIO_URL, HTTPS, CERTFILE,
# KEYFILE, DEFAULT_THEME, MAX_CONCURRENT_DOWNLOADS, LOGLEVEL, ENABLE_ACCESSLOG.
# ffmpeg.exe is bundled and automatically used for MP3 conversion.

DOWNLOAD_DIR=$env:USERPROFILE\Neo Apps\NeoTube Downloader\Downloads
STATE_DIR=$env:USERPROFILE\Neo Apps\NeoTube Downloader\.neotube
TEMP_DIR=$env:USERPROFILE\Neo Apps\NeoTube Downloader\Temp
PORT=8081
"@ | Set-Content -Path $EnvTemplate -Encoding UTF8

  Write-Host "Built standalone EXE: $(Resolve-Path $PortableExe)"
  Write-Host "Raw PyInstaller EXE: $(Resolve-Path $StandaloneExe)"
  Write-Host "Optional config template: $(Resolve-Path $EnvTemplate)"
} finally {
  Pop-Location
}
