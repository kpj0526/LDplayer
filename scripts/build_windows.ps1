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
    environment. Recognition assets are copied from templates/.
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$BuildVersion = (Get-Content -LiteralPath (Join-Path $RepoRoot 'VERSION') -Raw).Trim()
$BuildId = "$BuildVersion-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
$DistParent = Join-Path $RepoRoot "dist\test-$BuildId"
$WorkRoot = Join-Path $RepoRoot "build\test-$BuildId"
# Every build goes to a new directory. Existing release binaries/ZIPs stay intact.
if (Test-Path -LiteralPath $DistParent) { throw "Build output already exists: $DistParent" }

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "No .venv found; creating one at .venv ..."
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create build environment' }
    $Python = ".\.venv\Scripts\python.exe"
}

Write-Host "Installing project + recognition + build dependencies ..."
& $Python -X utf8 -m pip install --quiet -e ".[build,recognition]"
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }

Write-Host "Running PyInstaller ..."
& $Python -X utf8 -m PyInstaller `
    --noconfirm `
    --clean `
    --name ldmanager `
    --windowed `
    --collect-all windows_capture `
    --distpath $DistParent `
    --workpath $WorkRoot `
    --specpath $WorkRoot `
    --paths src `
    "$RepoRoot\scripts\entrypoint.py"
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed; refusing to package old output' }

$DistRoot = Join-Path $DistParent 'ldmanager'
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

# New isolated output; never deletes a prior customer's templates/configs.
Copy-Item -Recurse -Force "templates" "$DistRoot\templates"
Copy-Item -Force "VERSION" "$DistRoot\VERSION"
Copy-Item -Force "CHANGELOG.md" "$DistRoot\CHANGELOG.md"
New-Item -ItemType Directory -Force -Path "$DistRoot\docs" | Out-Null
Copy-Item -Force "docs\RUN_GUIDE.md" "$DistRoot\docs\RUN_GUIDE.md"
Copy-Item -Force "docs\REAL_CAPTURE_CHECKLIST.md" "$DistRoot\docs\REAL_CAPTURE_CHECKLIST.md"
Copy-Item -Force "docs\WINDOWS_CAPTURE_TEST.md" "$DistRoot\docs\WINDOWS_CAPTURE_TEST.md"

@'
ldmanager -- WINDOWS CAPTURE / MEMORY TEST
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
     confirm it's online.
  4. Click Refresh LD windows and select the EXACT matching window on each panel.
  5. Open the game's mission/region screen and click Test capture.
     Confirm that the ADB and Windows images show the SAME LD account.
     Only a successful Windows verification enables Start (including Start All).

If you re-run the exe later, your saved configs\config.yaml /
configs\bounty.yaml are never overwritten -- bootstrap only creates
them the first time, when they don't exist yet.

Before pressing Start, use Test capture for that account. It checks the
mission-list screen automatically and enables Start only for the verified
LD. This TEST build uses Windows Graphics Capture ONLY during operation.
It NEVER falls back to ADB screenshots: failed/stale/closed/resized capture
pauses that account until you correct the problem and run Test capture again.
One ADB screenshot per Test capture is intentional and logged separately.
Customers do not use Template calibration or enter click coordinates.

Extract into a NEW folder, separate from rc.35. Do not overwrite that release.
Memory and cumulative call logs are written every 30 seconds under
diagnostics\memory\<session>\. See docs\WINDOWS_CAPTURE_TEST.md.
'@ | Set-Content -Encoding utf8 "$DistRoot\README_FIRST_RUN.txt"

Write-Host ""
Write-Host "Build complete: $DistRoot\ldmanager.exe"
Write-Host "Packaged alongside it: configs\*.example.yaml, templates\, README_FIRST_RUN.txt"
Write-Host "The exe self-bootstraps configs\config.yaml/bounty.yaml on first run -- no manual copy needed."
