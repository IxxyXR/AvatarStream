@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Virtualenv not found at .venv\Scripts\python.exe
  echo Create it first with: python -m venv .venv
  pause
  exit /b 1
)

set "LOG_FILE=logs\holistic_tracker.log"
echo Logging to %LOG_FILE%
call ".venv\Scripts\python.exe" "game\AvatarStream\scripts\python\holistic_tracker.py" --pick-camera --debug --no-virtual-cam --listen-http --listen-host 127.0.0.1 --listen-port 40094 --listen-path /pose --transport none --log-file "%LOG_FILE%"
