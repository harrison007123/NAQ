#!/usr/bin/env bash
# Usage: curl -sSL https://raw.githubusercontent.com/harrison007123/naq/main/install.sh | bash

set -euo pipefail

REPO="https://github.com/harrison007123/naq"
PACKAGE_URL="${REPO}/archive/refs/heads/main.zip"
MIN_PYTHON="3.9"

# ── Colors ────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
RESET='\033[0m'

error() { echo -e "${RED}${BOLD}  ✗ ERROR:${RESET} $*" >&2; exit 1; }
warn()  { echo -e "${YELLOW}${BOLD}  ⚠${RESET} $*"; }

# ── 1. Check Python ───────────────────────────────────────────────
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
  error "Python ${MIN_PYTHON}+ is required.\n  Install it from https://www.python.org/downloads/"
fi

# ── 2. Check & Update pip silently ────────────────────────────────
if ! "$PYTHON_CMD" -m pip --version &>/dev/null; then
  "$PYTHON_CMD" -m ensurepip --upgrade >/dev/null 2>&1 || true
fi
"$PYTHON_CMD" -m pip install --upgrade pip --quiet >/dev/null 2>&1 || true

# ── 3. Install NAQ ──────────────────────────────────────────────
# Try standard user install first
if ! "$PYTHON_CMD" -m pip install --user --upgrade "${PACKAGE_URL}" --quiet >/dev/null 2>&1; then
  # Fallback for Ubuntu 23.04+ / Debian 12+ (PEP 668 Externally Managed)
  if ! "$PYTHON_CMD" -m pip install --user --upgrade "${PACKAGE_URL}" --break-system-packages --quiet >/dev/null 2>&1; then
    error "Installation failed.\n  Try manually: ${PYTHON_CMD} -m pip install ${PACKAGE_URL}"
  fi
fi

# ── 4. Verify Path ────────────────────────────────────────────────
if ! command -v naq &>/dev/null; then
  USER_BIN="$("$PYTHON_CMD" -m site --user-base)/bin"
  if [ -f "${USER_BIN}/naq" ]; then
    warn "naq is installed at ${USER_BIN} which may not be on your PATH."
    warn "Add the following to your shell profile:"
    echo "    export PATH=\"${USER_BIN}:\$PATH\""
  else
    # Some distros use ~/.local/bin directly
    if [ -f "$HOME/.local/bin/naq" ]; then
      warn "naq is installed at $HOME/.local/bin which may not be on your PATH."
      warn "Add the following to your shell profile:"
      echo "    export PATH=\"$HOME/.local/bin:\$PATH\""
    fi
  fi
fi

# ── Done ──────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo -e "${GREEN}${BOLD}  ✓  NAQ installed successfully!${RESET}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════════${RESET}"
echo ""
echo -e "  Run ${CYAN}${BOLD}naq${RESET} in your terminal to get started."
echo ""
