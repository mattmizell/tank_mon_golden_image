from veeder_root_tls_socket_library.socket import TlsSocket
import re

def parse_tank_response(response):
    """Parses a single I201XX response string into a dict"""
    pattern = re.compile(
        r"^\s*(\d+)\s+([A-Z0-9 ]+?)\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)$",
        re.MULTILINE
    )
    match = pattern.search(response)
    if match:
        return {
            "id": int(match.group(1)),
            "product": match.group(2).strip(),
            "volume": int(match.group(3)),
            "tc_volume": int(match.group(4)),
            "ullage": int(match.group(5)),
            "height": float(match.group(6)),
            "water": float(match.group(7)),
            "temp": float(match.group(8))
        }
    return None


def get_tank_levels(ip_address='127.0.0.1', port=10001):
    print(f"🟢 Connecting to Veeder Root at {ip_address}:{port}...")
    tls = TlsSocket(ip_address, port)
    tank_data = []

    for tank_num in range(1, 7):
        tank_id = f"{tank_num:02}"
        command = f"I201{tank_id}"
        print(f"➡️ Sending command: {command} to {tank_num}")
        try:
            response = tls.execute(command)
            print(f"⬅️ Response:\n{response}")
            tank = parse_tank_response(response)
            if tank:
                print(f"✅ Parsed: {tank}")
                tank_data.append(tank)
            else:
                print("⚠️ No match in response")
        except Exception as e:
            print(f"❌ Error querying Tank {tank_id}: {e}")

    return tank_data


if __name__ == "__main__":
    from pprint import pprint
    pprint(get_tank_levels())

def get_tank_inventory():
    return [
        {"number": "1", "product": "Unleaded", "tc_volume": 3563},
        {"number": "2", "product": "Diesel", "tc_volume": 4172}
    ]
