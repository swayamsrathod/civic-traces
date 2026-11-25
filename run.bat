@echo off
REM One-click start for Windows: installs, loads demo data, opens the dashboard.
cd /d "%~dp0"
echo Installing dependencies (first run takes a few minutes)...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
  echo.
  echo Install failed. Check that Python 3.10 or newer is installed: python --version
  pause
  exit /b 1
)
if not exist civictrace.db (
  echo Loading demo complaints...
  python -m scripts.seed_demo
)
echo.
echo CIVIC TRACE starting at http://localhost:8000/report  (keep this window open)
start "" http://localhost:8000/report
python -m uvicorn backend.main:app
pause
