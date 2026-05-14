import logging
import json
import os
import socket
import sys
import threading
from pathlib import Path

from aiohttp import web


_server_thread = None
_server_url = None
_dns_fallback_installed = False


def _install_android_dns_fallback():
    global _dns_fallback_installed
    if _dns_fallback_installed:
        return

    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        try:
            return original_getaddrinfo(host, port, family, type, proto, flags)
        except socket.gaierror:
            from java.net import InetAddress

            results = []
            socktype = type or socket.SOCK_STREAM
            protocol = proto or (socket.IPPROTO_TCP if socktype == socket.SOCK_STREAM else 0)
            if port in (None, ""):
                resolved_port = 0
            elif isinstance(port, str) and not port.isdigit():
                resolved_port = {"http": 80, "https": 443}.get(port, 0)
            else:
                resolved_port = int(port)
            for addr in InetAddress.getAllByName(str(host)):
                ip = str(addr.getHostAddress()).split("%", 1)[0]
                addr_family = socket.AF_INET6 if ":" in ip else socket.AF_INET
                if family not in (0, socket.AF_UNSPEC, addr_family):
                    continue
                sockaddr = (ip, resolved_port, 0, 0) if addr_family == socket.AF_INET6 else (ip, resolved_port)
                results.append((addr_family, socktype, protocol, "", sockaddr))
            if results:
                return results
            raise

    socket.getaddrinfo = getaddrinfo
    _dns_fallback_installed = True


def _first_free_port(preferred):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        if sock.connect_ex(("127.0.0.1", preferred)) != 0:
            return preferred

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start(files_dir, download_dir, ffmpeg_dir=None, ffmpeg_kit=False):
    global _server_thread, _server_url
    if _server_thread is not None:
        return _server_url

    files_dir = Path(str(files_dir))
    download_dir = Path(str(download_dir))
    web_root = files_dir / "www"
    python_root = Path(__file__).resolve().parent
    app_dir = python_root / "neotube_app"
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    state_dir = files_dir / ".neotube"
    temp_dir = files_dir / ".neotube-temp"
    state_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("NEOTUBE_ANDROID", "1")
    _install_android_dns_fallback()
    os.environ.setdefault("BASE_DIR", str(web_root))
    os.environ.setdefault("HOST", "127.0.0.1")
    os.environ.setdefault("PORT", str(_first_free_port(18081)))
    os.environ.setdefault("DOWNLOAD_DIR", str(download_dir))
    os.environ.setdefault("AUDIO_DOWNLOAD_DIR", "%%DOWNLOAD_DIR")
    os.environ.setdefault("STATE_DIR", str(state_dir))
    os.environ.setdefault("TEMP_DIR", str(temp_dir))
    os.environ.setdefault("MAX_CONCURRENT_DOWNLOADS", "2")
    os.environ.setdefault("LOGLEVEL", "INFO")
    os.environ.setdefault("ENABLE_ACCESSLOG", "false")
    if ffmpeg_kit:
        os.environ.setdefault("NEOTUBE_ANDROID_FFMPEG_KIT", "1")
        os.environ.setdefault(
            "YTDL_OPTIONS",
            json.dumps({
                "source_address": "0.0.0.0",
            }),
        )
    elif ffmpeg_dir:
        ffmpeg_path = Path(str(ffmpeg_dir)) / "ffmpeg"
        os.environ.setdefault("NEOTUBE_ANDROID_FFMPEG", str(ffmpeg_path))
        os.environ.setdefault(
            "YTDL_OPTIONS",
            json.dumps({
                "ffmpeg_location": str(ffmpeg_path),
                "source_address": "0.0.0.0",
            }),
        )
    else:
        os.environ.setdefault("NEOTUBE_ANDROID_NO_FFMPEG", "1")
        os.environ.setdefault("YTDL_OPTIONS", "{}")

    logging.basicConfig(level=logging.INFO, force=True)

    import main as neotube_main
    if ffmpeg_kit:
        neotube_main.config.set_runtime_override("source_address", "0.0.0.0")
    elif ffmpeg_dir:
        neotube_main.config.set_runtime_override("ffmpeg_location", os.environ["NEOTUBE_ANDROID_FFMPEG"])
        neotube_main.config.set_runtime_override("source_address", "0.0.0.0")

    def run_server():
        web.run_app(
            neotube_main.app,
            host=neotube_main.config.HOST,
            port=int(neotube_main.config.PORT),
            reuse_port=neotube_main.supports_reuse_port(),
            access_log=neotube_main.isAccessLogEnabled(),
            handle_signals=False,
            print=None,
        )

    _server_url = f"http://127.0.0.1:{os.environ['PORT']}/"
    _server_thread = threading.Thread(target=run_server, name="neotube-android-backend", daemon=True)
    _server_thread.start()
    return _server_url
