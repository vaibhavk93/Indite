#!/bin/bash
# Builds indite.app - a real Mac app bundle, so macOS has one stable thing to grant Accessibility to.
# Without a bundle, the permission attaches to whatever launched the script (Terminal, or Claude, or iTerm),
# which is why granting it to a python binary never stuck.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"   # -P: the real folder, never the Desktop symlink macOS blocks
APP="$ROOT/dist/indite.app"
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cat > "$APP/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>indite</string>
  <key>CFBundleDisplayName</key><string>indite</string>
  <key>CFBundleIdentifier</key><string>com.indite.mac</string>
  <key>CFBundleVersion</key><string>0.1</string>
  <key>CFBundleShortVersionString</key><string>0.1</string>
  <key>CFBundleExecutable</key><string>indite</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>indite</string>
  <key>LSUIElement</key><true/>
  <key>NSMicrophoneUsageDescription</key>
  <string>indite turns what you say into text. The recording stays on this Mac and is deleted straight after.</string>
  <key>NSAppleEventsUsageDescription</key>
  <string>indite types the text into the app you are using.</string>
</dict>
</plist>
PLIST

# -u: print at once, so the log shows each dictation (without it nothing appeared until the buffer filled)
cat > "$APP/Contents/MacOS/indite" <<LAUNCH
#!/bin/bash
exec "$ROOT/.venv/bin/python" -u "$ROOT/mac/indite_mac.py" >> "\$HOME/Library/Logs/indite-mac.log" 2>&1
LAUNCH
chmod +x "$APP/Contents/MacOS/indite"
cp "$ROOT/mac/brand/indite.icns" "$APP/Contents/Resources/indite.icns"     # the logo (mac/brand/logo.svg)

# An ad-hoc signature gives the bundle a stable identity, so the Accessibility tick survives a rebuild.
codesign --force --sign - "$APP" 2>/dev/null || echo "note: could not sign; the tick may not survive a rebuild"
echo "built: $APP"
echo "log:   ~/Library/Logs/indite-mac.log"
