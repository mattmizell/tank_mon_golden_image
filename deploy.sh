#!/bin/bash
# Veeder Reader Deployment Script
# Run this on the new Raspberry Pi

set -e

echo "=== Veeder Reader Deployment Script ==="
echo "This script will set up the Veeder Reader on this Pi"
echo

# Check if running as mattmizell
if [ "$USER" != "mattmizell" ]; then
    echo "ERROR: Please run this script as the mattmizell user"
    exit 1
fi

# Check if files exist
if [ ! -f "collector.py" ] || [ ! -f "simple_web_server.py" ]; then
    echo "ERROR: Required files not found. Please run from the golden image directory."
    exit 1
fi

echo "1. Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "2. Installing Python dependencies..."
pip install -r requirements.txt

echo "3. Setting permissions..."
chmod +x collector.py simple_web_server.py find_veeder_tls.py
chmod +x lantronix_discovery.py network_auto_config.py

echo "4. Installing system Python packages..."
sudo apt install -y python3-flask python3-requests
pip3 install schedule --break-system-packages >/dev/null 2>&1 || echo "Schedule package install attempted"

echo "5. Installing Tailscale for remote access..."
./install_tailscale.sh

echo "6. Setting up permissions..."
chmod +x *.py

echo "7. Setting up auto-start on boot..."
./setup_autostart.sh

echo "8. Starting services manually for immediate use..."
python3 simple_web_server.py > web.log 2>&1 &
sleep 2
python3 collector.py > collector.log 2>&1 &
sleep 3

echo "9. Checking running services..."
ps aux | grep python3 | grep -E "(simple_web|collector)" | grep -v grep

echo
echo "=== Deployment Complete! ==="
echo "Web interface available at: http://$(hostname -I | cut -d' ' -f1):8080"
echo "Configure via web interface to complete setup."
echo
echo "To install Tailscale for remote access:"
echo "  curl -fsSL https://tailscale.com/install.sh | sh"
echo "  sudo tailscale up"