#!/usr/bin/env python3
"""
Hardware Detection & Verification for Divoom MiniToo.
Enumerates serial/Bluetooth SPP ports on Windows, prioritizes based on
device metadata (vendor ID 0x05D6, MiniToo/Divoom identifiers, BTHENUM),
and safely probes using read-only SPP frames (0xBD 0x13 Display Channel query).
"""
from __future__ import annotations

import os
import sys
import time
from typing import List, Dict, Tuple, Optional


try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

from inputs import frame_spp, extract_packets


def get_all_com_ports() -> List[Dict[str, str]]:
    """Return all available COM ports with device info."""
    if serial is None:
        return []
    ports = []
    for p in serial.tools.list_ports.comports():
        ports.append({
            "device": p.device,
            "description": p.description or "",
            "hwid": p.hwid or "",
            "manufacturer": p.manufacturer or "",
        })
    return ports


def probe_divoom_device(port_name: str, timeout: float = 0.15) -> bool:
    """
    Safely probe a serial port using the read-only 0xBD 0x13 (Display Channel query).
    Returns True if a valid Divoom SPP response is received.
    """
    if serial is None:
        return False
    try:
        ser = serial.Serial(port_name, 115200, timeout=timeout, write_timeout=0.25)
        time.sleep(0.12)
        if ser.in_waiting:
            ser.read(ser.in_waiting)

        # Send safe read-only channel query: 0xBD 0x13
        ser.write(frame_spp(0xBD, bytes([0x13])))
        ser.flush()

        t0 = time.time()
        buf = bytearray()
        while time.time() - t0 < timeout:
            if ser.in_waiting:
                buf.extend(ser.read(ser.in_waiting))
                pkts = extract_packets(bytes(buf))
                for cmd, body in pkts:
                    if cmd in (0xBD, 0x09, 0x13, 0x04):
                        ser.close()
                        return True
            time.sleep(0.01)

        ser.close()
        return False
    except Exception:
        return False


def detect_minitoo_port(preferred_port: Optional[str] = "AUTO") -> Optional[str]:
    """
    Auto-detect and verify the Divoom MiniToo Bluetooth COM port.
    
    Logic:
    1. If a specific valid COM port is preferred (not 'AUTO'), probe that port first.
       If it responds, return it.
    2. Enumerate ports and score candidates based on device metadata:
       - Score 100: "MiniToo" or "Divoom" in description
       - Score 90: "05D6" (Divoom USB/BT Vendor ID) in HWID
       - Score 50: Bluetooth serial link (BTHENUM)
       - Score 10: other COM ports
    3. Probe top candidates in descending score order.
    4. Return first verified device or None if no device responds.
    """
    if serial is None:
        return None

    # Step 1: Check explicitly requested port if not AUTO
    if preferred_port and preferred_port.upper() != "AUTO":
        p_name = preferred_port.strip().upper()
        if probe_divoom_device(p_name):
            return p_name
        # If explicitly specified port couldn't be probed (e.g. disconnected or busy),
        # return it anyway so controller can retry it, or proceed to auto-detect.

    all_ports = list(serial.tools.list_ports.comports())
    scored: List[Tuple[int, str]] = []

    for p in all_ports:
        score = 0
        desc = (p.description or "").lower()
        hwid = (p.hwid or "").upper()

        if "minitoo" in desc or "divoom" in desc:
            score += 100
        if "05D6" in hwid:
            score += 90
        if "BTHENUM" in hwid:
            score += 50
        else:
            score += 10

        scored.append((score, p.device))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)

    # Step 2: Probe candidate ports (focusing on Bluetooth candidates first)
    for score, dev in scored:
        if score >= 50:  # Only probe Bluetooth SPP / Divoom candidates
            if probe_divoom_device(dev):
                return dev

    # Step 3: If probe couldn't verify (e.g. device sleeping or RFCOMM delay),
    # return the highest-scoring candidate if score >= 90
    if scored and scored[0][0] >= 90:
        return scored[0][1]

    return None


def open_windows_bluetooth_settings() -> bool:
    """Launch Windows Bluetooth Settings screen directly."""
    try:
        os.system("start ms-settings:bluetooth")
        return True
    except Exception:
        return False


def detect_minitoo_connection_state(preferred_port: Optional[str] = "AUTO") -> Tuple[str, Optional[str]]:
    """
    Evaluate MiniToo hardware connection state:
    Returns (status, port_or_detail):
    - ("FOUND", port): device verified or strong port detected
    - ("PAIRING REQUIRED", None): Bluetooth exists but no MiniToo SPP service paired
    - ("NOT FOUND", None): No serial or Bluetooth devices available
    """
    port = detect_minitoo_port(preferred_port)
    if port:
        return ("FOUND", port)

    if serial is not None:
        all_ports = list(serial.tools.list_ports.comports())
        has_bt = any("BTHENUM" in (p.hwid or "").upper() for p in all_ports)
        if has_bt:
            return ("PAIRING REQUIRED", None)

    return ("NOT FOUND", None)

