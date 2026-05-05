@echo off
title YouTube Downloader Setup

echo ================================
echo Installing required components
echo ================================

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Downloading Python...

    powershell -Command "Invoke-WebRequest https://www.python.org/ftp/python/3.12.8/python-3.12.8-amd64.exe -OutFile python_installer.exe"

    echo Installing Python...
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1 Include_tcltk=1

    echo Python installed.
    del python_installer.exe
) else (
    echo Python already installed.
)

:: Refresh PATH (important for same session)
set PATH=%PATH%;C:\Program Files\Python312\;C:\Program Files\Python312\Scripts\

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing yt-dlp...
python -m pip install yt-dlp

echo.
echo Installing FFmpeg...
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements

echo.
echo ================================
echo Setup completed
echo ================================

echo.
echo Starting application...
echo ================================

:: Run your GUI app
python y2b_modified.py

pause