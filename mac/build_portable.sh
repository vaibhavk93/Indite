#!/bin/bash
# Builds a SELF-CONTAINED inditeflow.app for other Macs: dist/portable/inditeflow.app and dist/portable/inditeflow-mac.zip.
#
# Why (17 Oct): the app sent to another Mac was a 67 MB shell that ran the code, libraries and model from the
# founder's project folder, was built for macOS 26 only, and its engine looked for its parts in an old folder.
# This build carries everything inside the app, works on macOS 14+ on any Apple Silicon Mac (M1-M4), and refuses
# to finish if any of those problems is back (mac/portable_check.py).
#
#   ./mac/build_portable.sh            # needs: .venv, mac/models/*, cmake (for the engine), Xcode command-line tools
#
# The founder's own dist/inditeflow.app (mac/build_app.sh) is not touched.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
OUT="$ROOT/dist/portable"
PKG="$OUT/inditeflow"                                      # what the zip holds: the app and the read-me, side by side
APP="$PKG/inditeflow.app"
RES="$APP/Contents/Resources"
VERSION="$(cat "$ROOT/mac/VERSION")"
ENGINE="$ROOT/.tools/whisper.cpp/build-portable/bin"

# The app is ~1.2 GB and its zip ~0.8 GB. A full disk broke this build once (17 Oct) and can stop Inditeflow itself
# from saving notes, so never start with less than 4 GB free.
free_gb=$(df -g "$ROOT" | awk 'NR==2 {print $4}')
if [ "$free_gb" -lt 4 ]; then
  echo "Only ${free_gb} GB free on this disk; the build needs 4 GB. Free some space and run it again." >&2
  exit 1
fi

# 1. The speech engine: one static file, generic Apple Silicon code (no -mcpu=native), macOS 13+, Metal built in.
if [ ! -x "$ENGINE/whisper-server" ]; then
  (cd "$ROOT/.tools/whisper.cpp" &&
   cmake -B build-portable -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF -DGGML_NATIVE=OFF -DGGML_METAL=ON \
     -DGGML_METAL_EMBED_LIBRARY=ON -DGGML_BLAS=ON -DCMAKE_OSX_DEPLOYMENT_TARGET=13.0 -DCMAKE_OSX_ARCHITECTURES=arm64 \
     -DWHISPER_BUILD_TESTS=OFF -DWHISPER_BUILD_EXAMPLES=ON >/dev/null &&
   cmake --build build-portable -j 4 --target whisper-server whisper-cli >/dev/null)
fi

rm -rf "$OUT"
mkdir -p "$APP/Contents/MacOS" "$RES/app/mac" "$RES/app/.tools/whisper.cpp/build/bin"

# 2. Python itself (a standalone build, macOS 11+).
PY_HOME="$("$ROOT/.venv/bin/python" -c 'import sys; print(sys.base_prefix)')"
cp -R "$PY_HOME" "$RES/python"
for lib in "$RES"/python/lib/libpython*.dylib; do         # its own name tag pointed into the builder's home folder
  install_name_tool -id "@executable_path/../lib/$(basename "$lib")" "$lib" 2>/dev/null || true
done

# 3. Only the libraries the app loads (mac/portable_check.py deps) plus everything they declare they need,
#    copied file by file from each library's own install record. torch, scipy, the web app's server: left out.
INDITEFLOW_DATA="$(mktemp -d)" "$ROOT/.venv/bin/python" - "$ROOT" "$RES/site-packages" <<'PY'
import importlib.metadata as md, re, shutil, subprocess, sys
from pathlib import Path
root, dest = Path(sys.argv[1]), Path(sys.argv[2])
tops = subprocess.run([str(root / ".venv/bin/python"), str(root / "mac/portable_check.py"), "deps"],
                      capture_output=True, text=True, check=True).stdout.split()
owners = md.packages_distributions()
todo = {d for t in tops for d in owners.get(t.split(".")[0], [])}
done = set()
while todo:
    name = todo.pop()
    if name.lower() in done:
        continue
    done.add(name.lower())
    dist = md.distribution(name)
    for req in dist.requires or []:
        if "extra ==" in req:
            continue
        dep = re.split(r"[ ;<>=!~\[(]", req, 1)[0]
        try:
            md.distribution(dep)
            todo.add(dep)
        except md.PackageNotFoundError:
            pass
    base = Path(dist.locate_file(""))
    for f in dist.files or []:
        src = Path(dist.locate_file(f))
        if src.is_file() and "__pycache__" not in f.parts and not str(f).startswith(".."):
            (dest / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / f)
print(f"libraries: {len(done)} packages", file=sys.stderr)
PY

