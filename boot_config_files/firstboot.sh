#!/bin/bash
# First boot setup script
# This runs once on first boot to install Tailscale and connect

LOCK_FILE="/var/lib/firstboot.done"

# Exit if already run
if [ -f "$LOCK_FILE" ]; then
    exit 0
fi

echo "🚀 Running first boot setup..."

# Install Tailscale
echo "📡 Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh

# Connect with auth key (you need to replace this with your actual key)
echo "🔗 Connecting to Tailscale network..."
# Get auth key from: https://login.tailscale.com/admin/settings/keys
# Make it reusable and set it to not expire
sudo tailscale up --authkey=YOUR_AUTH_KEY_HERE --hostname=veeder-$(hostname)

# Mark as completed
touch "$LOCK_FILE"

echo "✅ First boot setup complete!"
echo "📋 Pi should now be visible in your Tailscale admin panel"