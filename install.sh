#!/usr/bin/env bash

# ===================================================================
# Project Name : NetRecon - Automated Kali Linux Installer
# Author       : Syed Hoque
# GitHub       : https://github.com/Syedhoque/netrecon.git
# ===================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Output Color Definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Starting NetRecon installation for Kali Linux...${NC}"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Please run this script with root privileges (sudo).${NC}"
  echo -e "    Command: sudo bash install.sh"
  exit 1
fi

INSTALL_DIR="/opt/netrecon"
BIN_DIR="/usr/local/bin"
REPO_URL="https://github.com/Syedhoque/netrecon.git"

echo -e "${BLUE}[*] Updating system package index and installing dependencies...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

# Setup installation directory (supports both local git clone and curl execution)
if [ ! -d "$INSTALL_DIR" ]; then
    echo -e "${BLUE}[*] Cloning and copying tool files to ${INSTALL_DIR}...${NC}"
    if [ -f "netrecon.py" ] || [ -f "netrecon.sh" ]; then
        mkdir -p "$INSTALL_DIR"
        cp -r ./* "$INSTALL_DIR/"
    else
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
else
    echo -e "${BLUE}[*] Updating existing NetRecon installation...${NC}"
    if [ -d ".git" ]; then
        cp -r ./* "$INSTALL_DIR/"
    else
        cd "$INSTALL_DIR" && git pull origin main || true
    fi
fi

cd "$INSTALL_DIR"

# Install Python requirements (with Kali/Debian PEP 668 compatibility)
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}[*] Installing Python dependencies...${NC}"
    pip3 install --break-system-packages -r requirements.txt || pip3 install -r requirements.txt
fi

# Make primary script executable and create a system-wide command
echo -e "${BLUE}[*] Setting up global shortcut command (netrecon)...${NC}"

if [ -f "netrecon.py" ]; then
    chmod +x netrecon.py
    cat << 'EOF' > "${BIN_DIR}/netrecon"
#!/usr/bin/env bash
python3 /opt/netrecon/netrecon.py "$@"
EOF
    chmod +x "${BIN_DIR}/netrecon"
elif [ -f "netrecon.sh" ]; then
    chmod +x netrecon.sh
    ln -sf "${INSTALL_DIR}/netrecon.sh" "${BIN_DIR}/netrecon"
else
    chmod +x ./* 2>/dev/null || true
fi

echo -e "\n${GREEN}[+] NetRecon installed successfully!${NC}"
echo -e "${YELLOW}[*] You can run the tool from any directory using:${NC} sudo netrecon\n"