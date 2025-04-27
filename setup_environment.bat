@echo off
echo Grok Chat Environment Setup
echo ==========================
echo.
echo This script will help you set up the required environment variables for Grok Chat.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: This script is not running as administrator.
    echo Environment variables will only be set for the current user session.
    echo For permanent changes, run this script as administrator.
    echo.
    pause
)

echo Setting up environment variables for Grok Chat...
echo.

REM XAI API Key
set /p XAI_API_KEY="Enter your xAI API key: "
if "%XAI_API_KEY%"=="" (
    echo XAI API key cannot be empty. Skipping...
) else (
    setx XAI_API_KEY "%XAI_API_KEY%"
    echo XAI API key set successfully.
)

echo.

REM Brave Search API Key (optional)
set /p BRAVE_API_KEY="Enter your Brave Search API key (optional, press Enter to skip): "
if not "%BRAVE_API_KEY%"=="" (
    setx BRAVE_API_KEY "%BRAVE_API_KEY%"
    echo Brave Search API key set successfully.
) else (
    echo Brave Search API key not set.
)

echo.
echo Environment setup complete!
echo You can now run Grok Chat using the Start Menu shortcut or by running launch_grok_chat.bat
echo.
pause
