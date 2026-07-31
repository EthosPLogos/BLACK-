#!/bin/bash
# ── BLACK Service Installer ──────────────────────────────────
# Run this ONCE. After this, BLACK starts automatically.
# You will be asked for your Mac password once for Caddy.

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  Installing BLACK as a background service..."
echo ""

# ── Stop any existing instances ──────────────────────────────
launchctl unload ~/Library/LaunchAgents/com.black.backend.plist 2>/dev/null
sudo launchctl unload /Library/LaunchDaemons/com.black.caddy.plist 2>/dev/null
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "caddy run" 2>/dev/null
sleep 1

# ── Install backend service (no sudo needed) ─────────────────
echo "  [1/2] Installing backend service..."
cp "$ROOT/com.black.backend.plist" ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.black.backend.plist
echo "        Backend installed — starts on every login automatically."

# ── Install Caddy service (needs sudo for port 80/443) ───────
echo "  [2/2] Installing Caddy service (password required)..."
sudo cp "$ROOT/com.black.caddy.plist" /Library/LaunchDaemons/
sudo launchctl load /Library/LaunchDaemons/com.black.caddy.plist
echo "        Caddy installed — starts on every boot automatically."

# ── Wait for backend ─────────────────────────────────────────
echo ""
echo "  Waiting for BLACK to come online..."
for i in {1..20}; do
    if curl -s http://127.0.0.1:8001/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo "  ✓ BLACK is running as a background service."
echo ""
echo "  From now on, BLACK starts automatically."
echo "  Just open your browser to: https://black"
echo ""

open https://black
