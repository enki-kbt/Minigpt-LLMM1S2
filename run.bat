@echo off
:: ============================================================
:: run.bat — Mini ChatGPT
:: Supports: Windows 10 / 11
:: Usage: Double-click this file, or run it from a terminal.
:: ============================================================

title Mini ChatGPT — Launcher
color 0B

echo.
echo  ==========================================
echo   Mini ChatGPT — Local LLM Chat Interface
echo   Auto-Launcher v1.0
echo  ==========================================
echo.

:: ── STEP 1: Check Python is installed ───────────────────────
echo  [1/5] Checking for Python...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Python was not found on your system.
    echo.
    echo  Please install Python 3.9 or newer from:
    echo  --^> https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: During installation, check the box that says
    echo  "Add Python to PATH" before clicking Install Now.
    echo.
    echo  After installing, close this window and run this
    echo  script again.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo  [OK] Found %PYTHON_VERSION%
echo.

:: ── STEP 2: Check pip is available ──────────────────────────
echo  [2/5] Checking for pip...

python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] pip is not available. Try reinstalling Python
    echo  from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo  [OK] pip is available.
echo.

:: ── STEP 3: Install / verify Python dependencies ────────────
echo  [3/5] Installing / verifying Python dependencies...
echo  (This may take a moment on first run)
echo.

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo  [ERROR] Dependency installation failed.
    echo  Check your internet connection and try again.
    echo.
    pause
    exit /b 1
)
echo  [OK] Python dependencies are ready.
echo.

:: ── STEP 4: Check Ollama is running ─────────────────────────
:: Mini ChatGPT requires the Ollama daemon to be running locally
:: on port 11434. We perform a lightweight HTTP check using curl,
:: which is bundled with Windows 10/11.
echo  [4/5] Checking Ollama server (localhost:11434)...

curl -s --max-time 3 http://localhost:11434 >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  [WARNING] The Ollama server does not appear to be running.
    echo.
    echo  Mini ChatGPT requires Ollama to serve the local language model.
    echo.
    echo  To fix this:
    echo  1. Download and install Ollama from: https://ollama.com/download
    echo  2. Open a NEW terminal window and run: ollama serve
    echo  3. Pull a model if you haven't already, e.g.: ollama pull llama3
    echo  4. Then run this script again.
    echo.
    echo  Alternatively, start Ollama from the system tray if it is
    echo  already installed.
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        exit /b 1
    )
)
echo  [OK] Ollama is reachable.
echo.

:: ── STEP 5: Launch the Streamlit app ────────────────────────
echo  [5/5] Launching Mini ChatGPT...
echo.
echo  The app will open in your default browser automatically.
echo  If it does not, open your browser and go to:
echo  --^> http://localhost:8501
echo.
echo  To stop the app, close this window or press Ctrl+C here.
echo  ==========================================
echo.

python -m streamlit run chatbot.py ^
    --server.headless false ^
    --server.port 8501 ^
    --browser.gatherUsageStats false

echo.
echo  ChatGPT stopped. Press any key to close this window.
pause >nul
