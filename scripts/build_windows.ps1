<#
    Build a standalone Windows executable for ldmanager using PyInstaller
    (MVP-001).

    Usage (from repo root or anywhere):
        powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1

    Produces dist\ldmanager\ldmanager.exe (a "onedir" build -- more
    reliable for a Tkinter app than --onefile, and much faster to
    rebuild during development).

    This script only builds the executable; it does not verify the
    executable against a real end-user Windows machine outside this dev
    environment, and it does not bundle any real recognition templates
    (see templates/README.md and docs/REAL_CAPTURE_CHECKLIST.md).
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "No .venv found; creating one at .venv ..."
    python -m venv .venv
    $Python = ".\.venv\Scripts\python.exe"
}

Write-Host "Installing project + build dependencies (pip, ldmanager, pyinstaller) ..."
& $Python -m pip install --quiet --upgrade pip
& $Python -m pip install --quiet -e ".[build]"

Write-Host "Running PyInstaller ..."
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --name ldmanager `
    --windowed `
    --paths src `
    scripts\entrypoint.py

Write-Host ""
Write-Host "Build complete: dist\ldmanager\ldmanager.exe"
Write-Host "Copy configs\config.example.yaml/mission.example.yaml next to the exe"
Write-Host "(as configs\config.yaml / configs\mission.yaml) and fill them in before running."
