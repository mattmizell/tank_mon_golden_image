#!/bin/bash
# Install and configure Tailscale on Pi

echo "🌐 Installing Tailscale..."

# Download and install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

echo "✅ Tailscale installed"
echo "🔗 To connect this Pi to your Tailscale network:"
echo "   sudo tailscale up"
echo ""
echo "📋 Then check the Tailscale admin console for the new device"
echo "   and note its 100.x.x.x IP address for SSH access"