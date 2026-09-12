<#
    Build a standalone Windows executable for ldmanager using PyInstaller
    (MVP-001 / REL-0.1.0-PKG-01).

    Usage (from repo root or anywhere):
        powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1

    Produces dist\ldmanager\ldmanager.exe (a "onedir" build -- more
    reliable for a Tkinter app than --onefile, and much faster to
    rebuild during development), PLUS a sibling configs\ folder
    (config.example.yaml + bounty.example.yaml only -- never a real,
    filled-in config) and a copy of templates\, so the dist\ldmanager\
    folder is self-contained and ZIP-ready: a customer who extracts the
    ZIP and double-clicks ldmanager.exe gets a working GUI on first
    launch. The exe itself auto-bootstraps configs\config.yaml/
    configs\bounty.yaml from those examples on first run (see
    src\ldmanager\bootstrap.py) -- it never overwrites an existing,
    already-registered config.

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

$DistRoot = "dist\ldmanager"
if (-not (Test-Path $DistRoot)) {
    throw "PyInstaller did not produce $DistRoot -- aborting before packaging step."
}

Write-Host "Packaging safe default configs + templates into $DistRoot ..."

# Only the *.example.yaml templates -- never a real, filled-in config.
# All ADB mappings in these examples are null; neither file contains
# any credential (both are covered by tests/test_config.py's and
# tests/test_bounty_config.py's sensitive-key rejection tests).
New-Item -ItemType Directory -Force -Path "$DistRoot\configs" | Out-Null
Copy-Item -Force "configs\config.example.yaml" "$DistRoot\configs\config.example.yaml"
Copy-Item -Force "configs\bounty.example.yaml" "$DistRoot\configs\bounty.example.yaml"

# Placeholder templates folder (see templates/README.md -- no real
# recognition assets are shipped).
if (Test-Path "$DistRoot\templates") {
    Remove-Item -Recurse -Force "$DistRoot\templates"
}
Copy-Item -Recurse -Force "templates" "$DistRoot\templates"

@'
ldmanager -- first run
=======================

Just run ldmanager.exe (double-click it, or from a shell in this same
folder). On first launch it automatically creates:

    configs\config.yaml
    configs\bounty.yaml

from the configs\*.example.yaml files sitting next to it -- with every
ADB mapping left blank (null) and no credentials of any kind. You do
NOT need to edit any file or use a terminal before starting the app.

Once the GUI window opens:
  1. Start your LDPlayer instances.
  2. Click "Refresh ADB devices" at the top of the window.
  3. On each LD1..LD9 panel, pick (or type) the ADB serial for that
     instance and click "Save". Click "Refresh ADB devices" again to
     confirm it's online -- only then does that panel's Start button
     enable.

If you re-run the exe later, your saved configs\config.yaml /
configs\bounty.yaml are never overwritten -- bootstrap only creates
them the first time, when they don't exist yet.

This build has not been verified against a real game/LDPlayer screen;
recognition is a safe placeholder that never claims a match until a
real recognizer is implemented. See the project's
docs\REAL_CAPTURE_CHECKLIST.md and docs\MVP_UNVERIFIED.md if included,
or the project repository, for details.
'@ | Set-Content -Encoding utf8 "$DistRoot\README_FIRST_RUN.txt"

Write-Host ""
Write-Host "Build complete: $DistRoot\ldmanager.exe"
Write-Host "Packaged alongside it: configs\*.example.yaml, templates\, README_FIRST_RUN.txt"
Write-Host "The exe self-bootstraps configs\config.yaml/bounty.yaml on first run -- no manual copy needed."
