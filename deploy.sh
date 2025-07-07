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

echo "4. Installing systemd services..."
sudo cp veeder-*.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "5. Enabling services..."
sudo systemctl enable veeder-web.service veeder-collector.service

echo "6. Installing Tailscale for remote access..."
./install_tailscale.sh

echo "7. Starting services..."
sudo systemctl start veeder-web.service
sudo systemctl start veeder-collector.service

echo "8. Checking service status..."
sudo systemctl status veeder-web.service --no-pager
echo
sudo systemctl status veeder-collector.service --no-pager

echo
echo "=== Deployment Complete! ==="
echo "Web interface available at: http://$(hostname -I | cut -d' ' -f1):8080"
echo "Configure via web interface to complete setup."
echo
echo "To install Tailscale for remote access:"
echo "  curl -fsSL https://tailscale.com/install.sh | sh"
echo "  sudo tailscale up"