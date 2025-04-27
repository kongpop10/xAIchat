@echo off
echo Starting Grok Chat...
cd /d "%~dp0"

REM Set environment encoding
set PYTHONIOENCODING=utf-8

REM Check if environment variables are set
if not defined XAI_API_KEY (
    echo WARNING: XAI_API_KEY environment variable is not set.
    echo You may need to set this for the application to work properly.
    echo.
    timeout /t 3 >nul
)

REM Launch the Streamlit application
echo Launching Grok Chat application...
streamlit run app.py

REM If Streamlit fails to start, provide helpful message
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: Failed to start Grok Chat.
    echo.
    echo Please check that:
    echo 1. Streamlit is installed (pip install streamlit)
    echo 2. All dependencies are installed (pip install -r requirements.txt)
    echo 3. Your environment variables are set correctly
    echo.
    pause
)
