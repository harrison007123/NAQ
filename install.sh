#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  QueryMind 3 — One-Line Installer
#  Usage: curl -sSL https://querymind.dev/install.sh | bash
# ─────────────────────────────────────────────────────────────────

set -euo pipefail

REPO="https://github.com/harrison007123/querymind3"
PACKAGE="querymind3"
MIN_PYTHON="3.9"

# ── Colors ────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

info()    { echo -e "${CYAN}${BOLD}[QueryMind]${RESET} $*"; }
success() { echo -e "${GREEN}${BOLD}  ✓${RESET} $*"; }
warn()    { echo -e "${YELLOW}${BOLD}  ⚠${RESET} $*"; }
error()   { echo -e "${RED}${BOLD}  ✗ ERROR:${RESET} $*" >&2; exit 1; }

# ── Banner ────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}${BOLD}"
cat <<'EOF'
 ██████╗ ██╗   ██╗███████╗██████╗ ██╗   ██╗███╗   ███╗██╗███╗   ██╗██████╗
██╔═══██╗██║   ██║██╔════╝██╔══██╗╚██╗ ██╔╝████╗ ████║██║████╗  ██║██╔══██╗
██║   ██║██║   ██║█████╗  ██████╔╝ ╚████╔╝ ██╔████╔██║██║██╔██╗ ██║██║  ██║
██║▄▄ ██║██║   ██║██╔══╝  ██╔══██╗  ╚██╔╝  ██║╚██╔╝██║██║██║╚██╗██║██║  ██║
╚██████╔╝╚██████╔╝███████╗██║  ██║   ██║   ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝
 ╚══▀▀═╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝
EOF
echo -e "${RESET}"
echo -e "${BOLD}  QueryMind 3 Installer${RESET}"
echo -e "  AI Natural Language → SQL Engine"
echo ""

# ── Step 1: Check Python ──────────────────────────────────────────
info "Checking Python version..."

PYTHON_CMD=""
for cmd in python3 python python3.12 python3.11 python3.10 python3.9; do
  if command -v "$cmd" &>/dev/null; then
    version=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
    major=$(echo "$version" | cut -d. -f1)
    minor=$(echo "$version" | cut -d. -f2)
    if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
      PYTHON_CMD="$cmd"
      break
    fi
  fi
done

if [ -z "$PYTHON_CMD" ]; then
  error "Python ${MIN_PYTHON}+ is required but not found.\n  Install it from https://www.python.org/downloads/"
fi
success "Python $("$PYTHON_CMD" --version) detected."

# ── Step 2: Check / install pip ───────────────────────────────────
info "Checking pip..."
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
  warn "pip not found. Attempting to bootstrap..."
  "$PYTHON_CMD" -m ensurepip --upgrade || error "Could not bootstrap pip."
fi
success "pip is available."

# ── Step 3: Upgrade pip silently ──────────────────────────────────
info "Upgrading pip..."
"$PYTHON_CMD" -m pip install --upgrade pip --quiet
success "pip upgraded."

# ── Step 4: Install QueryMind 3 ───────────────────────────────────
info "Installing QueryMind 3..."

# Try PyPI first; fall back to GitHub if not yet published
if "$PYTHON_CMD" -m pip install --upgrade "${PACKAGE}" --quiet 2>/dev/null; then
  success "Installed ${PACKAGE} from PyPI."
else
  warn "Package not found on PyPI. Installing directly from GitHub..."
  "$PYTHON_CMD" -m pip install --upgrade "git+${REPO}.git" --quiet \
    || error "Installation failed. Please check your network connection and try again."
  success "Installed ${PACKAGE} from GitHub."
fi

# ── Step 5: Verify the command ────────────────────────────────────
info "Verifying installation..."

# Try to find the querymind command
if command -v querymind &>/dev/null; then
  QM_BIN="querymind"
else
  # Check common user-local bin paths
  USER_BIN="$("$PYTHON_CMD" -m site --user-base)/bin"
  if [ -f "${USER_BIN}/querymind" ]; then
    QM_BIN="${USER_BIN}/querymind"
    warn "querymind is installed at ${USER_BIN} which may not be on your PATH."
    warn "Add the following to your shell profile:"
    echo ""
    echo "    export PATH=\"${USER_BIN}:\$PATH\""
    echo ""
  else
    error "querymind command not found after installation."
  fi
fi

VERSION=$("$QM_BIN" --version 2>/dev/null || echo "unknown")
success "querymind ${VERSION} is ready."

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✓  QueryMind 3 installed successfully!${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Run ${CYAN}${BOLD}querymind${RESET} to get started."
echo -e "  Documentation: ${CYAN}${REPO}#readme${RESET}"
echo ""
