#!/bin/bash

# MKV Tool Suite - Chromebook/Debian Setup Script

echo "=== MKV Tool Suite Setup ==="
echo "Updating package lists..."
sudo apt update

echo "Installing system dependencies (Python, MKVToolNix)..."
sudo apt install -y python3-pip python3-tk python3-venv mkvtoolnix mkvtoolnix-gui

echo "Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

echo "Activating virtual environment and installing Python libraries..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup Complete!"
echo "To run the application, execute: ./run.sh"
