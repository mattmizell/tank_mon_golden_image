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

## Quick Setup Process:

1. **Flash Pi OS Lite** to SD card
2. **Mount boot partition** on your computer
3. **Copy both files** from this directory to boot partition root
4. **Edit wpa_supplicant.conf** if using WiFi (uncomment and fill in network details)
5. **Eject SD card** and insert into Pi
6. **Boot Pi** and wait 2-3 minutes
7. **SSH to Pi**: `ssh pi@[PI-IP]` (password: raspberry)

## Network Discovery:
- Check router admin panel for device with MAC starting with `2C:CF:67` or similar Pi prefix
- Or scan network: `nmap -sn 192.168.0.0/24` (adjust subnet as needed)

## After SSH Works:
1. Clone golden image: `git clone https://github.com/mattmizell/tank_mon_golden_image.git`
2. Run deployment: `cd tank_mon_golden_image && ./deploy.sh`
3. Configure via web interface at port 8080