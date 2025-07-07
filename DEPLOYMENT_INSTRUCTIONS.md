# Veeder Reader Golden Image Deployment Instructions
## Version: 2025-07-07

### Files Included:
- `collector.py` - Main data collection service (web-configurable)
- `simple_web_server.py` - Web configuration interface (port 8080)
- `find_veeder_tls.py` - TLS 350 protocol handler
- `lantronix_discovery.py` - Network discovery tool
- `network_auto_config.py` - Subnet compatibility handler
- `config.json` - Configuration file (set to UNCONFIGURED)
- `requirements.txt` - Python dependencies
- `veeder_root_tls_socket_library/` - Protocol implementation
- `veeder-web.service` - Systemd service for web interface
- `veeder-collector.service` - Systemd service for collector

### Deployment Steps:

1. **Prepare the SD Card (FIRST - before booting Pi):**
   ```bash
   # Flash Pi OS Lite to SD card
   # Mount the boot partition on your computer
   # Copy files from boot_config_files/ to boot partition root:
   #   - ssh (empty file - enables SSH)
   #   - wpa_supplicant.conf (WiFi config if needed)
   # Eject SD card and insert into Pi
   ```

2. **Boot and Connect to Pi:**
   ```bash
   # Boot Pi and wait 2-3 minutes
   # Find Pi IP in router admin panel (MAC starts with 2C:CF:67)
   # SSH to Pi: ssh pi@[PI-IP] (password: raspberry)
   ```

3. **Update Pi System:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python and dependencies  
   sudo apt install python3 python3-pip python3-venv git -y
   ```

2. **Create user and directory:**
   ```bash
   sudo useradd -m -s /bin/bash mattmizell
   sudo passwd mattmizell  # Set to: training1
   sudo usermod -aG sudo mattmizell
   ```

3. **Copy files to Pi:**
   ```bash
   # As mattmizell user
   mkdir -p /home/mattmizell/Veeder_Reader
   cd /home/mattmizell/Veeder_Reader
   
   # Copy all files from this golden image to the Pi
   ```

4. **Set up Python environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Install systemd services:**
   ```bash
   sudo cp veeder-*.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable veeder-web.service veeder-collector.service
   sudo systemctl start veeder-web.service veeder-collector.service
   ```

6. **Install Tailscale (for remote access):**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```

### Configuration:
1. Access web interface at `http://[PI-IP]:8080`
2. Click "Scan Network" to find Lantronix device
3. Update store name from "UNCONFIGURED"
4. Save configuration
5. Collector will automatically start uploading data

### Network Considerations:
- Pi must be on same subnet as Lantronix for discovery
- If subnet mismatch, configure router DHCP accordingly
- Default expects Lantronix on 192.168.x.x network

### Verification:
```bash
# Check services status
sudo systemctl status veeder-web veeder-collector

# View logs
sudo journalctl -u veeder-collector -f
```

### Support:
- Web interface logs: `/home/mattmizell/Veeder_Reader/web_server.log`
- Collector logs: Check systemd journal
- Remote access: Via Tailscale VPN