#!/usr/bin/env python3
"""
Network Auto-Configuration for Veeder Reader
Handles dynamic IP assignment and subnet matching for IoT deployments
"""

import subprocess
import socket
import ipaddress
import json
import logging
import time
from datetime import datetime
import requests

class NetworkAutoConfig:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = 'config.json'
        
    def get_current_ip_info(self):
        """Get current Pi IP address and network info"""
        try:
            # Get primary network interface (usually eth0 or wlan0)
            result = subprocess.run(['ip', 'route', 'get', '8.8.8.8'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'src' in line:
                        parts = line.split()
                        src_index = parts.index('src')
                        if src_index + 1 < len(parts):
                            pi_ip = parts[src_index + 1]
                            
                            # Get interface name and subnet
                            interface = self.get_interface_for_ip(pi_ip)
                            subnet_info = self.get_subnet_info(interface)
                            
                            return {
                                'pi_ip': pi_ip,
                                'interface': interface,
                                'subnet': subnet_info['subnet'],
                                'netmask': subnet_info['netmask'],
                                'gateway': subnet_info['gateway']
                            }
                            
        except Exception as e:
            self.logger.error(f"Failed to get IP info: {e}")
            
        return None
        
    def get_interface_for_ip(self, ip):
        """Find which interface has the given IP"""
        try:
            result = subprocess.run(['ip', 'addr', 'show'], 
                                  capture_output=True, text=True)
            
            current_interface = None
            for line in result.stdout.split('\n'):
                if line.startswith(' ') == False and ':' in line:
                    # Interface line
                    current_interface = line.split(':')[1].strip()
                elif f'inet {ip}/' in line:
                    return current_interface
                    
        except Exception as e:
            self.logger.error(f"Failed to get interface for IP {ip}: {e}")
            
        return 'eth0'  # Default fallback
        
    def get_subnet_info(self, interface):
        """Get subnet information for interface"""
        try:
            result = subprocess.run(['ip', 'addr', 'show', interface], 
                                  capture_output=True, text=True)
            
            subnet = None
            netmask = None
            
            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    # Extract IP/CIDR
                    inet_part = line.strip().split()[1]  # e.g., "192.168.1.100/24"
                    network = ipaddress.IPv4Network(inet_part, strict=False)
                    subnet = str(network.network_address)
                    netmask = str(network.netmask)
                    break
                    
            # Get gateway
            gateway = self.get_gateway()
            
            return {
                'subnet': subnet,
                'netmask': netmask,
                'gateway': gateway
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get subnet info for {interface}: {e}")
            return {'subnet': None, 'netmask': None, 'gateway': None}
            
    def get_gateway(self):
        """Get default gateway"""
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True)
            
            for line in result.stdout.split('\n'):
                if 'default via' in line:
                    return line.split()[2]
                    
        except Exception as e:
            self.logger.error(f"Failed to get gateway: {e}")
            
        return None
        
    def discover_lantronix_devices(self):
        """Discover Lantronix devices across all possible subnets"""
        devices = []
        
        # Get current network info
        network_info = self.get_current_ip_info()
        if not network_info:
            self.logger.error("Cannot determine current network configuration")
            return devices
            
        self.logger.info(f"Current Pi network: {network_info}")
        
        # Try discovery on current subnet first
        current_subnet_devices = self.udp_discovery_on_subnet(network_info['pi_ip'])
        devices.extend(current_subnet_devices)
        
        # Also try common IoT subnets that Lantronix might be on
        common_subnets = [
            '192.168.1.0/24',
            '192.168.0.0/24', 
            '192.168.2.0/24',
            '10.0.0.0/24',
            '10.0.1.0/24',
            '172.16.0.0/24'
        ]
        
        for subnet in common_subnets:
            try:
                network = ipaddress.IPv4Network(subnet)
                # Use first host as source for discovery
                first_host = str(list(network.hosts())[0])
                subnet_devices = self.udp_discovery_on_subnet(first_host)
                
                # Add devices not already found
                for device in subnet_devices:
                    if device['ip'] not in [d['ip'] for d in devices]:
                        devices.append(device)
                        
            except Exception as e:
                self.logger.warning(f"Failed to scan subnet {subnet}: {e}")
                continue
                
        return devices
        
    def udp_discovery_on_subnet(self, source_ip):
        """Perform UDP discovery from a specific source IP"""
        devices = []
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(2)
            
            # Lantronix discovery packet (standard protocol)
            discovery_packet = b'\x00\x00\x00\xF6'
            
            # Send to Lantronix discovery port
            sock.sendto(discovery_packet, ('255.255.255.255', 30718))
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < 5:  # 5 second timeout
                try:
                    data, addr = sock.recvfrom(1024)
                    
                    # Parse Lantronix response
                    device_info = self.parse_lantronix_response(data, addr[0])
                    if device_info:
                        devices.append(device_info)
                        
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.warning(f"Error receiving UDP response: {e}")
                    
            sock.close()
            
        except Exception as e:
            self.logger.error(f"UDP discovery failed on {source_ip}: {e}")
            
        return devices
        
    def parse_lantronix_response(self, data, ip):
        """Parse Lantronix discovery response"""
        try:
            if len(data) >= 30:  # Minimum expected response size
                # Extract MAC address (bytes 0-5)
                mac = ':'.join([f'{b:02x}' for b in data[0:6]])
                
                return {
                    'ip': ip,
                    'mac': mac,
                    'type': 'Lantronix',
                    'status': 'Responsive',
                    'subnet': str(ipaddress.IPv4Network(f'{ip}/24', strict=False).network_address)
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to parse response from {ip}: {e}")
            
        return None
        
    def check_subnet_compatibility(self, lantronix_ip, pi_ip):
        """Check if Pi and Lantronix are on compatible subnets"""
        try:
            pi_network = ipaddress.IPv4Network(f'{pi_ip}/24', strict=False)
            lantronix_network = ipaddress.IPv4Network(f'{lantronix_ip}/24', strict=False)
            
            return pi_network.network_address == lantronix_network.network_address
            
        except Exception as e:
            self.logger.error(f"Failed to check subnet compatibility: {e}")
            return False
            
    def suggest_network_changes(self, lantronix_ip):
        """Suggest network configuration changes for compatibility"""
        suggestions = []
        
        network_info = self.get_current_ip_info()
        if not network_info:
            return ["Cannot determine current network configuration"]
            
        try:
            lantronix_network = ipaddress.IPv4Network(f'{lantronix_ip}/24', strict=False)
            pi_network = ipaddress.IPv4Network(f'{network_info["pi_ip"]}/24', strict=False)
            
            if lantronix_network.network_address != pi_network.network_address:
                suggestions.append(f"⚠️ SUBNET MISMATCH DETECTED")
                suggestions.append(f"Pi is on: {pi_network}")
                suggestions.append(f"Lantronix is on: {lantronix_network}")
                suggestions.append("")
                suggestions.append("OPTION 1: Change Pi subnet to match Lantronix")
                suggestions.append(f"- Go to router admin interface")
                suggestions.append(f"- Change Pi IP to: {lantronix_network.network_address.exploded[:-1]}xxx")
                suggestions.append(f"- Example new Pi IP: {lantronix_network.network_address + 50}")
                suggestions.append("")
                suggestions.append("OPTION 2: Change Lantronix IP to match Pi subnet")
                suggestions.append(f"- Use ARP recovery tool")
                suggestions.append(f"- Set Lantronix IP to: {pi_network.network_address + 100}")
                suggestions.append(f"- Gateway: {network_info['gateway']}")
                suggestions.append("")
                suggestions.append("RECOMMENDED: Option 1 (change Pi subnet) is usually easier")
                
        except Exception as e:
            suggestions.append(f"Error analyzing networks: {e}")
            
        return suggestions
        
    def generate_network_report(self):
        """Generate comprehensive network report for troubleshooting"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'pi_network_info': self.get_current_ip_info(),
            'discovered_devices': self.discover_lantronix_devices(),
            'compatibility_check': None,
            'recommendations': []
        }
        
        # Check compatibility with configured Lantronix
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                lantronix_ip = config.get('lantronix_ip')
                
                if lantronix_ip:
                    pi_ip = report['pi_network_info']['pi_ip']
                    report['compatibility_check'] = {
                        'lantronix_ip': lantronix_ip,
                        'pi_ip': pi_ip,
                        'compatible': self.check_subnet_compatibility(lantronix_ip, pi_ip)
                    }
                    
                    if not report['compatibility_check']['compatible']:
                        report['recommendations'] = self.suggest_network_changes(lantronix_ip)
                        
        except Exception as e:
            self.logger.warning(f"Could not check configured Lantronix: {e}")
            
        return report
        
    def auto_configure_for_deployment(self):
        """Automatic configuration for IoT deployment scenario"""
        self.logger.info("Starting automatic network configuration for deployment...")
        
        # Step 1: Discover current network state
        network_info = self.get_current_ip_info()
        if not network_info:
            return {"success": False, "error": "Cannot determine network configuration"}
            
        # Step 2: Discover Lantronix devices
        devices = self.discover_lantronix_devices()
        
        if not devices:
            return {
                "success": False, 
                "error": "No Lantronix devices found",
                "network_info": network_info,
                "suggestions": [
                    "1. Verify Lantronix device is powered on",
                    "2. Check network cables are connected", 
                    "3. Try ARP recovery if device was factory reset",
                    "4. Check if device is on a different subnet"
                ]
            }
            
        # Step 3: Check subnet compatibility
        best_device = devices[0]  # Use first discovered device
        compatible = self.check_subnet_compatibility(best_device['ip'], network_info['pi_ip'])
        
        result = {
            "success": True,
            "network_info": network_info,
            "discovered_devices": devices,
            "selected_device": best_device,
            "subnet_compatible": compatible
        }
        
        if not compatible:
            result["network_changes_needed"] = self.suggest_network_changes(best_device['ip'])
            
        return result

def main():
    """Command line interface for network auto-configuration"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Auto-Configuration for Veeder Reader')
    parser.add_argument('--discover', action='store_true', help='Discover Lantronix devices')
    parser.add_argument('--report', action='store_true', help='Generate network report')
    parser.add_argument('--auto-config', action='store_true', help='Auto-configure for deployment')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    
    config = NetworkAutoConfig()
    
    if args.discover:
        devices = config.discover_lantronix_devices()
        print(f"Found {len(devices)} Lantronix devices:")
        for device in devices:
            print(f"  - {device['ip']} ({device['mac']}) on subnet {device['subnet']}")
            
    elif args.report:
        report = config.generate_network_report()
        print(json.dumps(report, indent=2))
        
    elif args.auto_config:
        result = config.auto_configure_for_deployment()
        print(json.dumps(result, indent=2))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()