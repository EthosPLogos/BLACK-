#!/bin/bash
# ── Mr. Black Kill Switch ────────────────────────────────────
# "Chibuike kill Mr. Black"
# Double-click or run from terminal to shut down all Mr. Black services.

echo ""
echo "  ██╗  ██╗██╗██╗     ██╗         ███████╗██╗    ██╗██╗████████╗ ██████╗██╗  ██╗"
echo "  ██║ ██╔╝██║██║     ██║         ██╔════╝██║    ██║██║╚══██╔══╝██╔════╝██║  ██║"
echo "  █████╔╝ ██║██║     ██║         ███████╗██║ █╗ ██║██║   ██║   ██║     ███████║"
echo "  ██╔═██╗ ██║██║     ██║         ╚════██║██║███╗██║██║   ██║   ██║     ██╔══██║"
echo "  ██║  ██╗██║███████╗███████╗    ███████║╚███╔███╔╝██║   ██║   ╚██████╗██║  ██║"
echo "  ╚═╝  ╚═╝╚═╝╚══════╝╚══════╝   ╚══════╝ ╚══╝╚══╝ ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝"
echo ""
echo "  Chibuike kill Mr. Black — executing..."
echo ""

# ── Frontend (Vite) ──────────────────────────────────────────
echo "  [1/3] Stopping frontend..."
pkill -f "vite" 2>/dev/null && echo "        Frontend stopped." || echo "        Frontend was not running."

# ── Backend (uvicorn) ────────────────────────────────────────
echo "  [2/3] Stopping backend..."
pkill -f "uvicorn app.main" 2>/dev/null && echo "        Backend stopped." || echo "        Backend was not running."

# ── Ollama ───────────────────────────────────────────────────
echo "  [3/3] Stopping Ollama..."
pkill -x "ollama" 2>/dev/null && echo "        Ollama stopped." || echo "        Ollama was not running."

echo ""
echo "  Mr. Black is offline. All services terminated."
echo ""
