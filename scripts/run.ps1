<#
    Start ldmanager's GUI app (MVP-001).
    Usage: powershell -ExecutionPolicy Bypass -File scripts\run.ps1
#>

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Host "No .venv found next to this script; falling back to 'python' on PATH."
    $Python = "python"
}

& $Python -m ldmanager.app
