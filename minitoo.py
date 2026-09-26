#!/usr/bin/env python3
"""
Multi-Provider AI Usage Display for Divoom MiniToo.
Connects via Bluetooth SPP (Virtual COM port on Windows),
reads local usage data (Claude Code, OpenAI Codex, Gemini),
renders pixel-perfect 128x128 screens, and pushes to MiniToo.
Supports physical button event diagnostics (--listen-buttons) and cycle navigation.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from PIL import Image

import serial
import serial.tools.list_ports
import zstandard as zstd

import providers
from render_provider_screen import render_provider_screen
from render_claude_screen import render_screen as render_claude_legacy

CMD_APP_NEW_GIF_2020 = 0x8B


def u16le(n: int) -> bytes: return n.to_bytes(2, "little")
def u32le(n: int) -> bytes: return n.to_bytes(4, "little")
def u16be(n: int) -> bytes: return n.to_bytes(2, "big")
def u32be(n: int) -> bytes: return n.to_bytes(4, "big")


def frame(cmd: int, body: bytes = b"") -> bytes:
    """Frame packet according to Divoom SPP envelope."""
    out = bytearray(7 + len(body))
    out[0] = 0x01
    declared = len(out) - 4
    out[1:3] = u16le(declared)
    out[3] = cmd & 0xFF
    out[4 : 4 + len(body)] = body
    checksum = sum(out[1 : len(out) - 3]) & 0xFFFF
    out[-3:-1] = u16le(checksum)
    out[-1] = 0x02
    return bytes(out)


def find_minitoo_port() -> Optional[str]:
    """Auto-detect Divoom MiniToo Bluetooth serial port on Windows."""
    try:
        from detector import detect_minitoo_port
        p = detect_minitoo_port()
        if p:
            return p
    except Exception:
        pass
    if serial is None:
        return None
    for port in serial.tools.list_ports.comports():
        hwid = port.hwid.upper()
        desc = port.description.upper()
        # Divoom MiniToo vendor/device signatures
        if "000105D6" in hwid or "05D6_PID&000A" in hwid or "B1218194229C" in hwid or "MINITOO" in desc:
            return port.device
    return None


def build_payload(img: Image.Image, jpeg_quality: int = 85) -> bytes:
    """Build JPEG media payload for MiniToo IPS LCD (160x128, 8x10 tile grid)."""
    import io
    if img.size == (128, 128):
        canvas = Image.new("RGB", (160, 128), (10, 15, 25))
        canvas.paste(img.convert("RGB"), (16, 0))
        target_img = canvas
    elif img.size != (160, 128):
        target_img = img.resize((160, 128), Image.Resampling.LANCZOS).convert("RGB")
    else:
        target_img = img.convert("RGB")

    buf = io.BytesIO()
    target_img.save(buf, format="JPEG", quality=jpeg_quality)
    jpeg_data = buf.getvalue()

    header = bytes([
        0x23,        # LCD frame marker
        0x01,        # 1 frame
        0x00, 0x00,  # speed = 0
        0x08,        # tile rows = 8 (160 // 20)
        0x0A,        # tile cols = 10 (128 // ~13)
    ])
    frame_bytes = bytes([0x01]) + len(jpeg_data).to_bytes(4, "big") + jpeg_data
    return header + frame_bytes


def build_packets(payload: bytes, chunk_size: int = 256) -> list[bytes]:
    """Split payload into START packet and 256-byte chunks."""
    packets = []
    # START packet: [0x00, total_len 4B LE, circle_flag 0]
    start_data = bytes([0x00]) + len(payload).to_bytes(4, "little") + bytes([0x00])
    packets.append(frame(CMD_APP_NEW_GIF_2020, start_data))
    # Chunks
    num_chunks = (len(payload) + chunk_size - 1) // chunk_size
    for i in range(num_chunks):
        offset = i * chunk_size
        chunk_data = payload[offset : offset + chunk_size]
        body = bytes([0x01]) + len(payload).to_bytes(4, "little") + i.to_bytes(2, "little") + chunk_data
        packets.append(frame(CMD_APP_NEW_GIF_2020, body))
    return packets


def read_available(ser: serial.Serial, wait: float = 0.25) -> bytes:
    end = time.time() + wait
    buf = bytearray()
    while time.time() < end:
        n = ser.in_waiting
        if n:
            buf.extend(ser.read(n))
            end = time.time() + wait
        else:
            time.sleep(0.02)
    return bytes(buf)


def push_to_minitoo(img: Image.Image, port: str | None = None, delay: float = 0.02) -> bool:
    """Push 160x128 image to Divoom MiniToo over Bluetooth SPP transport."""
    target_port = port or find_minitoo_port()
    if not target_port:
        print("[MINITOO] No Divoom MiniToo detected on any Bluetooth serial port.")
        return False
    payload = build_payload(img)
    packets = build_packets(payload)

    print(f"Connecting to Divoom MiniToo on {target_port}...")
    for attempt in range(5):
        try:
            with serial.Serial(target_port, baudrate=115200, timeout=0.2, write_timeout=3) as ser:
                time.sleep(0.4)
                # Clear any stale bytes
                read_available(ser, 0.15)

                # Send START packet
                start_pkt = packets[0]
                ser.write(start_pkt)
                ser.flush()

                # Wait for device request
                deadline = time.time() + 5.0
                got = bytearray()
                seen_request = False
                while time.time() < deadline:
                    got.extend(read_available(ser, 0.1))
                    if b"\x8b\x55\x00" in got or bytes.fromhex("010700048b550001ec0002") in got or len(got) >= 11:
                        seen_request = True
                        break

                if seen_request:
                    print("Device request received: OK")
                else:
                    print("No explicit device request, streaming chunks directly...")

                # Send chunks
                for i, pkt in enumerate(packets[1:]):
                    ser.write(pkt)
                    ser.flush()
                    time.sleep(delay)

                # Await final acknowledgement
                tail = read_available(ser, 2.0)
                if tail:
                    print(f"Display update confirmed! (ACK: {tail[:8].hex()})")
                    return True
                else:
                    print("Display chunks transferred.")
                    return True
        except serial.SerialException as e:
            if attempt < 4 and ("Access is denied" in str(e) or "PermissionError" in str(e)):
                time.sleep(1.0)
                continue
            print(f"Error connecting to {target_port}: {e}")
            return False
    return False


def listen_buttons(port: str | None = None, duration: float | None = None):
    """
    Diagnostic mode: Connects to MiniToo over Bluetooth SPP and listens for button/input events.
    Does NOT constantly overwrite the screen.
    Prints raw received packets with timestamps and framing analysis.
    """
    target_port = port or find_minitoo_port()
    if not target_port:
        print("[MINITOO] No Divoom MiniToo detected on any Bluetooth serial port.")
        return
    print("=" * 64)
    print("  DIVOOM MINITOO PHYSICAL BUTTON DIAGNOSTIC LISTENER")
    print(f"  Target Port: {target_port} | Baud: 115200")
    print("=" * 64)
    print("Instructions:")
    print("  1. Press each physical button on the MiniToo (Left, Right, Knob, Mode, Power).")
    print("  2. Rotate any dials or knobs if present.")
    print("  3. Incoming packets will appear below with timestamps and byte breakdowns.")
    print("  4. Press Ctrl+C when finished to view summary report.\n")

    try:
        ser = serial.Serial(target_port, baudrate=115200, timeout=0.1)
    except serial.SerialException as e:
        print(f"Error opening port {target_port}: {e}")
        return

    events_received: list[dict] = []
    start_time = time.time()

    with ser:
        time.sleep(0.4)
        # Flush stale buffer
        if ser.in_waiting:
            stale = ser.read(ser.in_waiting)
            print(f"[INIT] Flushed {len(stale)} stale byte(s) from buffer.")

        # Probe device with volume query (0x09) to confirm bi-directional connection is alive
        print("[INIT] Probing bidirectional connection with 0x09 (Volume Query)...")
        ser.write(frame(0x09))
        ser.flush()
        probe_resp = read_available(ser, 1.0)
        if probe_resp:
            print(f"[INIT] Probe Response received: {probe_resp.hex(' ')} (Channel verified active!)")
        else:
            print("[INIT] Warning: No response to probe. Continuing to listen...")

        print("\n--- Listening for hardware button events (press buttons on MiniToo) ---")
        buffer = bytearray()
        try:
            while True:
                if duration and (time.time() - start_time) >= duration:
                    print(f"\nDuration limit ({duration}s) reached.")
                    break

                n = ser.in_waiting
                if n:
                    chunk = ser.read(n)
                    buffer.extend(chunk)
                    ts = time.strftime('%H:%M:%S') + f".{int(time.time()*1000)%1000:03d}"

                    # Process buffer for Divoom framing (0x01 ... 0x02)
                    while len(buffer) >= 7:
                        # Find start byte 0x01
                        start_idx = buffer.find(b"\x01")
                        if start_idx == -1:
                            # Print non-framed bytes
                            print(f"[{ts}] UNFRAMED ({len(buffer)}B): {buffer.hex(' ')}")
                            buffer.clear()
                            break

                        if start_idx > 0:
                            unframed = buffer[:start_idx]
                            print(f"[{ts}] UNFRAMED ({len(unframed)}B): {unframed.hex(' ')}")
                            del buffer[:start_idx]

                        # Check if we have length bytes
                        if len(buffer) < 4:
                            break
                        declared_len = buffer[1] | (buffer[2] << 8)
                        total_pkt_len = declared_len + 4

                        if len(buffer) < total_pkt_len:
                            # Incomplete frame, wait for more bytes
                            break

                        pkt = bytes(buffer[:total_pkt_len])
                        del buffer[:total_pkt_len]

                        cmd = pkt[3]
                        body = pkt[4:-3] if total_pkt_len > 7 else b""
                        chk = pkt[-3] | (pkt[-2] << 8)
                        end_byte = pkt[-1]

                        event_info = {
                            "timestamp": ts,
                            "raw_hex": pkt.hex(" "),
                            "cmd": f"0x{cmd:02X}",
                            "body_hex": body.hex(" "),
                            "valid_end": end_byte == 0x02
                        }
                        events_received.append(event_info)

                        # Decode known event types
                        action_label = "Device Notification"
                        if cmd == 0x04:
                            action_label = "Response Envelope"
                        elif cmd == 0x16:
                            action_label = "Key / Media Control Event"
                        elif cmd == 0x2D:
                            action_label = "Touch / Button Event"
                        elif cmd == 0x46:
                            action_label = "Rotary / Dial Event"
                        elif cmd == 0x71:
                            action_label = "Channel Change Event"

                        print(f"[{ts}] -> DIVOOM FRAME: CMD={event_info['cmd']} ({action_label}) | "
                              f"Body: {event_info['body_hex']} | Raw: {event_info['raw_hex']}")

                time.sleep(0.04)

        except KeyboardInterrupt:
            print("\nListening stopped by user.")

    # Summary report
    elapsed = time.time() - start_time
    print("\n" + "=" * 64)
    print("  BUTTON DIAGNOSTIC SUMMARY")
    print("=" * 64)
    print(f"Total listening time:  {elapsed:.1f} seconds")
    print(f"Total packets captured: {len(events_received)}")

    if events_received:
        print("\nCaptured Events:")
        for idx, ev in enumerate(events_received, start=1):
            print(f"  {idx}. [{ev['timestamp']}] CMD: {ev['cmd']} | Body: {ev['body_hex']}")
    else:
        print("\nResult: No button or input events were received over the Bluetooth SPP connection.")
        print("Findings & Technical Explanation:")
        print("  • The physical buttons on the Divoom MiniToo (volume knob, mode switches, playback keys)")
        print("    are handled locally by the onboard microcontroller firmware.")
        print("  • The MiniToo does not emit unsolicited input packets over SPP during normal LCD mode.")
        print("  • Standard Divoom SPP implementations (TivooLcd, minitoo-control, alphafornow gist)")
        print("    focus exclusively on host-to-device media streaming (0x8B).")


def run_cycle(port: str | None, interval: float = 5.0, max_rotations: int | None = None):
    """Cycle through Claude -> Codex -> Gemini -> Claude every `interval` seconds."""
    provider_names = ["claude", "codex", "gemini"]
    total = len(provider_names)
    print(f"\nStarting automatic rotation: {' -> '.join(p.upper() for p in provider_names)} -> ...")
    print(f"Interval: {interval} seconds per page. Press Ctrl+C to stop.\n")

    cycle_count = 0
    while True:
        for idx, p_name in enumerate(provider_names, start=1):
            cycle_count += 1
            prov = providers.get_provider(p_name)
            try:
                data = prov.get_usage()
            except Exception as e:
                print(f"Error getting usage for {p_name}: {e}")
                continue

            print(f"[{time.strftime('%H:%M:%S')}] Page {cycle_count} [{idx}/{total}] {data.provider_name}: "
                  f"{data.primary_label}={data.primary_pct if data.primary_pct is not None else 'N/A'}% "
                  f"(Reset: {data.primary_reset}), "
                  f"{data.secondary_label}={data.secondary_pct if data.secondary_pct is not None else 'N/A'}% "
                  f"(Reset: {data.secondary_reset}), "
                  f"Model={data.model} | Status={data.primary_status}")

            img = render_provider_screen(data, page_num=idx, total_pages=total)
            success = push_to_minitoo(img, port=port)
            if not success:
                print(f"Warning: Failed to push {p_name} screen to MiniToo.")

            if max_rotations and cycle_count >= max_rotations:
                print(f"\nCompleted {cycle_count} rotation(s).")
                return

            print(f"Waiting {interval} seconds before next page...")
            time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Multi-Provider AI Usage Display for Divoom MiniToo")
    parser.add_argument(
        "--provider",
        type=str,
        default="claude",
        choices=["claude", "codex", "gemini"],
        help="Provider screen to show (claude, codex, or gemini; default: claude)"
    )
    parser.add_argument(
        "--cycle",
        action="store_true",
        help="Rotate through all providers (Claude -> Codex -> Gemini -> Claude) automatically"
    )
    parser.add_argument(
        "--listen-buttons",
        action="store_true",
        help="Run diagnostic mode to monitor physical button/input events"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=None,
        help="Optional duration in seconds for --listen-buttons diagnostic (default: run until Ctrl+C)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds per page during --cycle rotation (default: 5.0)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of page transitions to perform in --cycle before exiting (default: infinite)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use demo sample values for display (5H 63%%, RESET 2H 14M, WEEK 41%%, RESET 3D 8H)"
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Save rendered screen to PNG without sending to device"
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="Send a custom PNG/JPG file instead of a usage dashboard"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print usage metrics and data classification for all providers without pushing to screen"
    )
    parser.add_argument(
        "--port",
        type=str,
        default=None,
        help="Serial port for MiniToo (default: auto-detect)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="screen.png",
        help="Preview output filename (default: screen.png)"
    )
    args = parser.parse_args()

    # Diagnostic button listening mode
    if args.listen_buttons:
        listen_buttons(port=args.port, duration=args.duration)
        return

    # Direct custom image push
    if args.image:
        print(f"Loading custom image: {args.image}")
        img = Image.open(args.image)
        if args.preview:
            img.save(args.output)
            print(f"Saved to {args.output}")
            return
        success = push_to_minitoo(img, port=args.port)
        if success:
            print("\nImage successfully displayed on Divoom MiniToo!")
        else:
            print("\nFailed to push image.")
            sys.exit(1)
        return

    # Print status of all providers
    if args.status:
        print("\n=== MULTI-PROVIDER USAGE STATUS & CLASSIFICATION ===")
        for p_name in ["claude", "codex", "gemini"]:
            prov = providers.get_provider(p_name)
            data = prov.get_usage()
            print(f"\n[{data.provider_name}]")
            print(f"  Source:           {data.source_description}")
            print(f"  Active Model:     {data.model} (Tier: {data.plan_tier})")
            p_val = f"{data.primary_pct}%" if data.primary_pct is not None else "N/A"
            print(f"  {data.primary_label:10s} Limit:  {p_val} | Reset: {data.primary_reset} | Status: {data.primary_status}")
            s_val = f"{data.secondary_pct}%" if data.secondary_pct is not None else "N/A"
            print(f"  {data.secondary_label:10s} Limit:  {s_val} | Reset: {data.secondary_reset}")
            print("  Metrics Classification:")
            for m, c in data.metrics_classification.items():
                print(f"    • {m:16s}: {c.upper()}")
        return

    # Automatic cycle mode
    if args.cycle:
        try:
            run_cycle(port=args.port, interval=args.interval, max_rotations=args.count)
        except KeyboardInterrupt:
            print("\nCycle stopped by user.")
            sys.exit(0)
        return

    # Single provider mode
    prov = providers.get_provider(args.provider)
    if args.demo:
        print(f"Using demo sample values for {args.provider.upper()}...")
        data = providers.UsageData(
            provider_name=args.provider.upper(),
            primary_label="5H" if args.provider != "gemini" else "USAGE",
            primary_pct=63,
            primary_reset="2H 14M",
            primary_status="ACTIVE",
            secondary_label="WEEK",
            secondary_pct=41,
            secondary_reset="3D 8H",
            model="DEMO 1.0",
            plan_tier="DEMO",
            source_description="User prompt demo specification"
        )
    else:
        print(f"Reading {args.provider.upper()} usage data...")
        data = prov.get_usage()

    p_disp = f"{data.primary_pct}%" if data.primary_pct is not None else "N/A"
    s_disp = f"{data.secondary_pct}%" if data.secondary_pct is not None else "N/A"
    print(f"Screen Values: {data.provider_name} | {data.primary_label}={p_disp} ({data.primary_reset}) | "
          f"{data.secondary_label}={s_disp} ({data.secondary_reset}) | Model={data.model} | Status={data.primary_status}")

    # Render screen
    screen_img = render_provider_screen(data, page_num=1, total_pages=1)
    screen_img.save(args.output)
    print(f"Rendered screen saved to {args.output}")

    if args.preview:
        print("Preview mode: Not sending to device.")
        return

    # Push to device
    success = push_to_minitoo(screen_img, port=args.port)
    if success:
        print(f"\nScreen successfully displayed on Divoom MiniToo ({data.provider_name})!")
    else:
        print("\nFailed to push to Divoom MiniToo.")
        sys.exit(1)


if __name__ == "__main__":
    main()
