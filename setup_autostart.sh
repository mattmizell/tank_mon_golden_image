#!/bin/bash
# Setup auto-start for tank monitor services using crontab

echo "🚀 Setting up auto-start for tank monitor services..."

# Add crontab entries for auto-start on boot
(crontab -l 2>/dev/null || echo ""; echo "@reboot cd /home/mattmizell/Veeder_Reader && python3 simple_web_server.py > web.log 2>&1 &"; echo "@reboot sleep 10 && cd /home/mattmizell/Veeder_Reader && python3 collector.py > collector.log 2>&1 &") | crontab -

echo "✅ Auto-start configured!"
echo "📋 Services will start automatically on every boot:"
echo "   - Web interface on port 8080"
echo "   - Tank data collector"
echo ""
echo "📝 Current crontab:"
crontab -l