# 4. The app's own code, page, models and engine - the same layout as the project, so no path in the code changes.
cp "$ROOT"/mac/*.py "$ROOT/mac/spelling.tsv" "$ROOT/mac/VERSION" "$RES/app/mac/"
cp -R "$ROOT/mac/ui" "$ROOT/mac/brand" "$ROOT/mac/models" "$RES/app/mac/"
mkdir -p "$RES/app/inditeflow"
cp "$ROOT"/inditeflow/*.py "$RES/app/inditeflow/"
cp "$ENGINE/whisper-server" "$ENGINE/whisper-cli" "$RES/app/.tools/whisper.cpp/build/bin/"
cp "$ROOT/mac/brand/inditeflow.icns" "$RES/inditeflow.icns"
cp "$ROOT/mac/READ_ME_FIRST.txt" "$PKG/READ ME FIRST.txt"

cat > "$RES/run.sh" <<'LAUNCH'
#!/bin/bash
# Everything is inside this app: no path outside it is used. If Inditeflow cannot start, it SAYS so - a menu-bar app
# that quits on its own looks like "I clicked it and nothing happened" (17 Oct, on another Mac).
HERE="$(cd "$(dirname "$0")" && pwd)"
LOG="$HOME/Library/Logs/inditeflow-mac.log"
mkdir -p "$HOME/Library/Logs"
tell() { /usr/bin/osascript -e "display alert \"Inditeflow could not start\" message \"$1\" as critical" >/dev/null 2>&1; }
if [ "$(uname -m)" != "arm64" ]; then tell "Inditeflow needs a Mac with Apple Silicon (M1 or newer). This Mac has an Intel chip."; exit 1; fi
major="$(sw_vers -productVersion | cut -d. -f1)"
if [ "$major" -lt 14 ]; then tell "Inditeflow needs macOS 14 (Sonoma) or newer. This Mac has macOS $(sw_vers -productVersion)."; exit 1; fi
export PYTHONPATH="$HERE/site-packages:$HERE/app"
export PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1    # .pyc files inside the app would break its signature
echo "--- Inditeflow $(cat "$HERE/app/mac/VERSION") starting $(date) on macOS $(sw_vers -productVersion) $(uname -m)" >> "$LOG"
"$HERE/python/bin/python3" -u "$HERE/app/mac/inditeflow_mac.py" >> "$LOG" 2>&1
code=$?
if [ $code -ne 0 ] && [ $code -lt 128 ]; then        # 128+: stopped by a signal (Quit, restart) - not a failure
  why="$(tail -n 4 "$LOG" | tr '"\\' "'/" | cut -c1-300)"
  tell "It stopped with an error. The details are in $LOG.\n\nLast lines:\n$why"
fi
exit $code
LAUNCH
chmod +x "$RES/run.sh"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Inditeflow</string>
  <key>CFBundleDisplayName</key><string>Inditeflow</string>
  <key>CFBundleIdentifier</key><string>com.inditeflow.mac</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleExecutable</key><string>inditeflow</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>inditeflow</string>
  <key>LSUIElement</key><true/>
  <key>LSMinimumSystemVersion</key><string>14.0</string>
  <key>LSArchitecturePriority</key><array><string>arm64</string></array>
  <key>NSMicrophoneUsageDescription</key>
  <string>Inditeflow turns what you say into text, on this Mac.</string>
  <key>NSAppleEventsUsageDescription</key>
  <string>Inditeflow types the text into the app you are using.</string>
</dict>
</plist>
PLIST

clang -O2 -mmacosx-version-min=14.0 -arch arm64 -o "$APP/Contents/MacOS/inditeflow" "$ROOT/mac/launcher.c"

# 5. Checks that stop the build: no home-folder paths, every binary for macOS 13+ and arm64, every file present,
#    and the app imports everything from inside itself.
find "$APP" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
"$ROOT/.venv/bin/python" "$ROOT/mac/portable_check.py" bundle "$APP"
env -i HOME="$(mktemp -d)" INDITEFLOW_DATA="$(mktemp -d)" PYTHONPATH="$RES/site-packages:$RES/app" PYTHONNOUSERSITE=1 \
  PYTHONDONTWRITEBYTECODE=1 "$RES/python/bin/python3" "$RES/app/mac/portable_check.py" where
find "$APP" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict "$APP"
ditto -c -k --sequesterRsrc --keepParent "$PKG" "$OUT/inditeflow-mac.zip"   # straight from the build: no second copy
echo "built: $APP ($(du -sh "$APP" | cut -f1))"
echo "send:  $OUT/inditeflow-mac.zip ($(du -sh "$OUT/inditeflow-mac.zip" | cut -f1)) - it holds the app and READ ME FIRST.txt"
