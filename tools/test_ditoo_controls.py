#!/usr/bin/env python3
"""
Test whether Divoom Ditoo physical keyboard / lever generates BLE notifications.
Connects to DitooPro-Light, enables GATT notification on RX characteristic,
and logs any incoming packets.
"""
import asyncio
import sys
from bleak import BleakClient

BLE_ADDRESS = "B1:21:81:5B:E3:16"
BLE_CHAR_RX = "49535343-1e4d-4bd9-ba61-23c647249616"
BLE_CHAR_TX = "49535343-8841-43f4-a8d4-ecbe34729bb3"

packets_received = []

def notification_handler(sender, data: bytearray):
    hex_str = data.hex()
    print(f"[BLE RX] Received from {sender}: {hex_str} (len={len(data)})")
    packets_received.append((sender, bytes(data)))

async def main():
    print(f"Connecting to Ditoo BLE: {BLE_ADDRESS}...")
    async with BleakClient(BLE_ADDRESS, timeout=10.0) as client:
        print(f"Connected! MTU: {client.mtu_size}")
        print(f"Subscribing to notifications on {BLE_CHAR_RX}...")
        try:
            await client.start_notify(BLE_CHAR_RX, notification_handler)
            print("Successfully subscribed to notifications!")
        except Exception as e:
            print(f"Failed to subscribe to notifications: {e}")
            return

        print("Listening for 5 seconds for any unsolicited packets (e.g. keyboard/lever)...")
        await asyncio.sleep(5.0)

        await client.stop_notify(BLE_CHAR_RX)
        print(f"Done. Total packets received: {len(packets_received)}")

if __name__ == "__main__":
    asyncio.run(main())
