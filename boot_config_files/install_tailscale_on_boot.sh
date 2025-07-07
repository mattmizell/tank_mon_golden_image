#!/bin/bash
# Auto-install Tailscale on first boot
# This script gets copied to the boot partition and runs automatically

echo "🌐 Installing Tailscale on first boot..."

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to your Tailscale network with auth key
# You'll need to replace YOUR_AUTH_KEY with a real auth key from https://login.tailscale.com/admin/settings/keys
sudo tailscale up --authkey=YOUR_AUTH_KEY --hostname=veeder-reader-$(date +%s)

echo "✅ Tailscale installed and connected!"
echo "📋 Check https://login.tailscale.com/admin/machines for the new device"

# Remove this script so it doesn't run again
rm -f /boot/firmware/install_tailscale_on_boot.sh