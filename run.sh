#!/usr/bin/env bash
# ==============================================================
# run.sh — Mini ChatGPT
# Supports: macOS 12+, Ubuntu 20.04+, Debian-based Linux
# Usage:
#   chmod +x run.sh   (only needed once)
#   ./run.sh
# ==============================================================

set -euo pipefail

# ── Colour codes ───────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

echo ""
echo -e "${CYAN}${BOLD} =========================================="
echo -e "  Mini ChatGPT — Local LLM Chat Interface"
echo -e "  Auto-Launcher v1.0"
echo -e " ==========================================${RESET}"
echo ""

# ── STEP 1: Locate Python 3.9+ ────────────────────────────────
echo -e "${BOLD}[1/5] Checking for Python 3...${RESET}"

PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VERSION=$("$cmd" --version 2>&1 | awk '{print $2}')
        MAJOR=$(echo "$VERSION" | cut -d. -f1)
        MINOR=$(echo "$VERSION" | cut -d. -f2)
        if [[ "$MAJOR" -eq 3 && "$MINOR" -ge 9 ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    echo ""
    echo -e "${RED}[ERROR] Python 3.9 or newer was not found on your system.${RESET}"
    echo ""
    echo "  macOS   → https://www.python.org/downloads/macos/"
    echo "            (or via Homebrew: brew install python@3.11)"
    echo "  Linux   → sudo apt update && sudo apt install python3.11"
    echo ""
    exit 1
fi

echo -e "${GREEN}[OK] Found $($PYTHON_CMD --version)${RESET}"
echo ""

# ── STEP 2: Check pip ─────────────────────────────────────────
echo -e "${BOLD}[2/5] Checking for pip...${RESET}"

if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
    echo -e "${RED}[ERROR] pip is not available for $PYTHON_CMD.${RESET}"
    echo "  Try: sudo apt install python3-pip"
    exit 1
fi

echo -e "${GREEN}[OK] pip is available.${RESET}"
echo ""

# ── STEP 3: Install dependencies ──────────────────────────────
echo -e "${BOLD}[3/5] Installing / verifying Python dependencies...${RESET}"
echo -e "${YELLOW}      (First run may take a minute)${RESET}"
echo ""

"$PYTHON_CMD" -m pip install --quiet --upgrade pip
"$PYTHON_CMD" -m pip install --quiet -r requirements.txt

echo -e "${GREEN}[OK] All Python dependencies are ready.${RESET}"
echo ""

# ── STEP 4: Check Ollama server ───────────────────────────────
# We probe the Ollama REST API on its default port.
# curl's --max-time prevents hanging if the port is firewalled.
echo -e "${BOLD}[4/5] Checking Ollama server (localhost:11434)...${RESET}"

OLLAMA_OK=0
if command -v curl &>/dev/null; then
    if curl -s --max-time 3 http://localhost:11434 &>/dev/null; then
        OLLAMA_OK=1
    fi
elif command -v wget &>/dev/null; then
    if wget -q --timeout=3 -O /dev/null http://localhost:11434 &>/dev/null; then
        OLLAMA_OK=1
    fi
fi

if [[ "$OLLAMA_OK" -eq 0 ]]; then
    echo ""
    echo -e "${YELLOW}[WARNING] The Ollama server does not appear to be running.${RESET}"
    echo ""
    echo "  Mini ChatGPT requires Ollama to serve the local language model."
    echo ""
    echo "  To fix this:"
    echo "    1. Install Ollama from: https://ollama.com/download"
    echo "    2. In a NEW terminal, run: ollama serve"
    echo "    3. Pull a model if needed: ollama pull llama3"
    echo "    4. Re-run this script."
    echo ""
    echo -n "  Continue anyway? [y/N]: "
    read -r CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Exiting."
        exit 1
    fi
else
    echo -e "${GREEN}[OK] Ollama is reachable at localhost:11434.${RESET}"
fi
echo ""

# ── STEP 5: Launch the Streamlit app ──────────────────────────
echo -e "${BOLD}[5/5] Launching Mini ChatGPT...${RESET}"
echo ""
echo "  The app will open in your default browser automatically."
echo "  If it does not, navigate to:"
echo -e "  ${CYAN}→ http://localhost:8501${RESET}"
echo ""
echo "  Press Ctrl+C in this terminal to stop the server."
echo -e "${BOLD} ==========================================${RESET}"
echo ""

"$PYTHON_CMD" -m streamlit run chatbot.py \
    --server.headless false \
    --server.port 8501 \
    --browser.gatherUsageStats false

echo ""
echo "Mini ChatGPT stopped. Goodbye!"
