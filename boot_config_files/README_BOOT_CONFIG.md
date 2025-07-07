# Boot Configuration Files for New Pi Setup

These files need to be copied to the SD card's boot partition for each new Pi deployment.

## Files to Copy:

### 1. `ssh` (empty file)
- **Purpose**: Enables SSH service on first boot
- **Location**: Copy to root of boot partition
- **Required**: YES - SSH will not work without this

### 2. `wpa_supplicant.conf`
- **Purpose**: WiFi configuration (optional if using Ethernet)
- **Location**: Copy to root of boot partition  
- **Usage**: Edit to add your WiFi credentials before copying

### 3. `firstboot.sh` (OPTIONAL - for automatic Tailscale)
- **Purpose**: Installs and connects Tailscale on first boot
- **Location**: Copy to root of boot partition
- **Setup**: EDIT FILE to add your Tailscale auth key before copying
- **Get Auth Key**: https://login.tailscale.com/admin/settings/keys

### 4. `firstboot.service` (if using firstboot.sh)
- **Purpose**: Systemd service to run firstboot.sh automatically
- **Location**: Copy to root of boot partition

## Quick Setup Process:

### Basic Setup (SSH only):
1. **Flash Pi OS Lite** to SD card
2. **Mount boot partition** on your computer
3. **Copy `ssh` file** to boot partition root
4. **Copy `wpa_supplicant.conf`** if using WiFi (edit first)
5. **Eject SD card** and insert into Pi
6. **Boot Pi** and wait 2-3 minutes
7. **SSH to Pi**: `ssh pi@[PI-IP]` (password: raspberry)

### Auto-Tailscale Setup (recommended):
1. **Get Tailscale auth key** from https://login.tailscale.com/admin/settings/keys
   - Create a reusable key that doesn't expire
   - Copy the key value
2. **Edit `firstboot.sh`** - replace `YOUR_AUTH_KEY_HERE` with your actual key
3. **Copy all 4 files** to boot partition root:
   - `ssh`
   - `wpa_supplicant.conf` (if using WiFi)
   - `firstboot.sh` (with your auth key)
   - `firstboot.service`
4. **Boot Pi** - it will auto-install Tailscale and connect to your network
5. **Check Tailscale admin panel** for the new device
6. **SSH via Tailscale**: `ssh pi@100.x.x.x` (check admin panel for IP)

## Network Discovery:
- Check router admin panel for device with MAC starting with `2C:CF:67` or similar Pi prefix
- Or scan network: `nmap -sn 192.168.0.0/24` (adjust subnet as needed)

## After SSH Works:
1. Clone golden image: `git clone https://github.com/mattmizell/tank_mon_golden_image.git`
2. Run deployment: `cd tank_mon_golden_image && ./deploy.sh`
3. Configure via web interface at port 8080