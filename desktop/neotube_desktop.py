import logging
import multiprocessing
import os
import queue
import json
import socket
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

from aiohttp import web
import engineio.async_drivers.aiohttp  # noqa: F401 - required in frozen Socket.IO builds


APP_NAME = "NeoTube Downloader"
SERVER_ERRORS = queue.Queue()
SETTINGS_FILE_NAME = "desktop-settings.json"
DESKTOP_DEFAULT_YTDL_OPTIONS = {
    "concurrent_fragment_downloads": 8,
    "retries": 10,
    "fragment_retries": 10,
    "continuedl": True,
    "noprogress": False,
}
REQUIRED_FFMPEG_ENCODERS = {
    "h264": "libx264",
    "h265": "libx265",
    "av1": "libaom-av1",
    "vp9": "libvpx-vp9",
    "m4a": "aac",
    "mp3": "libmp3lame",
    "opus": "libopus",
    "wav": "pcm_s16le",
    "flac": "flac",
}


STARTUP_HTML = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>NeoTube Downloader</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      font-family: "Segoe UI", Arial, sans-serif;
      color: #17202a;
      background: #f5f7fb;
      display: grid;
      place-items: center;
    }
    main {
      width: min(720px, calc(100vw - 48px));
      background: #fff;
      border: 1px solid #d8dee9;
      border-radius: 8px;
      padding: 28px;
      box-shadow: 0 18px 46px rgba(26, 35, 50, 0.12);
    }
    h1 { margin: 0 0 8px; font-size: 24px; font-weight: 650; }
    p { margin: 0 0 22px; color: #526070; line-height: 1.45; }
    label {
      display: block;
      margin-bottom: 8px;
      font-size: 13px;
      font-weight: 650;
      color: #344256;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      align-items: center;
    }
    input {
      width: 100%;
      height: 40px;
      border: 1px solid #c4ccda;
      border-radius: 6px;
      padding: 0 12px;
      font-size: 14px;
    }
    button {
      height: 40px;
      border: 1px solid #bcc6d5;
      border-radius: 6px;
      background: #fff;
      color: #1f2a3a;
      font-weight: 650;
      padding: 0 16px;
      cursor: pointer;
    }
    button.primary {
      border-color: #1f6feb;
      background: #1f6feb;
      color: #fff;
    }
    .actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-top: 22px;
    }
    .check {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: #526070;
      font-size: 13px;
    }
    .check input {
      width: 16px;
      height: 16px;
    }
    #status {
      min-height: 20px;
      margin-top: 14px;
      color: #b42318;
      font-size: 13px;
    }
  </style>
</head>
<body>
  <main>
    <h1>NeoTube Downloader</h1>
    <p>Neo Apps downloader setup. Select where downloaded files should be saved before the app starts.</p>
    <label for="folder">Download folder</label>
    <div class="row">
      <input id="folder" spellcheck="false" autocomplete="off">
      <button id="browse" type="button">Browse</button>
    </div>
    <div class="actions">
      <label class="check">
        <input id="remember" type="checkbox" checked>
        Remember this folder
      </label>
      <button class="primary" id="start" type="button">Start Downloader</button>
    </div>
    <div id="status"></div>
  </main>
  <script>
    const folder = document.getElementById('folder');
    const remember = document.getElementById('remember');
    const status = document.getElementById('status');
    const start = document.getElementById('start');
    const browse = document.getElementById('browse');

    function setBusy(isBusy) {
      start.disabled = isBusy;
      browse.disabled = isBusy;
      start.textContent = isBusy ? 'Starting...' : 'Start Downloader';
    }

    window.addEventListener('pywebviewready', async () => {
      const settings = await window.pywebview.api.get_startup_settings();
      folder.value = settings.download_dir;
    });

    browse.addEventListener('click', async () => {
      const selected = await window.pywebview.api.choose_download_dir(folder.value);
      if (selected) {
        folder.value = selected;
        status.textContent = '';
      }
    });

    start.addEventListener('click', async () => {
      status.textContent = '';
      setBusy(true);
      const result = await window.pywebview.api.start_downloader(folder.value, remember.checked);
      if (!result.ok) {
        status.textContent = result.error || 'Unable to start NeoTube Downloader.';
        setBusy(false);
      }
    });
  </script>
