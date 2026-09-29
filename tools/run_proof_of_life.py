import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath("."))
from src.devices.ditoo import DitooDevice

async def main():
    device = DitooDevice()
    print("Initiating connection to Ditoo...")
    ok = await device.connect()
    if not ok:
        print("[FAIL] Could not connect to Ditoo over BLE or Serial.")
        sys.exit(1)
        
    print("[SUCCESS] Connected to Ditoo!")
    await device.run_proof_of_life()
    await device.disconnect()
    print("Disconnected.")

if __name__ == "__main__":
    asyncio.run(main())
