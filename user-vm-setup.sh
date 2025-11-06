#!/bin/bash

# Script Name: setup_xrdp_xfce.sh

# Description: Installs XFCE desktop environment and configures XRDP for remote desktop access.

# Author: Arunvel Arunachalam

set -e

echo "=== Updating system packages ==="
sudo apt update -y && sudo apt upgrade -y

echo "=== Installing XFCE desktop environment ==="
sudo apt install -y xfce4 xfce4-goodies xubuntu-desktop

echo "=== Installing XRDP ==="
sudo apt install -y xrdp

echo "=== Enabling and starting XRDP service ==="
sudo systemctl enable xrdp
sudo systemctl start xrdp

echo "=== Configuring XRDP to start XFCE ==="
sudo bash -c 'echo "startxfce4" > /etc/xrdp/startwm.sh'
sudo chmod +x /etc/xrdp/startwm.sh

echo "=== Creating .xsession file for the current user ==="
echo "startxfce4" > ~/.xsession
chmod +x ~/.xsession

echo "=== Restarting XRDP service ==="
sudo systemctl restart xrdp

echo "=== Checking XRDP service status ==="
sudo systemctl status xrdp --no-pager

echo "=== Setup complete! You can now connect via RDP using your server IP. ==="
