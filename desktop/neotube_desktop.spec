# pyinstaller --clean --noconfirm desktop/neotube_desktop.spec

from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules


root = Path.cwd()
python_home = Path(sys.executable).resolve().parent

datas = [
    (str(root / "app"), "app"),
    (str(root / "ui" / "dist" / "neotube"), "ui/dist/neotube"),
]
ffmpeg_bin = root / "build" / "tools" / "ffmpeg" / "bin"
if (ffmpeg_bin / "ffmpeg.exe").exists():
    datas.append((str(ffmpeg_bin), "ffmpeg/bin"))
datas += collect_data_files("yt_dlp")

hiddenimports = collect_submodules("yt_dlp")
hiddenimports += [
    "engineio.async_drivers.aiohttp",
]

binaries = []
for dll_name in (
    "python313.dll",
    "python3.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
):
    dll_path = python_home / dll_name
    if dll_path.exists():
        binaries.append((str(dll_path), "."))

for dll_path in (python_home / "DLLs").glob("*.dll"):
    binaries.append((str(dll_path), "DLLs"))

for package_name in (
    "aiohttp",
    "curl_cffi",
    "multidict",
    "propcache",
    "watchfiles",
    "websockets",
    "yarl",
):
    binaries += collect_dynamic_libs(package_name)


a = Analysis(
    [str(root / "desktop" / "neotube_desktop.py")],
    pathex=[str(root), str(root / "app")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="NeoTube Downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "desktop" / "assets" / "neotube-icon.ico"),
)