</body>
</html>"""


def _runtime_root() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[1]


def _exe_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _desktop_settings_path(data_dir: Path) -> Path:
    return data_dir / ".neotube" / SETTINGS_FILE_NAME


def _read_desktop_settings(data_dir: Path) -> dict:
    path = _desktop_settings_path(data_dir)
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as settings:
            data = json.load(settings)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_desktop_settings(data_dir: Path, settings: dict) -> None:
    path = _desktop_settings_path(data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)


def _merge_ytdl_options(defaults: dict) -> str:
    raw = os.environ.get("YTDL_OPTIONS")
    if not raw:
        return json.dumps(defaults)
    try:
        user_options = json.loads(raw)
        if not isinstance(user_options, dict):
            raise ValueError("YTDL_OPTIONS must be a JSON object")
    except Exception:
        return raw
    merged = dict(defaults)
    merged.update(user_options)
    return json.dumps(merged)


def _log_ffmpeg_support(ffmpeg_bin: Path) -> None:
    ffmpeg_exe = ffmpeg_bin / "ffmpeg.exe"
    if not ffmpeg_exe.exists():
        logging.warning("Bundled FFmpeg was not found at %s", ffmpeg_exe)
        return
    try:
        proc = subprocess.run(
            [str(ffmpeg_exe), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception as exc:
        logging.warning("Could not inspect FFmpeg encoder support: %s", exc)
        return
    encoders = proc.stdout + proc.stderr
    missing = [
        f"{name} ({encoder})"
        for name, encoder in REQUIRED_FFMPEG_ENCODERS.items()
        if encoder not in encoders
    ]
    if missing:
        logging.warning("Bundled FFmpeg is missing encoder support: %s", ", ".join(missing))
    else:
        logging.info(
            "Bundled FFmpeg supports H.264, H.265, AV1, VP9, MP4 remuxing, M4A, MP3, Opus, WAV, and FLAC"
        )


def _setup_logging() -> Path:
    log_dir = Path(os.environ.get("NEOTUBE_DESKTOP_LOG_DIR", _exe_dir()))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "neotube-downloader.log"
    logging.basicConfig(
        filename=log_file,
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )
    return log_file


def _first_free_port(preferred: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _prepare_environment() -> Path:
    root = _runtime_root()

    _load_dotenv(_exe_dir() / ".env")
    _load_dotenv(root / ".env")

    data_dir = Path(os.environ.get("NEOTUBE_DESKTOP_DATA_DIR", Path.home() / "Neo Apps" / APP_NAME))
    desktop_settings = _read_desktop_settings(data_dir)
    saved_download_dir = desktop_settings.get("download_dir")
    initial_download_dir = Path(
        os.environ.get("DOWNLOAD_DIR") or saved_download_dir or data_dir / "Downloads"
    )
    ytdl_defaults = dict(DESKTOP_DEFAULT_YTDL_OPTIONS)
    ffmpeg_bin = root / "ffmpeg" / "bin"
    if (ffmpeg_bin / "ffmpeg.exe").exists():
        ytdl_defaults["ffmpeg_location"] = str(ffmpeg_bin)

    defaults = {
        "BASE_DIR": str(root),
        "HOST": "127.0.0.1",
        "PORT": str(_first_free_port(int(os.environ.get("PORT", "8081")))),
        "DOWNLOAD_DIR": str(initial_download_dir),
        "AUDIO_DOWNLOAD_DIR": "%%DOWNLOAD_DIR",
        "STATE_DIR": str(data_dir / ".neotube"),
        "TEMP_DIR": str(initial_download_dir / ".neotube-temp"),
        "MAX_CONCURRENT_DOWNLOADS": "4",
        "LOGLEVEL": "INFO",
        "ENABLE_ACCESSLOG": "false",
    }

    for key, value in defaults.items():
        os.environ.setdefault(key, value)

    os.environ["YTDL_OPTIONS"] = _merge_ytdl_options(ytdl_defaults)

    for key in ("DOWNLOAD_DIR", "STATE_DIR", "TEMP_DIR"):
        Path(os.environ[key]).mkdir(parents=True, exist_ok=True)

    app_dir = root / "app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    return root


def _apply_download_dir(download_dir: str, remember: bool) -> None:
    if not str(download_dir or "").strip():
        raise ValueError("Select a download folder.")
    selected = Path(download_dir).expanduser()
    selected.mkdir(parents=True, exist_ok=True)
    if not selected.is_dir():
        raise ValueError("The selected download path is not a folder.")

    os.environ["DOWNLOAD_DIR"] = str(selected)
    if os.environ.get("AUDIO_DOWNLOAD_DIR") == "%%DOWNLOAD_DIR":
        os.environ["AUDIO_DOWNLOAD_DIR"] = "%%DOWNLOAD_DIR"
    if not os.environ.get("NEOTUBE_DESKTOP_KEEP_TEMP_DIR"):
        temp_dir = selected / ".neotube-temp"
        temp_dir.mkdir(parents=True, exist_ok=True)
        os.environ["TEMP_DIR"] = str(temp_dir)

    if remember:
        data_dir = Path(
            os.environ.get("NEOTUBE_DESKTOP_DATA_DIR", Path.home() / "Neo Apps" / APP_NAME)
        )
        settings = _read_desktop_settings(data_dir)
        settings["download_dir"] = str(selected)
        _write_desktop_settings(data_dir, settings)


def _wait_for_server(url: str, timeout: float = 60.0) -> None:
    import urllib.request

    deadline = time.monotonic() + timeout
    last_error = None
    while time.monotonic() < deadline:
        try:
            exc = SERVER_ERRORS.get_nowait()
        except queue.Empty:
            exc = None
        if exc is not None:
            raise RuntimeError(f"{APP_NAME} backend failed to start: {exc}") from exc

        try:
            with urllib.request.urlopen(url, timeout=1.0):
                return
        except Exception as exc:  # pragma: no cover - startup timing guard
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {APP_NAME} at {url}: {last_error}")


def _url_prefix() -> str:
    prefix = os.environ.get("URL_PREFIX", "/") or "/"
    if not prefix.startswith("/"):
        prefix = "/" + prefix
    if not prefix.endswith("/"):
        prefix += "/"
    return prefix


def _run_server():
    try:
        import main as neotube_main

        logging.getLogger().setLevel(
            neotube_main.parseLogLevel(neotube_main.config.LOGLEVEL) or logging.INFO
        )

        if os.path.exists(neotube_main.COOKIES_PATH):
            neotube_main.config.set_runtime_override("cookiefile", neotube_main.COOKIES_PATH)

        ssl_context = None
        if neotube_main.config.HTTPS:
            import ssl

            ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_context.load_cert_chain(
                certfile=neotube_main.config.CERTFILE,
                keyfile=neotube_main.config.KEYFILE,
            )

        web.run_app(
            neotube_main.app,
            host=neotube_main.config.HOST,
            port=int(neotube_main.config.PORT),
            reuse_port=neotube_main.supports_reuse_port(),
            ssl_context=ssl_context,
            access_log=neotube_main.isAccessLogEnabled(),
            handle_signals=False,
            print=None,
        )
    except BaseException as exc:
        logging.critical("%s backend failed to start\n%s", APP_NAME, traceback.format_exc())
        SERVER_ERRORS.put(exc)


class StartupApi:
    def __init__(self, url: str, window_holder: dict):
        self.url = url
        self.window_holder = window_holder
        self.server_started = False

    def get_startup_settings(self):
        return {"download_dir": os.environ["DOWNLOAD_DIR"]}

    def choose_download_dir(self, current_dir: str):
        import webview

        window = self.window_holder["window"]
        result = window.create_file_dialog(
            webview.FOLDER_DIALOG,
            directory=current_dir or os.environ["DOWNLOAD_DIR"],
        )
        if not result:
            return None
        return result[0] if isinstance(result, (list, tuple)) else result

    def start_downloader(self, download_dir: str, remember: bool):
        if self.server_started:
            return {"ok": True}
        try:
            _apply_download_dir(download_dir, remember)
            logging.info("Using download directory: %s", os.environ["DOWNLOAD_DIR"])
            server_thread = threading.Thread(target=_run_server, name="neotube-backend", daemon=True)
            server_thread.start()
            _wait_for_server(self.url)
            self.server_started = True
            self.window_holder["window"].load_url(self.url)
            return {"ok": True}
        except Exception as exc:
            logging.exception("Unable to start %s", APP_NAME)
            return {"ok": False, "error": str(exc)}


def main() -> int:
    _prepare_environment()
    log_file = _setup_logging()
    scheme = "https" if os.environ.get("HTTPS", "").lower() in {"true", "on", "1"} else "http"
    url = f"{scheme}://127.0.0.1:{os.environ['PORT']}{_url_prefix()}"
    logging.info("Starting %s at %s; log=%s", APP_NAME, url, log_file)
    _log_ffmpeg_support(_runtime_root() / "ffmpeg" / "bin")

    import webview

    if os.environ.get("NEOTUBE_DESKTOP_SKIP_FOLDER_DIALOG", "").lower() in {"1", "true", "yes"}:
        server_thread = threading.Thread(target=_run_server, name="neotube-backend", daemon=True)
        server_thread.start()
        _wait_for_server(url)
        webview.create_window(APP_NAME, url, width=1280, height=820, min_size=(960, 640))
    else:
        window_holder = {}
        api = StartupApi(url, window_holder)
        window_holder["window"] = webview.create_window(
            APP_NAME,
            html=STARTUP_HTML,
            js_api=api,
            width=760,
            height=460,
            min_size=(680, 420),
        )
    webview.start()
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())
