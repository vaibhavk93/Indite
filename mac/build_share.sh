#!/bin/bash
# Builds indite.app that runs on ANOTHER Mac (Apple Silicon, macOS 13+): its own Python, its own libraries, the
# models inside. Unlike build_app.sh (a launcher for this folder), nothing here points back at this project.
#
#   ./mac/build_share.sh          -> dist-share/indite.app and dist-share/indite-mac.zip
#
# Not signed with a Developer ID: the first time, the person right-clicks indite.app -> Open -> Open.
# Nothing personal goes in: no history, settings, word fixes, API keys or logins - those live in each person's
# ~/Library/Application Support/indite and Keychain, which this script never reads.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
OUT="$ROOT/dist-share"
APP="$OUT/indite.app"
RES="$APP/Contents/Resources"
PY_HOME="$("$ROOT/.venv/bin/python" -c 'import sys; print(sys.base_prefix)')"
VERSION="0.2"

rm -rf "$OUT"
mkdir -p "$APP/Contents/MacOS" "$RES/app/mac/models" "$RES/app/indite" "$RES/app/.tools/whisper.cpp/build/bin"

echo "1/6 Python (relocatable build, $(basename "$PY_HOME"))"
cp -R "$PY_HOME" "$RES/python"
rm -rf "$RES/python/lib/python3.12/test" "$RES/python/lib/python3.12/idlelib" "$RES/python/lib/python3.12/tkinter" \
       "$RES/python/lib/python3.12/ensurepip"

echo "2/6 Libraries the Mac app uses (no torch: the Mac app never loads it)"
uv pip install --quiet --python "$RES/python/bin/python3" --target "$RES/site" \
    numpy sounddevice pynput rumps av sherpa-onnx sherpa-onnx-core \
    pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz pyobjc-framework-ApplicationServices \
    pyobjc-framework-AVFoundation pyobjc-framework-WebKit pyobjc-framework-CoreMedia \
    pyobjc-framework-ScreenCaptureKit pyobjc-framework-CoreAudio

echo "3/6 indite code"
cp "$ROOT"/mac/*.py "$RES/app/mac/"
cp -R "$ROOT/mac/ui" "$RES/app/mac/ui"
cp "$ROOT/mac/spelling.tsv" "$RES/app/mac/"
cp "$ROOT"/indite/{__init__,core,styles,notes}.py "$RES/app/indite/"

echo "4/6 Models (the speech model and the speaker model, real copies)"
cp "$ROOT/mac/models/ggml-apex-q5_k.bin" "$ROOT/mac/models/titanet_small.onnx" "$RES/app/mac/models/"

echo "5/6 Speech engine, pointed at its own libraries"
BIN="$RES/app/.tools/whisper.cpp/build/bin"
cp "$ROOT/.tools/whisper.cpp/build/bin/whisper-server" "$ROOT/.tools/whisper.cpp/build/bin/whisper-cli" "$BIN/"
cp -P "$ROOT"/.tools/whisper.cpp/build/bin/*.dylib "$BIN/"
cp "$ROOT"/.tools/whisper.cpp/build/bin/*.metal "$BIN/" 2>/dev/null || true
for exe in "$BIN/whisper-server" "$BIN/whisper-cli"; do
    # every search path baked in at build time (one had a space in it: "Voice to Text"), replaced by the app's own
    otool -l "$exe" | awk '/LC_RPATH/{getline; getline; sub(/^ *path /, ""); sub(/ \(offset.*$/, ""); print}' |
    while IFS= read -r old; do install_name_tool -delete_rpath "$old" "$exe" 2>/dev/null || true; done
    install_name_tool -add_rpath "@executable_path" "$exe"
done

if otool -l "$BIN/whisper-server" | grep -A2 LC_RPATH | grep -q "/Users/"; then echo "error: a path from this Mac is still inside the engine"; exit 1; fi

echo "6/6 The app bundle"
cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>indite</string>
  <key>CFBundleDisplayName</key><string>indite</string>
  <key>CFBundleIdentifier</key><string>com.indite.mac</string>
  <key>CFBundleVersion</key><string>$VERSION</string>
  <key>CFBundleShortVersionString</key><string>$VERSION</string>
  <key>CFBundleExecutable</key><string>indite</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>LSMinimumSystemVersion</key><string>13.0</string>
  <key>LSUIElement</key><true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>indite turns what you say into text, on this Mac. The recording is deleted straight after.</string>
  <key>NSAppleEventsUsageDescription</key>
  <string>indite types the text into the app you are using.</string>
</dict>
</plist>
PLIST
cat > "$APP/Contents/MacOS/indite" <<'LAUNCH'
#!/bin/bash
# Everything is inside the app: its Python, its libraries, its models. Logs go where the Mac keeps app logs.
HERE="$(cd "$(dirname "$0")/../Resources" && pwd)"
export PYTHONPATH="$HERE/site:$HERE/app"
export PYTHONNOUSERSITE=1
mkdir -p "$HOME/Library/Logs"
exec "$HERE/python/bin/python3" -u "$HERE/app/mac/indite_mac.py" >> "$HOME/Library/Logs/indite-mac.log" 2>&1
LAUNCH
chmod +x "$APP/Contents/MacOS/indite"

# One ad-hoc signature over everything: Apple Silicon refuses to run unsigned code, and a stable identity keeps the
# Accessibility tick across launches. Not a Developer ID: Gatekeeper still asks once ("right-click -> Open").
codesign --force --deep --sign - "$APP" >/dev/null 2>&1 || echo "note: signing failed"

(cd "$OUT" && ditto -c -k --sequesterRsrc --keepParent indite.app indite-mac.zip)
echo
echo "built: $APP ($(du -sh "$APP" | cut -f1))"
echo "share: $OUT/indite-mac.zip ($(du -sh "$OUT/indite-mac.zip" | cut -f1))"
