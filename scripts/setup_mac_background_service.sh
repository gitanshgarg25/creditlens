#!/bin/bash
# CreditLens 24/7 Always-On Service Installer for macOS
# Registers CreditLens with macOS launchd so it runs automatically in background on boot and auto-restarts if closed.

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.creditlens.streamlit.plist"

mkdir -p "$PLIST_DIR"
mkdir -p "$BASE_DIR/reports"

# Unload previous service if already installed
launchctl unload "$PLIST_FILE" 2>/dev/null || true

cat <<EOF > "$PLIST_FILE"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.creditlens.streamlit</string>
    <key>ProgramArguments</key>
    <array>
        <string>$BASE_DIR/.venv/bin/streamlit</string>
        <string>run</string>
        <string>$BASE_DIR/app/streamlit_app.py</string>
        <string>--server.port=8501</string>
        <string>--server.headless=true</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>$BASE_DIR</string>
    <key>StandardOutPath</key>
    <string>$BASE_DIR/reports/creditlens_service.log</string>
    <key>StandardErrorPath</key>
    <string>$BASE_DIR/reports/creditlens_service.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_FILE"

echo "✅ CreditLens 24/7 background service installed!"
echo "The app will now always be running automatically at http://localhost:8501 even after rebooting your Mac."
echo "To uninstall later, run: launchctl unload $PLIST_FILE && rm $PLIST_FILE"
