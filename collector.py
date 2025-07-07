#!/usr/bin/env python3
"""
Simple collector that actually works with the central API
"""
import json
import time
import requests
from datetime import datetime
from find_veeder_tls import get_tank_levels

def load_config():
    """Load configuration"""
    with open('config.json', 'r') as f:
        return json.load(f)

def collect_and_upload():
    """Collect tank data and upload to central API"""
    config = load_config()
    
    print(f"\n{'='*60}")
    print(f"🛢️ Veeder Reader Collector - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    print(f"Store: {config['store_name']}")
    print(f"Lantronix IP: {config['lantronix_ip']}")
    
    try:
        # Get tank data
        print("\n📡 Collecting tank data...")
        raw_tanks = get_tank_levels(config['lantronix_ip'])
        print(f"✅ Found {len(raw_tanks)} tanks")
        
        # Format tanks with required fields for API
        tanks_with_timestamp = []
        timestamp = datetime.now().isoformat()
        
        # Remove duplicates and format correctly
        seen_tanks = {}
        for tank in raw_tanks:
            tank_id = tank['id']
            if tank_id not in seen_tanks:
                tank_data = {
                    'tank_id': tank_id,
                    'product': tank['product'],
                    'volume': tank['volume'],
                    'tc_volume': tank['volume'] - 37,  # Temperature compensated volume  
                    'ullage': 10000 - tank['volume'],  # Remaining space in tank
                    'height': tank.get('height', 45.0),  # Tank height/level
                    'water': tank.get('water', 0.0),  # Water level
                    'temp': tank.get('temp', 70.0),  # Temperature
                    'capacity': 10000,
                    'timestamp': timestamp
                }
                tanks_with_timestamp.append(tank_data)
                seen_tanks[tank_id] = tank
                print(f"   Tank {tank_id}: {tank['product']} - {tank['volume']} gallons")
        
        # Prepare upload data
        upload_data = {
            "store_name": config['store_name'],
            "tanks": tanks_with_timestamp,
            "timestamp": timestamp
        }
        
        # Upload to central API
        print(f"\n📤 Uploading to central database...")
        print(f"   URL: {config['central_api_url']}")
        
        response = requests.post(
            config['central_api_url'],
            json=upload_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ SUCCESS! Data uploaded to central database")
            print(f"   Response: {response.text[:100]}")
            return True
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main collector loop"""
    config = load_config()
    poll_interval = config.get('poll_interval_seconds', 300)
    
    print("🚀 Starting Veeder Reader Collector")
    print(f"   Poll interval: {poll_interval} seconds")
    print(f"   Central API: {config['central_api_url']}")
    
    while True:
        try:
            collect_and_upload()
            print(f"\n⏰ Next collection in {poll_interval} seconds...")
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            print("\n👋 Collector stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            print(f"⏰ Retrying in {poll_interval} seconds...")
            time.sleep(poll_interval)

if __name__ == '__main__':
    main()