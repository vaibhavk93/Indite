"""
Is indite self-contained? (17 Oct: the app sent to another Mac ran code, libraries and the model from the founder's
project folder, was built for macOS 26 only, and its engine looked for its parts in an old folder.)

    python mac/portable_check.py deps            # the libraries the app really loads (used by build_portable.sh)
    python mac/portable_check.py where           # run INSIDE the built app: anything loaded from outside it fails
    python mac/portable_check.py bundle <app>    # static checks on a built app: paths, macOS version, chip, files

Every module the app can ever import is imported here, including the ones it loads only on first use (who spoke,
files, AI, the player), so a missing library shows up now and not on someone else's Mac.
"""

from __future__ import annotations

import importlib
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

APP_MODULES = ["indite_mac", "window", "overlay", "player", "meeting", "system_audio", "calls", "speakers", "review",
               "wordtimes", "digits", "ai", "store", "indite.core", "indite.styles", "indite.notes", "indite.guards"]
LAZY = ["av", "sherpa_onnx", "AVFoundation", "WebKit", "ScreenCaptureKit", "CoreMedia", "Quartz", "AppKit",
        "Foundation", "PyObjCTools.AppHelper", "sounddevice", "pynput.keyboard", "rumps", "numpy", "httpx", "truststore",
        "ssl", "zipfile", "wave", "json", "urllib.request", "ctypes.util", "difflib", "faulthandler", "uuid"]
MIN_MACOS = (14, 0)        # numpy and av wheels, and the call detector, need macOS 14
FILES = ["mac/ui/app.html", "mac/models/ggml-apex-q5_k.bin", "mac/models/titanet_small.onnx", "mac/spelling.tsv",
         ".tools/whisper.cpp/build/bin/whisper-server", "mac/brand/indite.icns"]


def load_all() -> None:
    for name in APP_MODULES + LAZY:
        importlib.import_module(name)


def deps() -> list[str]:
    """Top-level names under site-packages that the app loads."""
    load_all()
    out = set()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None) or ""
        if "site-packages" in f:
            out.add(f.split("site-packages/", 1)[1].split("/", 1)[0])
    return sorted(out)


def where() -> int:
    """Inside the built app: every loaded file must come from the app itself or from macOS."""
    load_all()
    app = Path(sys.executable).resolve().parents[2]          # .../Contents/Resources
    bad = sorted({f for m in list(sys.modules.values()) if (f := getattr(m, "__file__", None) or "")
                  and not f.startswith((str(app), "/System/", "/usr/lib/", "/Library/Apple/"))})
    for f in bad:
        print("loaded from outside the app:", f)
    print("where:", "ok" if not bad else f"{len(bad)} file(s) from outside")
    return 1 if bad else 0


def macho(path: Path) -> bool:
    with open(path, "rb") as f:
        return f.read(4) in (b"\xcf\xfa\xed\xfe", b"\xca\xfe\xba\xbe", b"\xfe\xed\xfa\xcf")


def bundle(app: Path) -> int:
    """Static checks: no path to a home folder anywhere, every binary runs on macOS 13 and on arm64, files present."""
    res, problems = app / "Contents/Resources", []
    for f in FILES:
        if not (res / "app" / f).exists():
            problems.append(f"missing: {f}")
    for p in sorted(res.rglob("*")):
        if p.is_symlink() and not p.resolve().is_relative_to(app.resolve()):
            problems.append(f"link out of the app: {p.relative_to(app)} -> {p.resolve()}")
        if not p.is_file() or p.is_symlink():
            continue
        if p.suffix in (".sh", ".cfg", ".pth", ".txt", ".py", ".plist") and p.stat().st_size < 2_000_000:
            text = p.read_text(errors="ignore")
            if "/Users/" in text and p.suffix != ".py":            # .py files may mention paths in comments/docs
                problems.append(f"home-folder path in {p.relative_to(app)}")
        elif p.stat().st_size > 1024 and macho(p):
            info = subprocess.run(["otool", "-l", str(p)], capture_output=True, text=True).stdout
            for v in re.findall(r"minos (\d+)\.(\d+)", info) + re.findall(r"LC_VERSION_MIN_MACOSX.*?version (\d+)\.(\d+)", info, re.S):
                if tuple(map(int, v)) > MIN_MACOS:
                    problems.append(f"needs macOS {v[0]}.{v[1]}: {p.relative_to(app)}")
                    break
            for rp in re.findall(r"path (/(?:Users|opt|usr/local)/\S+)", info):
                if Path(rp).exists():            # a builder's leftover folder elsewhere is harmless; one HERE is not
                    problems.append(f"looks for parts in {rp}: {p.relative_to(app)}")
            libs = subprocess.run(["otool", "-L", str(p)], capture_output=True, text=True).stdout.splitlines()[1:]
            if p.suffix in (".dylib", ".so"):
                libs = libs[1:]                          # a library's first line is its own name, not a need
            for lib in re.findall(r"^\s+(/(?:Users|opt|usr/local)/\S+)", "\n".join(libs), re.M):
                problems.append(f"needs {lib}: {p.relative_to(app)}")
            archs = subprocess.run(["lipo", "-archs", str(p)], capture_output=True, text=True).stdout.split()
            if archs and "arm64" not in archs:
                problems.append(f"not for Apple Silicon: {p.relative_to(app)}")
    seen = set()
    for p in problems:
        if p not in seen:
            print("✗", p)
            seen.add(p)
    print("bundle:", "ok" if not problems else f"{len(seen)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    verb = sys.argv[1] if len(sys.argv) > 1 else ""
    if verb == "deps":
        print("\n".join(deps()))
    elif verb == "where":
        sys.exit(where())
    elif verb == "bundle":
        sys.exit(bundle(Path(sys.argv[2])))
    else:
        print(__doc__)
