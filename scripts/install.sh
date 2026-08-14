#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# Velvet Browser — installer
# Detects OS and installs PyQt5 + Chromium automatically
# Usage: bash scripts/install.sh
# ─────────────────────────────────────────────────────────
set -e

RED='\033[0;31m'; PINK='\033[0;35m'; NC='\033[0m'; GREEN='\033[0;32m'

echo -e "${PINK}"
echo "  ♥  Velvet Browser Installer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${NC}"

OS="$(uname -s 2>/dev/null || echo Windows)"

install_linux_apt() {
    echo -e "${GREEN}[apt] Detected Debian/Ubuntu${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtsvg \
        chromium-browser 2>/dev/null \
        || sudo apt-get install -y python3-pyqt5 python3-pyqt5.qtsvg chromium
}

install_linux_dnf() {
    echo -e "${GREEN}[dnf] Detected Fedora/RHEL${NC}"
    sudo dnf install -y python3-qt5 chromium
}

install_linux_pacman() {
    echo -e "${GREEN}[pacman] Detected Arch${NC}"
    sudo pacman -S --noconfirm python-pyqt5 chromium
}

install_macos() {
    echo -e "${GREEN}[brew] Detected macOS${NC}"
    if ! command -v brew &>/dev/null; then
        echo "Homebrew not found. Install from https://brew.sh"
        exit 1
    fi
    brew install pyqt@5 --quiet
    brew install --cask chromium --quiet 2>/dev/null \
        || brew install --cask google-chrome --quiet
}

install_pip_fallback() {
    echo -e "${GREEN}[pip] Falling back to pip install${NC}"
    pip3 install PyQt5 --break-system-packages 2>/dev/null \
        || pip3 install PyQt5
}

case "$OS" in
    Linux)
        if command -v apt-get &>/dev/null;  then install_linux_apt
        elif command -v dnf    &>/dev/null; then install_linux_dnf
        elif command -v pacman &>/dev/null; then install_linux_pacman
        else install_pip_fallback
        fi
        ;;
    Darwin)
        install_macos
        ;;
    *)
        echo "Windows detected — run:  pip install PyQt5"
        echo "Then ensure Chrome is installed at the default path."
        ;;
esac

echo ""
echo -e "${PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓ Install done.${NC}"
echo ""
echo "  Launch:  python main.py"
echo ""
