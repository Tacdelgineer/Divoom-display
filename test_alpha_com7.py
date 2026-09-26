#!/usr/bin/env python3
"""
Test sending an image to Divoom MiniToo via COM7 using the verified 160x128 JPEG protocol.
"""
import io
import time
import serial
from PIL import Image, ImageDraw

try:
    from detector import detect_minitoo_port
    MINITOO_PORT = detect_minitoo_port()
except Exception:
    MINITOO_PORT = None
CHUNK_SIZE = 256
CMD_APP_NEW_GIF_CMD2020 = 0x8B

def u16le(n: int) -> bytes: return n.to_bytes(2, "little")
def u32le(n: int) -> bytes: return n.to_bytes(4, "little")

def build_packet(cmd: int, data: bytes = b"") -> bytes:
    total = 1 + 2 + 1 + len(data) + 2 + 1
    length_field = total - 4
    packet = bytearray(total)
    packet[0] = 0x01
    packet[1] = length_field & 0xFF
    packet[2] = (length_field >> 8) & 0xFF
    packet[3] = cmd & 0xFF
    packet[4 : 4 + len(data)] = data
    checksum = 0
    for i in range(1, total - 2):
        checksum = (checksum + packet[i]) & 0xFFFF
    packet[-3] = checksum & 0xFF
    packet[-2] = (checksum >> 8) & 0xFF
    packet[-1] = 0x02
    return bytes(packet)

def hex_dump(data: bytes, max_bytes: int = 32) -> str:
    if len(data) <= max_bytes:
        return " ".join(f"{b:02x}" for b in data)
    shown = " ".join(f"{b:02x}" for b in data[:max_bytes])
    return f"{shown} ... ({len(data)}B)"

def read_response(ser: serial.Serial, timeout: float = 3.0) -> bytes | None:
    deadline = time.monotonic() + timeout
    buf = bytearray()
    while time.monotonic() < deadline:
        if ser.in_waiting:
            chunk = ser.read(ser.in_waiting)
            buf.extend(chunk)
            # Find frame starting with 0x01
            while len(buf) >= 7:
                if buf[0] != 0x01:
                    idx = buf.find(b"\x01")
                    if idx == -1:
                        buf.clear()
                        break
                    buf = buf[idx:]
                if len(buf) < 4:
                    break
                pkt_len = buf[1] | (buf[2] << 8)
                expected_total = pkt_len + 4
                if len(buf) >= expected_total:
                    return bytes(buf[:expected_total])
        time.sleep(0.01)
    return bytes(buf) if buf else None

def encode_image_payload(img: Image.Image, jpeg_quality: int = 85) -> bytes:
    if img.size != (160, 128):
        img = img.resize((160, 128), Image.Resampling.LANCZOS)
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    jpeg_data = buf.getvalue()

    header = bytes([
        0x23,        # LCD frame marker
        0x01,        # 1 frame
        0x00, 0x00,  # speed = 0
        0x08,        # tile rows = 8 (160 // 20)
        0x0A,        # tile cols = 10 (128 // ~13)
    ])
    frame = bytes([0x01]) + len(jpeg_data).to_bytes(4, "big") + jpeg_data
    return header + frame

def build_chunks(payload: bytes) -> list[bytes]:
    chunks = []
    total_len = len(payload)
    num_chunks = (total_len + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(num_chunks):
        offset = i * CHUNK_SIZE
        chunk_data = payload[offset : offset + CHUNK_SIZE]
        inner = bytes([0x01]) + total_len.to_bytes(4, "little") + i.to_bytes(2, "little") + chunk_data
        chunks.append(build_packet(CMD_APP_NEW_GIF_CMD2020, inner))
    return chunks

def send_image_to_minitoo(port: str, img: Image.Image, jpeg_quality: int = 85) -> bool:
    payload = encode_image_payload(img, jpeg_quality)
    print(f"Encoded payload: {len(payload)} bytes (JPEG q={jpeg_quality})")
    chunks = build_chunks(payload)
    print(f"Split into {len(chunks)} chunks of {CHUNK_SIZE} bytes")

    with serial.Serial(port, baudrate=115200, timeout=0.1) as ser:
        time.sleep(0.4)
        if ser.in_waiting:
            stale = ser.read(ser.in_waiting)
            print(f"Flushed stale buffer: {stale.hex()}")

        # START packet
        start_data = bytes([0x00]) + len(payload).to_bytes(4, "little") + bytes([0x00])
        start_pkt = build_packet(CMD_APP_NEW_GIF_CMD2020, start_data)
        print(f"TX START: {hex_dump(start_pkt)}")
        ser.write(start_pkt)
        ser.flush()

        print("Waiting for device response to START...")
        resp = read_response(ser, timeout=4.0)
        if not resp:
            print("No response to START! Sending all chunks blindly...")
            for i, chunk in enumerate(chunks):
                ser.write(chunk)
                ser.flush()
                time.sleep(0.02)
        else:
            print(f"RX response ({len(resp)}B): {hex_dump(resp)}")
            for idx, b in enumerate(resp):
                print(f"  [{idx:2d}] 0x{b:02x}")
            if len(resp) > 6:
                ctrl = resp[6]
                if ctrl == 0x00:
                    print("Device confirmed: SEND ALL")
                    for i, chunk in enumerate(chunks):
                        ser.write(chunk)
                        ser.flush()
                        time.sleep(0.02)
                        if (i + 1) % 5 == 0 or i == len(chunks) - 1:
                            print(f"  Sent chunk {i+1}/{len(chunks)}")
                elif ctrl == 0x01:
                    req_idx = int.from_bytes(resp[7:11], "little") if len(resp) > 10 else 0
                    print(f"Device requested chunk {req_idx}")
                    if 0 <= req_idx < len(chunks):
                        ser.write(chunks[req_idx])
                        ser.flush()
                    # Resend rest
                    for i, chunk in enumerate(chunks):
                        ser.write(chunk)
                        ser.flush()
                        time.sleep(0.02)
                else:
                    print(f"Unknown ctrl 0x{ctrl:02x}, sending all chunks...")
                    for chunk in chunks:
                        ser.write(chunk)
                        ser.flush()
                        time.sleep(0.02)

        print("Waiting for final confirmation...")
        final = read_response(ser, timeout=2.0)
        if final:
            print(f"Final confirmation: {hex_dump(final)}")
        else:
            print("(No final packet, transfer finished)")
    return True

if __name__ == "__main__":
    # Create high-contrast test image
    img = Image.new("RGB", (160, 128), (0, 30, 80)) # Dark blue
    draw = ImageDraw.Draw(img)
    # Bright cyan border
    draw.rectangle([2, 2, 157, 125], outline=(0, 255, 255), width=3)
    # Bright text
    draw.text((25, 20), "AI DASHBOARD", fill=(255, 200, 0))
    draw.text((40, 50), "ONLINE", fill=(0, 255, 100))
    draw.text((20, 80), "BTC: $89,450", fill=(255, 255, 255))
    draw.text((30, 105), "CODEX: ACTIVE", fill=(0, 200, 255))

    img.save("test_dashboard_160x128.png")
    print("Saved test_dashboard_160x128.png")
    send_image_to_minitoo(MINITOO_PORT, img)
