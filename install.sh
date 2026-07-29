#!/usr/bin/env bash

# ===================================================================
# Project Name : NetRecon - Automated Kali Linux Installer
# Author       : Syed Hoque
# GitHub       : https://github.com/Syedhoque/netrecon.git
# ===================================================================

# Exit immediately if a command exits with a non-zero status
set -e

# Color definitions for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}[*] Starting NetRecon Installation for Kali Linux...${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Please run this installer with sudo or as root.${NC}"
  echo -e "    Example: sudo bash install.sh"
  exit 1
fi

INSTALL_DIR="/opt/netrecon"
BIN_DIR="/usr/local/bin"

echo -e "${BLUE}[*] Updating package index and installing system dependencies...${NC}"
apt-get update -y
apt-get install -y python3 python3-pip python3-venv git curl

echo -e "${BLUE}[*] Setting up installation directory at ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"

# Copy current repository files to destination directory
cp -r ./* "$INSTALL_DIR/"

# Navigate to installation directory
cd "$INSTALL_DIR"

# Install Python requirements if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -e "${BLUE}[*] Installing Python dependencies from requirements.txt...${NC}"
    pip3 install --break-system-packages -r requirements.txt || pip3 install -r requirements.txt
fi

# Ensure main script is executable (assuming main file is netrecon.py or netrecon.sh)
if [ -f "netrecon.py" ]; then
    chmod +x netrecon.py
    # Create global symlink
    echo -e "${BLUE}[*] Creating global command 'netrecon'...${NC}"
    cat << 'EOF' > "${BIN_DIR}/netrecon"
#!/usr/bin/env bash
python3 /opt/netrecon/netrecon.py "$@"
EOF
    chmod +x "${BIN_DIR}/netrecon"
elif [ -f "netrecon.sh" ]; then
    chmod +x netrecon.sh
    ln -sf "${INSTALL_DIR}/netrecon.sh" "${BIN_DIR}/netrecon"
fi

echo -e "${GREEN}[+] NetRecon installation completed successfully!${NC}"
echo -e "${YELLOW}[*] You can now run the tool from anywhere using: ${NC}sudo netrecon"