#!/usr/bin/env python3
"""
Lantronix Device Discovery and Configuration Tool
Based on the Lantronix Discovery Protocol (UDP Port 30718 / 0x77FE)

This tool automatically finds Lantronix devices on the network, even if they're
on different subnets or have factory default IPs.
"""

import socket
import struct
import time
import threading
import ipaddress
import logging
from datetime import datetime
import json

# Lantronix Discovery Protocol Constants
LANTRONIX_DISCOVERY_PORT = 30718  # 0x77FE
DISCOVERY_TIMEOUT = 3
DISCOVERY_RETRIES = 3
DISCOVERY_PROBE = b'\x00\x00\x00\xF8'  # Standard discovery probe

class LantronixDevice:
    def __init__(self, ip, mac, device_info=None):
        self.ip = ip
        self.mac = mac
        self.device_info = device_info or {}
        self.last_seen = datetime.now()
        
    def __str__(self):
        return f"Lantronix Device - IP: {self.ip}, MAC: {self.mac}"
    
    def to_dict(self):
        return {
            'ip': self.ip,
            'mac': self.mac,
            'device_info': self.device_info,
            'last_seen': self.last_seen.isoformat()
        }

class LantronixDiscovery:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.devices = []
        self.discovery_active = False
        
    def get_local_interfaces(self):
        """Get all local network interfaces and their subnets"""
        interfaces = []
        try:
            # Get hostname to find local IPs
            hostname = socket.gethostname()
            
            # Get all IP addresses for this host
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip.startswith('127.'):
                    continue
                    
                # Try to determine subnet (assume /24 for now)
                try:
                    network = ipaddress.IPv4Network(f"{ip}/24", strict=False)
                    interfaces.append({
                        'ip': ip,
                        'network': str(network),
                        'broadcast': str(network.broadcast_address)
                    })
                except:
                    pass
                    
        except Exception as e:
            self.logger.error(f"Error getting local interfaces: {e}")
            
        # Fallback - try to get default interface
        if not interfaces:
            try:
                # Connect to a dummy address to find default interface
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()
                
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
                interfaces.append({
                    'ip': local_ip,
                    'network': str(network),
                    'broadcast': str(network.broadcast_address)
                })
            except:
                pass
                
        return interfaces
    
    def parse_discovery_response(self, data, sender_ip):
        """Parse the 30-byte discovery response from Lantronix device"""
        if len(data) < 30:
            return None
            
        try:
            # Extract MAC address (typically in bytes 6-12)
            mac_bytes = data[6:12]
            mac = ':'.join(f'{b:02x}' for b in mac_bytes)
            
            # Extract device information
            device_info = {
                'raw_data': data.hex(),
                'data_length': len(data),
                'sender_ip': sender_ip
            }
            
            # Try to extract more information from the response
            # This is based on reverse engineering and may vary by device model
            if len(data) >= 30:
                device_info['device_type'] = data[0:2].hex()
                device_info['firmware_version'] = data[2:4].hex()
                device_info['status'] = data[4:6].hex()
                
            return LantronixDevice(sender_ip, mac, device_info)
            
        except Exception as e:
            self.logger.error(f"Error parsing discovery response: {e}")
            return None
    
    def send_discovery_broadcast(self, interface_ip, broadcast_ip):
        """Send discovery broadcast on a specific interface"""
        discovered_devices = []
        
        try:
            # Create UDP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(DISCOVERY_TIMEOUT)
            
            # Bind to specific interface
            sock.bind((interface_ip, 0))
            
            # Send discovery probe
            sock.sendto(DISCOVERY_PROBE, (broadcast_ip, LANTRONIX_DISCOVERY_PORT))
            self.logger.debug(f"Sent discovery probe from {interface_ip} to {broadcast_ip}")
            
            # Listen for responses
            start_time = time.time()
            while time.time() - start_time < DISCOVERY_TIMEOUT:
                try:
                    data, addr = sock.recvfrom(1024)
                    self.logger.debug(f"Received response from {addr[0]}: {data.hex()}")
                    
                    device = self.parse_discovery_response(data, addr[0])
                    if device:
                        discovered_devices.append(device)
                        self.logger.info(f"Found Lantronix device: {device}")
                        
                except socket.timeout:
                    break
                except Exception as e:
                    self.logger.debug(f"Error receiving response: {e}")
                    
            sock.close()
            
        except Exception as e:
            self.logger.error(f"Error in discovery broadcast: {e}")
            
        return discovered_devices
    
    def discover_devices(self, target_subnets=None):
        """Discover Lantronix devices on the network"""
        self.logger.info("🔍 Starting Lantronix device discovery...")
        self.discovery_active = True
        self.devices = []
        
        # Get local interfaces
        interfaces = self.get_local_interfaces()
        if not interfaces:
            self.logger.error("No network interfaces found")
            return []
        
        # Add common factory default subnets
        default_subnets = [
            '192.168.1.0/24',
            '10.0.0.0/24',
            '172.16.0.0/24',
            '192.168.0.0/24',
            '169.254.0.0/16'  # Link-local
        ]
        
        # Combine interface subnets with defaults
        all_subnets = []
        for interface in interfaces:
            all_subnets.append({
                'interface_ip': interface['ip'],
                'broadcast_ip': interface['broadcast'],
                'network': interface['network']
            })
        
        # Add default subnets (broadcast from first interface)
        if interfaces:
            first_interface = interfaces[0]['ip']
            for subnet in default_subnets:
                try:
                    network = ipaddress.IPv4Network(subnet)
                    all_subnets.append({
                        'interface_ip': first_interface,
                        'broadcast_ip': str(network.broadcast_address),
                        'network': subnet
                    })
                except:
                    pass
        
        # Use threads for parallel discovery
        threads = []
        results = []
        
        for subnet in all_subnets:
            def discover_subnet(subnet_info):
                devices = self.send_discovery_broadcast(
                    subnet_info['interface_ip'],
                    subnet_info['broadcast_ip']
                )
                results.extend(devices)
            
            thread = threading.Thread(target=discover_subnet, args=(subnet,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Remove duplicates based on MAC address
        unique_devices = {}
        for device in results:
            if device.mac not in unique_devices:
                unique_devices[device.mac] = device
        
        self.devices = list(unique_devices.values())
        self.discovery_active = False
        
        self.logger.info(f"✅ Discovery complete. Found {len(self.devices)} Lantronix devices")
        return self.devices
    
    def test_device_connection(self, ip, port=10001):
        """Test if a Lantronix device is accessible on the given port"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_device_info(self, ip):
        """Get detailed information about a Lantronix device"""
        try:
            # Try to connect to web interface (port 80)
            info = {'ip': ip, 'accessible_ports': []}
            
            # Test common Lantronix ports
            test_ports = [80, 9999, 10001, 23]  # Web, Setup, Serial, Telnet
            
            for port in test_ports:
                if self.test_device_connection(ip, port):
                    info['accessible_ports'].append(port)
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting device info for {ip}: {e}")
            return {'ip': ip, 'error': str(e)}
    
    def configure_device_ip(self, device_mac, new_ip, new_netmask='255.255.255.0', new_gateway=None):
        """Configure a Lantronix device's IP address using the discovery protocol"""
        try:
            # Parse MAC address
            mac_bytes = bytes.fromhex(device_mac.replace(':', ''))
            if len(mac_bytes) != 6:
                raise ValueError("Invalid MAC address format")
            
            # Create IP configuration command
            # Based on the protocol: "IP-SETUP" + 00 00 + last 2 bytes of MAC + new IP
            command = b'IP-SETUP'  # ASCII "IP-SETUP"
            command += b'\x00\x00'  # Padding
            command += mac_bytes[-2:]  # Last 2 bytes of MAC
            command += socket.inet_aton(new_ip)  # New IP address
            command += socket.inet_aton(new_netmask)  # Netmask
            
            if new_gateway:
                command += socket.inet_aton(new_gateway)  # Gateway
            
            # Send configuration command
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(command, ('255.255.255.255', LANTRONIX_DISCOVERY_PORT))
            sock.close()
            
            self.logger.info(f"Sent IP configuration command to {device_mac}: {new_ip}")
            
            # Wait a moment for the device to reconfigure
            time.sleep(2)
            
            # Test if the device is now accessible at the new IP
            if self.test_device_connection(new_ip):
                self.logger.info(f"✅ Device {device_mac} successfully configured to {new_ip}")
                return True
            else:
                self.logger.warning(f"⚠️ Device may have been configured but is not yet accessible at {new_ip}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configuring device IP: {e}")
            return False

def main():
    """Main function for standalone execution"""
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 Lantronix Device Discovery Tool")
    print("=" * 40)
    
    discovery = LantronixDiscovery()
    
    # Discover devices
    devices = discovery.discover_devices()
    
    if not devices:
        print("❌ No Lantronix devices found")
        return
    
    print(f"\n✅ Found {len(devices)} Lantronix device(s):")
    print("-" * 40)
    
    for i, device in enumerate(devices):
        print(f"{i+1}. {device}")
        
        # Get additional info
        info = discovery.get_device_info(device.ip)
        if info.get('accessible_ports'):
            print(f"   Accessible ports: {info['accessible_ports']}")
        
        # Test Veeder Root connection (port 10001)
        if discovery.test_device_connection(device.ip, 10001):
            print(f"   ✅ Veeder Root port (10001) accessible")
        else:
            print(f"   ❌ Veeder Root port (10001) not accessible")
        
        print()

if __name__ == '__main__':
    main()