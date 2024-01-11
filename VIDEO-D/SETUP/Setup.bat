@echo off

REM Check if the script is running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo This script requires administrative privileges.
    echo Please run this script as an administrator.
    pause
    exit /b
)

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed on this system.
    echo Please download and install Python from https://www.python.org/downloads/
    pause
    exit /b
)

REM Installing required Python packages
echo Installing required Python packages...
python -m pip install spotdl pytube validators

REM Check if installation was successful
python -c "import spotdl, pytube, validators" > nul 2>&1
cls
if %errorlevel% neq 0 (
    echo There was an issue installing required packages.
    pause
    exit /b
)

REM Set the download directory to the current folder
set "download_dir=%~dp0"

REM Download FFmpeg using PowerShell with the default progress bar
echo Downloading FFmpeg...
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z' -OutFile '%download_dir%ffmpeg.7z'}"

REM Unzip FFmpeg
echo Extracting FFmpeg...
"%ProgramFiles%\7-Zip\7z.exe" x "%download_dir%ffmpeg.7z" -o"%download_dir%VIDEO-D\FFMPEG" -y

REM Final message
echo Download complete zip folder. Follow the remaining steps for setup.
echo.
timeout /t 5 >nul
exit /b