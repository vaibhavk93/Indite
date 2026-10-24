#!/bin/bash
# Builds inditeflow.app - a real Mac app bundle, so macOS has one stable thing to grant Accessibility to.
# Without a bundle, the permission attaches to whatever launched the script (Terminal, or Claude, or iTerm),
# which is why granting it to a python binary never stuck.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"   # -P: the real folder, never the Desktop symlink macOS blocks
APP="$ROOT/dist/inditeflow.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Inditeflow</string>
  <key>CFBundleDisplayName</key><string>Inditeflow</string>
  <key>CFBundleIdentifier</key><string>com.inditeflow.mac</string>
  <key>CFBundleVersion</key><string>$(cat "$ROOT/mac/VERSION")</string>
  <key>CFBundleShortVersionString</key><string>$(cat "$ROOT/mac/VERSION")</string>
  <key>CFBundleExecutable</key><string>inditeflow</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>inditeflow</string>
  <key>LSUIElement</key><true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>Inditeflow turns what you say into text. The recording stays on this Mac and is deleted straight after.</string>
  <key>NSAppleEventsUsageDescription</key>
  <string>Inditeflow types the text into the app you are using.</string>
</dict>
</plist>
PLIST

# -u: print at once, so the log shows each dictation (without it nothing appeared until the buffer filled)
# Python lives INSIDE the bundle (a copy of the interpreter, ~70 MB), the code and libraries stay in this folder.
# macOS checks Screen & System Audio Recording against the program actually running: with the interpreter outside
# the app, the switch for "Inditeflow" never applied and meetings could not hear calls (15 Oct, log said False).
PY_HOME="$("$ROOT/.venv/bin/python" -c 'import sys; print(sys.base_prefix)')"
cp -R "$PY_HOME" "$APP/Contents/Resources/python"
SITE="$("$ROOT/.venv/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
cat > "$APP/Contents/Resources/run.sh" <<LAUNCH
#!/bin/bash
export PYTHONPATH="$SITE:$ROOT"
export PYTHONNOUSERSITE=1
# Python writes .pyc files next to the .py files it imports. Inside a signed bundle that breaks the signature's
# seal, and macOS then stops trusting the app - which is how Accessibility kept switching itself off mid-session
# (16 Oct: "key access allowed: True" ... "This process is not trusted!"). Never write bytecode into the bundle.
export PYTHONDONTWRITEBYTECODE=1
HERE="\$(cd "\$(dirname "\$0")" && pwd)"
exec "\$HERE/python/bin/python3" -u "$ROOT/mac/inditeflow_mac.py" >> "\$HOME/Library/Logs/inditeflow-mac.log" 2>&1
LAUNCH
chmod +x "$APP/Contents/Resources/run.sh"
# The app's executable is a tiny program that keeps running as the parent (mac/launcher.c says why).
clang -O2 -o "$APP/Contents/MacOS/inditeflow" "$ROOT/mac/launcher.c"
cp "$ROOT/mac/brand/inditeflow.icns" "$APP/Contents/Resources/inditeflow.icns"     # the logo (mac/brand/logo.svg)

# An ad-hoc signature gives the bundle a stable identity, so the Accessibility tick survives a rebuild.
# Any stray bytecode from a previous run has to go before signing, or the new signature seals files that will
# differ the moment the app runs again.
find "$APP" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true
find "$APP" -name "*.pyc" -delete 2>/dev/null || true
codesign --force --deep --sign - "$APP" 2>/dev/null || echo "note: could not sign; the tick may not survive a rebuild"
if codesign --verify --deep --strict "$APP" 2>/dev/null; then
    echo "signature: sealed and valid"
else
    echo "⚠ signature did NOT verify - macOS will drop Accessibility again. Do not ship this build."
fi
echo "built: $APP"
echo "log:   ~/Library/Logs/inditeflow-mac.log"
