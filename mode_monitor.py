#!/usr/bin/env python3
"""
Mode & State Monitor for Divoom MiniToo on COM7.
Polls GET_WORK_MODE (0x13), GET_LIGHT_MODE (0x46), EXT 0x13 (Channel query),
GET_VOL (0x09), and LIGHT_CURRENT_LEVEL (0x31) in real-time.
Logs state changes as the user physically switches modes on the MiniToo.
"""
import sys
import time
import serial

try:
    from detector import detect_minitoo_port
    MINITOO_PORT = detect_minitoo_port()
except Exception:
    MINITOO_PORT = None

def u16le(n: int) -> bytes: return n.to_bytes(2, "little")

def frame(cmd: int, body: bytes = b"") -> bytes:
    out = bytearray(7 + len(body))
    out[0] = 0x01
    decl = len(out) - 4
    out[1:3] = u16le(decl)
    out[3] = cmd & 0xFF
    out[4:4+len(body)] = body
    chk = sum(out[1:len(out)-3]) & 0xFFFF
    out[-3:-1] = u16le(chk)
    out[-1] = 0x02
    return bytes(out)

def parse_packets(raw: bytes) -> list[tuple[int, int, bytes]]:
    """Parse Divoom 0x01 ... 0x02 packets. Returns list of (cmd, ack, payload)."""
    packets = []
    buf = bytearray(raw)
    while len(buf) >= 7:
        if buf[0] != 0x01:
            idx = buf.find(b"\x01")
            if idx == -1:
                break
            buf = buf[idx:]
        if len(buf) < 4:
            break
        pkt_len = buf[1] | (buf[2] << 8)
        total_len = pkt_len + 4
        if len(buf) < total_len:
            break
        pkt = bytes(buf[:total_len])
        del buf[:total_len]

        cmd = pkt[3]
        inner_cmd = pkt[4] if len(pkt) > 4 else 0
        ack = pkt[5] if len(pkt) > 5 else 0
        payload = pkt[6:-3] if len(pkt) > 9 else b""
        packets.append((inner_cmd if cmd == 0x04 else cmd, ack, payload))
    return packets

def run_monitor(duration: float = 30.0):
    print("=" * 65)
    print("  DIVOOM MINITOO DISPLAY MODE & STATE MONITOR")
    print(f"  Target: {MINITOO_PORT} | Duration: {duration}s")
    print("=" * 65)
    print("Instructions:")
    print("  Please manually switch between on the MiniToo:")
    print("  1. CLOCK display")
    print("  2. ALBUM mode (if available)")
    print("  3. PIXEL ART / DIY mode")
    print("  4. MUSIC VISUALIZER")
    print("  5. Rotate knob or press mode buttons\n")

    try:
        ser = serial.Serial(MINITOO_PORT, baudrate=115200, timeout=0.05)
    except serial.SerialException as e:
        print(f"Error opening {MINITOO_PORT}: {e}")
        return

    last_work_mode = None
    last_ext13 = None
    last_vol = None
    last_light = None

    start_time = time.time()
    try:
        with ser:
            time.sleep(0.3)
            if ser.in_waiting:
                ser.read(ser.in_waiting)

            while time.time() - start_time < duration:
                # 1. Query EXT 0x13 (Display channel)
                ser.write(frame(0xBD, bytes([0x13])))
                ser.flush()
                time.sleep(0.04)

                # 2. Query 0x13 (Audio Work Mode)
                ser.write(frame(0x13))
                ser.flush()
                time.sleep(0.04)

                # 3. Query 0x09 (Volume)
                ser.write(frame(0x09))
                ser.flush()
                time.sleep(0.04)

                # 4. Query 0x31 (Light Level)
                ser.write(frame(0x31))
                ser.flush()
                time.sleep(0.04)

                # Read responses
                raw = ser.read(ser.in_waiting)
                pkts = parse_packets(raw)

                changed = False
                ts = time.strftime("%H:%M:%S") + f".{int(time.time()*1000)%1000:03d}"

                for cmd, ack, data in pkts:
                    if cmd == 0xBD and len(data) >= 3:
                        ext_sub = data[0]
                        if ext_sub == 0x13 and len(data) >= 3:
                            val = data[2]
                            if val != last_ext13:
                                last_ext13 = val
                                changed = True
                    elif cmd == 0x13:
                        val = data[0] if data else 0
                        if val != last_work_mode:
                            last_work_mode = val
                            changed = True
                    elif cmd == 0x09:
                        val = data[0] if data else 0
                        if val != last_vol:
                            last_vol = val
                            changed = True
                    elif cmd == 0x31:
                        val = data[0] if data else 0
                        if val != last_light:
                            last_light = val
                            changed = True

                if changed or (time.time() - start_time < 0.5 and last_work_mode is not None):
                    work_mode_names = {0: "Bluetooth", 1: "FM", 2: "LineIn", 3: "SD Card", 4: "USB", 7: "UAC"}
                    channel_names = {0: "Clock", 1: "NightLight", 2: "Cloud", 3: "VJ", 4: "MusicEQ", 5: "Custom/DIY"}
                    wm_str = work_mode_names.get(last_work_mode, f"0x{last_work_mode:02X}" if last_work_mode is not None else "?")
                    ch_str = channel_names.get(last_ext13, f"0x{last_ext13:02X}" if last_ext13 is not None else "?")
                    print(f"[{ts}] Channel/EXT13: {ch_str} ({last_ext13}) | Audio WorkMode: {wm_str} ({last_work_mode}) | Vol: {last_vol} | Brightness: {last_light}")

                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == "__main__":
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 30.0
    run_monitor(dur)
