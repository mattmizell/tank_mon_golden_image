# Production Deployment Workflow

## **Pre-Deployment Setup (Office)**

### **1. Pi Imaging with Custom Image**
- Use Raspberry Pi Imager with custom configuration
- **User**: `mattmizell` (pre-configured)
- **SSH**: Enabled automatically
- **WiFi**: Office network credentials
- **Hostname**: `VeederReader1`, `VeederReader2`, etc. (increment manually)

### **2. Initial Connection**
- Pi boots and connects to office WiFi
- Check router/network for `VeederReader#` device
- Note the assigned IP address
- SSH to Pi: `ssh mattmizell@[IP]` (password: training1)

### **3. Tailscale Installation**
```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to network  
sudo tailscale up --authkey=YOUR_TAILSCALE_AUTH_KEY --hostname=veeder-$(hostname)

# Note the 100.x.x.x IP from Tailscale admin panel
```

### **4. Golden Image Deployment**
```bash
# Clone and deploy
git clone https://github.com/mattmizell/tank_mon_golden_image.git
cd tank_mon_golden_image
./deploy.sh

# Services will auto-start and be configured for boot
```

### **5. Box Integration**
- Install Pi in Veeder Reader box
- Connect to mobile modem via ethernet switch
- Box contains: Pi + Mobile Modem + Network Switch
- Ready for field deployment

## **Field Deployment (Gas Station)**

### **1. Physical Installation**
- Install box at gas station
- Connect power and cellular antenna
- Wait 2-3 minutes for boot and cellular connection

### **2. Remote Configuration**
- Access via Tailscale: http://100.x.x.x:8080
- Set store name (replace "UNCONFIGURED")
- Scan network for Lantronix device
- Save configuration
- Collector auto-starts

### **3. Verification**
- ✅ Web interface shows "Collector Running: True"
- ✅ Tank data appearing in central dashboard
- ✅ Data uploads every 5 minutes

## **Benefits of This Workflow**
- ✅ **Pre-tested**: Verified working before field deployment
- ✅ **Remote Access**: Always accessible via Tailscale
- ✅ **Zero Field Config**: Just power on and configure via web
- ✅ **Reliable**: Auto-start services, proven cellular connection