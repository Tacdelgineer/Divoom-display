import sys
import os
import asyncio
import time
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from bleak import BleakScanner, BleakClient
from src.devices.ditoo import (
    frame_spp,
    build_solid_color_packet,
    encode_16x16_frame,
    build_0x8b_packets,
    BLE_SERVICE_UUID,
    BLE_CHAR_TX,
    BLE_CHAR_RX,
)

PREV_ADDRESS = "B1:21:81:5B:E3:16"

async def run_diagnostic():
    print("[1/6] Scanning for Bluetooth Low Energy peripherals (timeout=5s)...")
    discovered_devices = await BleakScanner.discover(timeout=5.0, return_adv=True)
    
    target_device = None
    target_adv = None
    
    print(f"Total BLE devices detected: {len(discovered_devices)}")
    for d, adv in discovered_devices.values():
        name = d.name or adv.local_name or "Unknown"
        # Check if name contains Ditoo or Light, or if ISSC service UUID is advertised
        has_issc = BLE_SERVICE_UUID.lower() in [u.lower() for u in adv.service_uuids]
        if "ditoo" in name.lower() or "light" in name.lower() or has_issc or d.address.upper() == PREV_ADDRESS.upper():
            print(f" -> MATCH CANDIDATE: '{name}' | Address: {d.address} | RSSI: {adv.rssi} dBm | Services: {adv.service_uuids}")
            if "ditoopro-light" in name.lower() or has_issc or d.address.upper() == PREV_ADDRESS.upper():
                target_device = d
                target_adv = adv

    if not target_device:
        # Fallback: check if any device matches Ditoo in name
        for d, adv in discovered_devices.values():
            name = d.name or adv.local_name or ""
            if "ditoo" in name.lower():
                target_device = d
                target_adv = adv
                break

    if not target_device:
        print("[ERROR] 'DitooPro-Light' was NOT detected in BLE scan!")
        print("Please check: Is the Ditoo powered ON and within Bluetooth range?")
        return False, None, None, None, False

    target_name = target_device.name or (target_adv.local_name if target_adv else "Unknown")
    target_addr = target_device.address
    target_rssi = target_adv.rssi if target_adv else "N/A"
    addr_changed = (target_addr.upper() != PREV_ADDRESS.upper())
    
    print("\n--- SCAN REPORT ---")
    print(f"Discovered Name   : {target_name}")
    print(f"Current Address   : {target_addr}")
    print(f"RSSI              : {target_rssi} dBm")
    print(f"Address Changed?  : {'YES (changed from ' + PREV_ADDRESS + ')' if addr_changed else 'NO (matches ' + PREV_ADDRESS + ')'}")
    print("-------------------\n")

    # Step 2: Connect using discovered BLEDevice object
    print(f"[2/6] Connecting to {target_name} ({target_addr}) using Bleak BLEDevice object...")
    client = BleakClient(target_device, timeout=10.0)
    try:
        await client.connect()
    except Exception as e:
        print(f"[ERROR] Failed to connect to {target_addr}: {e}")
        # Try fallback using address string directly
        print(f"Retrying connection using address string '{target_addr}'...")
        client = BleakClient(target_addr, timeout=10.0)
        try:
            await client.connect()
        except Exception as e2:
            print(f"[ERROR] Fallback connection failed: {e2}")
            return True, target_name, target_addr, target_rssi, False

    print(f"[SUCCESS] Connected! MTU size: {client.mtu_size}")

    # Step 3: Enumerate services and characteristics
    print("[3/6] Enumerating GATT services & characteristics...")
    service_found = False
    tx_found = False
    rx_found = False

    for service in client.services:
        is_issc = (service.uuid.lower() == BLE_SERVICE_UUID.lower())
        if is_issc:
            service_found = True
        print(f"  Service: {service.uuid} {'[ISSC TRANSPARENT UART]' if is_issc else ''}")
        for char in service.characteristics:
            is_tx = (char.uuid.lower() == BLE_CHAR_TX.lower())
            is_rx = (char.uuid.lower() == BLE_CHAR_RX.lower())
            if is_tx:
                tx_found = True
            if is_rx:
                rx_found = True
            flags = ",".join(char.properties)
            marker = " <- [TX WRITE]" if is_tx else (" <- [RX NOTIFY]" if is_rx else "")
            print(f"    Char: {char.uuid} ({flags}){marker}")

    print("\n--- GATT VERIFICATION ---")
    print(f"Service {BLE_SERVICE_UUID} found: {service_found}")
    print(f"TX Char {BLE_CHAR_TX} found: {tx_found}")
    print(f"RX Char {BLE_CHAR_RX} found: {rx_found}")
    print("-------------------------\n")

    if not tx_found:
        print("[ERROR] TX characteristic was not found on connected device!")
        await client.disconnect()
        return True, target_name, target_addr, target_rssi, False

    # Step 4: Set Brightness to 100%
    print("[4/6] Setting screen brightness to 100% via Command 0x74...")
    pkt_bright = frame_spp(0x74, bytes([100]))
    await client.write_gatt_char(BLE_CHAR_TX, pkt_bright, response=False)
    await asyncio.sleep(0.2)

    # Step 5: Send RED display data
    print("[5/6] Sending RED frame to physical Ditoo display...")
    # First: Command 0x45 Solid Color Red
    pkt_solid_red = build_solid_color_packet(255, 0, 0, 100)
    await client.write_gatt_char(BLE_CHAR_TX, pkt_solid_red, response=False)
    await asyncio.sleep(0.2)

    # Second: Command 0x8B 16x16 Pure Red Image
    red_img = Image.new("RGB", (16, 16), (255, 0, 0))
    frame_bytes = encode_16x16_frame(red_img, delay_ms=0)
    packets = build_0x8b_packets(frame_bytes)
    print(f"  Streaming {len(packets)} Command 0x8B packets for 16x16 RED image...")
    for idx, pkt in enumerate(packets):
        await client.write_gatt_char(BLE_CHAR_TX, pkt, response=False)
        if idx == 0:
            await asyncio.sleep(0.12)
        else:
            await asyncio.sleep(0.04)

    print("[SUCCESS] All RED frame packets successfully transmitted to Ditoo!")

    # Step 6: Hold connection open for 15 seconds so user can visually verify
    print("[6/6] Holding connection open for 15 seconds to allow physical confirmation...")
    await asyncio.sleep(15.0)

    print("Disconnecting cleanly...")
    await client.disconnect()
    print("Disconnected.")
    return True, target_name, target_addr, target_rssi, True

if __name__ == "__main__":
    found, name, addr, rssi, sent = asyncio.run(run_diagnostic())
    sys.exit(0 if (found and sent) else 1)
