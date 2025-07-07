#!/usr/bin/env python3
"""
SIMPLE working web server - no bullshit
"""
from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

def load_config():
    """Load config or return defaults"""
    try:
        if os.path.exists('config.json'):
            with open('config.json', 'r') as f:
                return json.load(f)
    except:
        pass
    return {
        "store_name": "TEST_STORE",
        "lantronix_ip": "localhost", 
        "central_api_url": "https://central-tank-server.onrender.com/upload",
        "poll_interval_seconds": 300
    }

def save_config(config):
    """Save config to file"""
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)

def test_lantronix_connection(ip):
    """Test connection - simple version"""
    try:
        from find_veeder_tls import get_tank_levels
        tanks = get_tank_levels(ip)
        return {
            "success": True,
            "tanks": len(tanks),
            "message": f"Found {len(tanks)} tanks"
        }
    except Exception as e:
        return {
            "success": False, 
            "error": str(e)
        }

@app.route('/')
def home():
    """Simple home page"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Veeder Reader Setup</title>
    <style>
        body { font-family: Arial; margin: 40px; }
        .btn { padding: 10px 20px; margin: 10px; background: #007cba; color: white; border: none; cursor: pointer; }
        .btn:hover { background: #005a82; }
        .error { color: red; }
        .success { color: green; }
        .loading { color: orange; }
        input { padding: 8px; margin: 5px; width: 200px; }
        label { display: block; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🔧 Veeder Reader Setup</h1>
    
    <h3>Step 1: Find Lantronix Device</h3>
    <button class="btn" onclick="scanNetwork()">🔍 Scan Network</button>
    <div id="scan-status"></div>
    <div id="devices"></div>
    
    <h3>Step 2: Manual Entry (if needed)</h3>
    <label>Lantronix IP:</label>
    <input type="text" id="manual-ip" placeholder="192.168.1.100">
    <button class="btn" onclick="testManual()">Test Connection</button>
    
    <h3>Step 3: Configure</h3>
    <div id="current-config"></div>
    <form onsubmit="saveConfig(event)">
        <label>Store Name:</label>
        <input type="text" id="store-name" value="TEST_STORE" required>
        
        <label>Lantronix IP:</label>
        <input type="text" id="lantronix-ip" required>
        
        <label>Central API URL:</label>
        <input type="text" id="central-api" value="https://central-tank-server.onrender.com/upload" required>
        
        <label>Polling Frequency (seconds):</label>
        <input type="number" id="poll-interval" value="60" min="30" max="3600" required>
        <small>How often to collect tank data (30-3600 seconds)</small>
        
        <button type="submit" class="btn">Save Configuration</button>
    </form>
    
    <h3>Step 4: Status</h3>
    <button class="btn" onclick="checkStatus()">🔄 Check Status</button>
    <div id="status-display"></div>
    
    <script>
        function scanNetwork() {
            document.getElementById('scan-status').innerHTML = '<div class="loading">🔄 Scanning network...</div>';
            
            fetch('/api/scan-network')
                .then(response => {
                    if (!response.ok) throw new Error('Network response was not ok');
                    return response.json();
                })
                .then(data => {
                    document.getElementById('scan-status').innerHTML = '';
                    if (data.devices && data.devices.length > 0) {
                        let html = '<div class="success">✅ Found devices:</div>';
                        data.devices.forEach(device => {
                            html += `<div style="margin: 10px; padding: 10px; border: 1px solid #ccc;">
                                <strong>IP:</strong> ${device.ip}<br>
                                <strong>MAC:</strong> ${device.mac}<br>
                                <button class="btn" onclick="selectDevice('${device.ip}')">Select This Device</button>
                            </div>`;
                        });
                        document.getElementById('devices').innerHTML = html;
                    } else {
                        document.getElementById('devices').innerHTML = '<div class="error">❌ No devices found</div>';
                    }
                })
                .catch(error => {
                    document.getElementById('scan-status').innerHTML = `<div class="error">❌ Error: ${error}</div>`;
                });
        }
        
        function selectDevice(ip) {
            document.getElementById('lantronix-ip').value = ip;
            document.getElementById('manual-ip').value = ip;
            testConnection(ip);
        }
        
        function testManual() {
            const ip = document.getElementById('manual-ip').value;
            if (ip) {
                document.getElementById('lantronix-ip').value = ip;
                testConnection(ip);
            }
        }
        
        function testConnection(ip) {
            document.getElementById('scan-status').innerHTML = '<div class="loading">🔄 Testing connection...</div>';
            
            fetch('/api/test-connection', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ip: ip})
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    document.getElementById('scan-status').innerHTML = 
                        `<div class="success">✅ Connection successful! Found ${data.tanks} tanks</div>`;
                } else {
                    document.getElementById('scan-status').innerHTML = 
                        `<div class="error">❌ Connection failed: ${data.error}</div>`;
                }
            })
            .catch(error => {
                document.getElementById('scan-status').innerHTML = 
                    `<div class="error">❌ Error: ${error}</div>`;
            });
        }
        
        function saveConfig(event) {
            event.preventDefault();
            
            const config = {
                store_name: document.getElementById('store-name').value,
                lantronix_ip: document.getElementById('lantronix-ip').value,
                central_api_url: document.getElementById('central-api').value,
                poll_interval_seconds: parseInt(document.getElementById('poll-interval').value)
            };
            
            fetch('/api/save-config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('✅ Configuration saved!');
                } else {
                    alert('❌ Error: ' + data.error);
                }
            })
            .catch(error => {
                alert('❌ Error: ' + error);
            });
        }
        
        function loadCurrentConfig() {
            fetch('/api/get-config')
                .then(response => response.json())
                .then(config => {
                    document.getElementById('store-name').value = config.store_name || 'TEST_STORE';
                    document.getElementById('lantronix-ip').value = config.lantronix_ip || '';
                    document.getElementById('central-api').value = config.central_api_url || 'https://central-tank-server.onrender.com/upload';
                    document.getElementById('poll-interval').value = config.poll_interval_seconds || 60;
                    
                    document.getElementById('current-config').innerHTML = 
                        `<div style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px;">
                            <strong>Current Configuration:</strong><br>
                            Store: ${config.store_name}<br>
                            Lantronix IP: ${config.lantronix_ip}<br>
                            Poll Interval: ${config.poll_interval_seconds} seconds
                        </div>`;
                })
                .catch(error => console.error('Error loading config:', error));
        }
        
        function checkStatus() {
            document.getElementById('status-display').innerHTML = '<div class="loading">🔄 Checking status...</div>';
            
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    const status = data.collector_running ? 
                        '<span style="color: green;">✅ Running</span>' : 
                        '<span style="color: red;">❌ Not Running</span>';
                    
                    document.getElementById('status-display').innerHTML = 
                        `<div style="background: #f0f0f0; padding: 10px; margin: 10px 0; border-radius: 5px;">
                            <strong>System Status:</strong><br>
                            Collector: ${status}<br>
                            Polling Frequency: ${data.config.poll_interval_seconds} seconds<br>
                            Log: ${data.log_info}
                        </div>`;
                })
                .catch(error => {
                    document.getElementById('status-display').innerHTML = 
                        `<div class="error">❌ Error: ${error}</div>`;
                });
        }
        
        // Load current config on page load
        window.onload = function() {
            loadCurrentConfig();
        };
    </script>
</body>
</html>
    '''

@app.route('/api/scan-network')
def scan_network():
    """Real UDP network discovery"""
    try:
        from lantronix_discovery import LantronixDiscovery
        
        discovery = LantronixDiscovery()
        devices = discovery.discover_devices()
        
        device_list = []
        for device in devices:
            device_info = {
                'ip': device.ip,
                'mac': device.mac,
                'accessible_ports': []
            }
            
            # Test port 10001 (Veeder Root)
            if discovery.test_device_connection(device.ip, 10001):
                device_info['accessible_ports'].append(10001)
            
            device_list.append(device_info)
        
        return jsonify({"devices": device_list})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """Test connection to device"""
    try:
        data = request.get_json()
        ip = data.get('ip')
        result = test_lantronix_connection(ip)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/save-config', methods=['POST'])
def save_config_api():
    """Save configuration"""
    try:
        config = request.get_json()
        save_config(config)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/get-config')
def get_config_api():
    """Get current configuration"""
    try:
        config = load_config()
        return jsonify(config)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/status')
def get_status():
    """Get system status"""
    try:
        import subprocess
        import os
        
        # Check if collector is running
        try:
            result = subprocess.run(['pgrep', '-f', 'collector_simple.py'], 
                                  capture_output=True, text=True)
            collector_running = bool(result.stdout.strip())
        except:
            collector_running = False
        
        # Get log file info
        log_info = "No log file"
        if os.path.exists('collector.log'):
            stat = os.stat('collector.log')
            import time
            log_info = f"Last modified: {time.ctime(stat.st_mtime)}"
        
        config = load_config()
        
        return jsonify({
            "collector_running": collector_running,
            "log_info": log_info,
            "config": config
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)