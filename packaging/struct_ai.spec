# Diagnostic desktop + draft section file commands. NOT the complete M14 installer/export gate.
import platform
import struct
import sys
from pathlib import Path

from PyInstaller.depend.bindepend import resolve_library_path
from PyInstaller.utils.hooks import collect_all, copy_metadata, get_package_paths

root = Path(SPECPATH).parent
native_package = "openseespywin" if sys.platform == "win32" else "openseespylinux"
if sys.platform not in ("win32", "linux"):
    raise RuntimeError("The packaging spike supports Windows x64 and supplementary Linux x64 only")
if struct.calcsize("P") != 8 or platform.machine().lower() not in ("amd64", "x86_64"):
    raise RuntimeError("The selected native OpenSees wheels require an x86-64 build interpreter")
if sys.platform == "win32" and sys.version_info[:2] != (3, 12):
    raise RuntimeError("openseespywin 3.7.1.2 requires CPython 3.12 x64")

datas = []
binaries = []
hiddenimports = ["PySide6.QtSvg", f"{native_package}.opensees"]
for package in ("openseespy", native_package):
    package_data, package_binaries, package_hidden = collect_all(package)
    datas += package_data
    binaries += package_binaries
    hiddenimports += package_hidden

# The native wheels use broad tags. Explicitly include pyd/DLL/versioned .so files,
# not only Python modules or libraries matching the unversioned '*.so' pattern.
_, native_root = get_package_paths(native_package)
for file in sorted(Path(native_root).rglob("*")):
    if file.is_file() and (file.suffix in (".pyd", ".dll") or ".so" in file.name):
        destination = str(Path(native_package) / file.relative_to(native_root).parent)
        binaries.append((str(file), destination))

# PyInstaller ordinarily excludes system graphics libraries. The supplementary
# Linux offscreen test must not rely on a developer-only LD_LIBRARY_PATH.
# No Linux GPU driver is bundled or claimed to be certified.
if sys.platform == "linux":
    for library in (
        "libGL.so.1",
        "libEGL.so.1",
        "libGLX.so.0",
        "libGLdispatch.so.0",
        "libxkbcommon.so.0",
        "libdbus-1.so.3",
    ):
        resolved = resolve_library_path(library)
        if resolved is None:
            raise RuntimeError(f"Install the required Linux diagnostic library: {library}")
        binaries.append((resolved, "."))

package_root = root / "struct_ai"
for pattern in ("codes/*/data/*.json", "gui/resources/**/*"):
    for file in sorted(package_root.glob(pattern)):
        if file.is_file():
            datas.append(
                (str(file), str(Path("struct_ai") / file.relative_to(package_root).parent))
            )
for package in (
    "openseespy",
    native_package,
    "PySide6-Essentials",
    "shiboken6",
    "pydantic",
    "pydantic-core",
    "annotated-types",
    "typing-extensions",
    "typing-inspection",
):
    datas += copy_metadata(package)

a = Analysis(
    [str(root / "packaging/spike_entry.py")],
    pathex=[str(root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    runtime_hooks=[str(root / "packaging/hooks/runtime_native.py")],
    excludes=[
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.QtWebEngineQuick",
        "PyQt5",
        "PyQt6",
        "torch",
        "ollama",
        "tkinter",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="struct_ai",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=str(package_root / "gui/resources/app-icon.ico") if sys.platform == "win32" else None,
    version=str(root / "packaging/version_info.txt") if sys.platform == "win32" else None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="struct_ai")
