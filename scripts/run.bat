@echo off
REM Start ldmanager's GUI app (MVP-001).
REM Run from anywhere -- this script locates the repo root itself.
setlocal
cd /d "%~dp0\.."

if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe -m ldmanager.app
) else (
    echo No .venv found next to this script; falling back to 'python' on PATH.
    python -m ldmanager.app
)

endlocal
