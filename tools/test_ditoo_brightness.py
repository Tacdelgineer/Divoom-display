import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from bleak import BleakClient
from src.devices.ditoo import frame_spp

async def main():
    client = BleakClient("B1:21:81:5B:E3:16", timeout=8.0)
    await client.connect()
    print("Connected!")
    # Test brightness 100%
    pkt100 = frame_spp(0x74, bytes([100]))
    await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", pkt100, response=False)
    print("Sent brightness 100")
    await asyncio.sleep(1.0)
    # Test brightness 50%
    pkt50 = frame_spp(0x74, bytes([50]))
    await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", pkt50, response=False)
    print("Sent brightness 50")
    await asyncio.sleep(1.0)
    # Restore brightness 100%
    await client.write_gatt_char("49535343-8841-43f4-a8d4-ecbe34729bb3", pkt100, response=False)
    print("Restored brightness 100")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
