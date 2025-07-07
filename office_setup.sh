#!/bin/bash
# Office Setup Script for Pre-Deployment Pi Configuration
# Run this after SSH'ing to the Pi on office WiFi

echo "🏢 Veeder Reader Office Setup"
echo "Pi Hostname: $(hostname)"
echo "IP Address: $(hostname -I | cut -d' ' -f1)"
echo ""

# 1. Install Tailscale if not already installed
if ! command -v tailscale &> /dev/null; then
    echo "📡 Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "✅ Tailscale already installed"
fi

# 2. Connect to Tailscale network
echo "🔗 Connecting to Tailscale network..."
sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=veeder-$(hostname)

# Get Tailscale IP
sleep 3
TAILSCALE_IP=$(tailscale ip -4)
echo "📋 Tailscale IP: $TAILSCALE_IP"

# 3. Clone and deploy golden image
echo "📥 Cloning golden image..."
rm -rf tank_mon_golden_image 2>/dev/null
git clone https://github.com/mattmizell/tank_mon_golden_image.git
cd tank_mon_golden_image

echo "🚀 Deploying tank monitor services..."
chmod +x deploy.sh
./deploy.sh

echo ""
echo "🎉 Office Setup Complete!"
echo "📋 Summary:"
echo "   Pi Hostname: $(hostname)"
echo "   Tailscale IP: $TAILSCALE_IP"
echo "   Web Interface: http://$TAILSCALE_IP:8080"
echo ""
echo "✅ Ready for Veeder Reader box integration"
echo "📦 Next: Install in mobile router box for field deployment"