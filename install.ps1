<#
.SYNOPSIS
NAQ - One-Line Installer for Windows
Usage: irm https://raw.githubusercontent.com/harrison007123/naq/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$REPO = "https://github.com/harrison007123/naq"
$ZIP_URL = "${REPO}/archive/refs/heads/main.zip"

function error([string]$msg) { 
    Write-Host "  ✗ ERROR: " -ForegroundColor Red -NoNewline
    Write-Host $msg
    exit 1 
}

# 1. Check Python
$PythonCmd = ""
foreach ($cmd in @("python", "python3")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $version = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        try {
            $major, $minor = $version.Split('.')
            if ([int]$major -ge 3 -and [int]$minor -ge 9) {
                $PythonCmd = $cmd
                break
            }
        }
        catch { }
    }
}

if (-not $PythonCmd) {
    error "Python 3.9+ is required but not found.`n  Install it from https://www.python.org/downloads/"
}

# 2. Check & Update pip silently
$pipCheck = & $PythonCmd -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    & $PythonCmd -m ensurepip --upgrade 2>&1 | Out-Null
}
& $PythonCmd -m pip install --upgrade pip --quiet 2>&1 | Out-Null

# 3. Install NAQ
# Using .zip URL directly avoids requiring `git` to be installed on Windows
& $PythonCmd -m pip install --user --upgrade $ZIP_URL --quiet 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    error "Installation failed. Please check your network connection and try again."
}

# 4. Verify Path
$qmCmd = Get-Command "naq" -ErrorAction SilentlyContinue
if (-not $qmCmd) {
    $UserBin = & $PythonCmd -m site --user-site
    $ScriptsBin = (Split-Path $UserBin -Parent) + "\Scripts"
    Write-Host "  ⚠ naq is installed but may not be on your PATH." -ForegroundColor Yellow
    Write-Host "  Ensure the following directory is in your System PATH:"
    Write-Host "      $ScriptsBin"
}

# Done
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓  NAQ installed successfully!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Run 'naq' in your terminal to get started." -ForegroundColor Cyan
Write-Host ""
