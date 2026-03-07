<#
.SYNOPSIS
QueryMind 3 - One-Line Installer for Windows
Usage: irm https://raw.githubusercontent.com/harrison007123/querymind3/main/install.ps1 | iex
#>

$ErrorActionPreference = "Stop"

$REPO = "https://github.com/harrison007123/querymind3"
$PACKAGE = "querymind3"

# ── Colors ────────────────────────────────────────────────────────
function info([string]$msg)    { Write-Host "[$PACKAGE] " -ForegroundColor Cyan -NoNewline; Write-Host $msg }
function success([string]$msg) { Write-Host "  ✓ " -ForegroundColor Green -NoNewline; Write-Host $msg }
function warn([string]$msg)    { Write-Host "  ⚠ " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function error([string]$msg)   { Write-Host "  ✗ ERROR: " -ForegroundColor Red -NoNewline; Write-Host $msg; exit 1 }

# ── Banner ────────────────────────────────────────────────────────
Write-Host ""
Write-Host " ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗███╗   ███╗██╗███╗   ██╗██████╗" -ForegroundColor Cyan
Write-Host "██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝████╗ ████║██║████╗  ██║██╔══██╗" -ForegroundColor Cyan
Write-Host "██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ ██╔████╔██║██║██╔██╗ ██║██║  ██║" -ForegroundColor Cyan
Write-Host "██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║" -ForegroundColor Cyan
Write-Host "╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║   ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝" -ForegroundColor Cyan
Write-Host " ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  QueryMind 3 Installer (Windows)" -ForegroundColor White
Write-Host "  AI Natural Language -> SQL Engine"
Write-Host ""

# ── Step 1: Check Python ──────────────────────────────────────────
info "Checking Python version..."
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
        } catch { }
    }
}

if (-not $PythonCmd) {
    error "Python 3.9+ is required but not found.`n  Install it from https://www.python.org/downloads/"
}

$FullVersion = & $PythonCmd --version
success "$FullVersion detected."

# ── Step 2: Check pip ─────────────────────────────────────────────
info "Checking pip..."
$pipCheck = & $PythonCmd -m pip --version 2>&1
if ($LASTEXITCODE -ne 0) {
    warn "pip not found. Attempting to bootstrap..."
    & $PythonCmd -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { error "Could not bootstrap pip." }
}
success "pip is available."

# ── Step 3: Upgrade pip ───────────────────────────────────────────
info "Upgrading pip..."
& $PythonCmd -m pip install --upgrade pip --quiet
success "pip upgraded."

# ── Step 4: Install QueryMind 3 ───────────────────────────────────
info "Installing QueryMind 3 from GitHub..."
& $PythonCmd -m pip install --upgrade "git+${REPO}.git" --quiet
if ($LASTEXITCODE -ne 0) {
    error "Installation failed. Please check your network connection and try again."
}
success "Installed ${PACKAGE}."

# ── Step 5: Verify the command ────────────────────────────────────
info "Verifying installation..."
$qmCmd = Get-Command "querymind" -ErrorAction SilentlyContinue

if (-not $qmCmd) {
    warn "querymind is installed but may not be on your PATH."
    $UserBin = & $PythonCmd -m site --user-site
    $ScriptsBin = (Split-Path $UserBin -Parent) + "\Scripts"
    warn "Ensure the following directory is in your System PATH:"
    Write-Host "    $ScriptsBin"
} else {
    $ver = & querymind --version 2>$null
    success "querymind is ready. ($ver)"
}

# ── Done ──────────────────────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓  QueryMind 3 installed successfully!" -ForegroundColor Green
Write-Host "══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "  Run 'querymind' in your terminal to get started." -ForegroundColor Cyan
Write-Host ""
