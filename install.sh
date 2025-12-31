#!/bin/bash

# MKV Tool Suite - Installation Script
# Checks for Python, system dependencies (zenity, mkvtoolnix), and installs Python packages.

APP_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
DESKTOP_FILE="$HOME/.local/share/applications/mkv-tool-suite.desktop"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Welcome to the MKV Tool Suite Installer!${NC}"

# Function to check if a command exists
check_cmd() {
    command -v "$1" >/dev/null 2>&1
}

# 1. Check & Install System Dependencies
echo "Checking system dependencies..."

MISSING_DEPS=()

if ! check_cmd "python3"; then
    MISSING_DEPS+=("python3")
fi

if ! check_cmd "pip3" && ! check_cmd "pip"; then
    MISSING_DEPS+=("python3-pip")
fi

if ! check_cmd "zenity"; then
    MISSING_DEPS+=("zenity") # Required for file dialogs
fi

if ! check_cmd "mkvmerge"; then
    MISSING_DEPS+=("mkvtoolnix") # Required for MKV operations
fi

# Check for tkinter (often separate on Linux)
# We can't easily check 'python3-tk' via command, but we can check if python can import tkinter
if python3 -c "import tkinter" &> /dev/null; then
    : # tkinter is present
else
    MISSING_DEPS+=("python3-tk")
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${YELLOW}The following system dependencies are missing:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do
        echo " - $dep"
    done

    echo ""
    read -p "Do you want to install them now? (Requires sudo) [y/N] " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing dependencies..."
        # Update first to be safe
        sudo apt-get update
        sudo apt-get install -y "${MISSING_DEPS[@]}"
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to install dependencies. Please install them manually.${NC}"
            exit 1
        fi
        echo -e "${GREEN}Dependencies installed successfully!${NC}"
    else
        echo -e "${RED}Cannot proceed without dependencies. Exiting.${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}All system dependencies found.${NC}"
fi

# 2. Install Python Packages
echo "Installing Python packages..."
# Using --break-system-packages if on newer Debian/Ubuntu to install to user site, 
# or just standard install. We try standard first.
if check_cmd "pip3"; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

$PIP_CMD install --user -r "$APP_DIR/requirements.txt" || \
$PIP_CMD install --user -r "$APP_DIR/requirements.txt" --break-system-packages

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install Python packages.${NC}"
    echo "Please ensure you have internet access and try again."
    exit 1
fi

# 3. Create Desktop Shortcut
echo "Creating desktop shortcut..."
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=MKV Tool Suite
Comment=Unified MKV Tools (Extractor, Mixer, Editor, Creator)
Exec=python3 "$APP_DIR/main.py"
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=AudioVideo;Video;
EOF

chmod +x "$DESKTOP_FILE"

echo -e "${GREEN}==============================${NC}"
echo -e "${GREEN}   Installation Complete!     ${NC}"
echo -e "${GREEN}==============================${NC}"
echo "You can now launch 'MKV Tool Suite' from your applications menu."
echo "Or run it directly with: python3 main.py"
