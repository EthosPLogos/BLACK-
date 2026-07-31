#!/bin/bash
# ── BLACK Launcher ───────────────────────────────────────────
# Double-click to start BLACK. Keep this window open while using it.

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "  ██████╗ ██╗      █████╗  ██████╗██╗  ██╗"
echo "  ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝"
echo "  ██████╔╝██║     ███████║██║     █████╔╝ "
echo "  ██╔══██╗██║     ██╔══██║██║     ██╔═██╗ "
echo "  ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗"
echo "  ╚═════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝"
echo ""

# ── Kill old processes ───────────────────────────────────────
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 1

# ── Ollama ───────────────────────────────────────────────────
echo "  [1/3] Starting Ollama..."
if ! pgrep -x "ollama" > /dev/null 2>&1; then
    ollama serve >> /tmp/black_ollama.log 2>&1 &
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done
    echo "        Ollama started."
else
    echo "        Ollama already running."
fi

# ── Backend ──────────────────────────────────────────────────
echo "  [2/3] Starting backend..."
cd "$ROOT/backend"
"$ROOT/backend/.venv/bin/uvicorn" app.main:app \
    --host 0.0.0.0 --port 8001 \
    >> /tmp/black_backend.log 2>&1 &

# ── Frontend ─────────────────────────────────────────────────
echo "  [3/3] Starting frontend..."
cd "$ROOT/frontend"
npm run dev -- --host >> /tmp/black_frontend.log 2>&1 &

# ── Wait for backend ─────────────────────────────────────────
echo ""
echo "  Waiting for BLACK..."
for i in {1..20}; do
    if curl -s http://127.0.0.1:8001/api/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo ""
echo "  ✓ BLACK is online"
echo ""
echo "  Mac:   http://localhost:5173"
echo "  Phone: http://$(ipconfig getifaddr en0 2>/dev/null || echo "172.20.33.0"):5173"
echo ""
echo "  Keep this window open. Close it to shut down."
echo ""

open "http://localhost:5173"

wait
