# Tank Monitor Golden Image

Production-ready Veeder Reader deployment package for Raspberry Pi-based fuel tank monitoring.

## Overview
This golden image contains the complete software stack needed to deploy a tank monitoring system that:
- Connects to Veeder Root TLS 350 gauges via Lantronix serial-to-IP converters
- Collects tank level data at configurable intervals
- Uploads data to central monitoring server
- Provides web-based configuration interface

## Key Features
- **Web Configuration**: Browser-based setup at port 8080
- **Auto-Discovery**: Automatic network scanning for Lantronix devices
- **Auto-Start**: Systemd services for reliable operation
- **Remote Access**: Tailscale VPN support for remote management
- **Subnet Handling**: Built-in network compatibility detection

## Quick Start
1. Extract files to new Raspberry Pi
2. Run `./deploy.sh`
3. Access web interface at `http://[PI-IP]:8080`
4. Configure store settings via web interface

## Contents
- `collector.py` - Main data collection service
- `simple_web_server.py` - Web configuration interface
- `deploy.sh` - Automated deployment script
- `DEPLOYMENT_INSTRUCTIONS.md` - Detailed setup guide
- Service files for systemd integration

## Requirements
- Raspberry Pi 3/4/5
- Python 3.8+
- Network connection (Ethernet or WiFi)
- Access to Veeder Root TLS 350 via Lantronix

## Support
For deployment assistance, refer to DEPLOYMENT_INSTRUCTIONS.md

## Version
Golden Image Version: 2025-07-07