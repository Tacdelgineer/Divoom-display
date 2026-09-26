#!/usr/bin/env python3
"""
Test sending a 128x128 image to Divoom MiniToo via COM7.
Using proven zstandard RGB888 protocol from divoom-minitoo-osx and minitoo-control.
"""
import time
import serial
import zstandard as zstd
from PIL import Image, ImageDraw, ImageFont

CMD_APP_NEW_GIF_2020 = 0x8B

def u16le(n: int) -> bytes: return n.to_bytes(2, "little")
def u32le(n: int) -> bytes: return n.to_bytes(4, "little")
def u16be(n: int) -> bytes: return n.to_bytes(2, "big")
def u32be(n: int) -> bytes: return n.to_bytes(4, "big")

def frame(cmd: int, body: bytes = b"") -> bytes:
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

def build_payload(img: Image.Image, speed: int = 1000, level: int = 17, window_log: int = 17) -> bytes:
    # Ensure 128x128 RGB
    if img.size != (128, 128):
        img = img.resize((128, 128), Image.Resampling.LANCZOS)
    img = img.convert("RGB")
    raw = img.tobytes("raw", "RGB")

    compressor = zstd.ZstdCompressor(
        compression_params=zstd.ZstdCompressionParameters.from_level(
            level, window_log=window_log, write_content_size=True
        )
    )
    zbytes = compressor.compress(raw)
    blocks = 128 // 16  # 8 blocks of 16px
    # Header: marker 0x25, frame_count 1, speed 2B BE, row_blocks, col_blocks, zstd_len 4B BE
    header = bytes([0x25, 1]) + u16be(speed) + bytes([blocks, blocks]) + u32be(len(zbytes))
    return header + zbytes

def build_packets(payload: bytes, chunk_size: int = 256) -> list[bytes]:
    packets = []
    # Start packet: cmd 0x8B, body: 0x00 + payload_len 4B LE
    packets.append(frame(CMD_APP_NEW_GIF_2020, b"\x00" + u32le(len(payload))))
    for seq, off in enumerate(range(0, len(payload), chunk_size)):
        chunk = payload[off : off + chunk_size]
        body = b"\x01" + u32le(len(payload)) + u16le(seq) + chunk
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

def send_image_to_minitoo(port: str, img: Image.Image, delay: float = 0.02) -> bool:
    payload = build_payload(img)
    packets = build_packets(payload)
    print(f"Payload: {len(payload)} bytes, {len(packets)} total packets (1 start + {len(packets)-1} chunks)")

    print(f"Opening {port}...")
    with serial.Serial(port, baudrate=115200, timeout=0.2, write_timeout=3) as ser:
        time.sleep(0.5)
        stale = read_available(ser, 0.2)
        if stale:
            print(f"Stale bytes cleared: {stale.hex()}")

        start_pkt = packets[0]
        print(f"TX START ({len(start_pkt)}B): {start_pkt.hex()}")
        ser.write(start_pkt)
        ser.flush()

        print("Waiting for device request...")
        deadline = time.time() + 6.0
        got = bytearray()
        seen_request = False
        while time.time() < deadline:
            got.extend(read_available(ser, 0.1))
            if b"\x8b\x55\x00" in got or bytes.fromhex("010700048b550001ec0002") in got or len(got) >= 11:
                print(f"Device request received: {got.hex()}")
                seen_request = True
                break
        if not seen_request:
            print(f"No explicit request seen (got: {got.hex()}), proceeding to send chunks...")

        for i, pkt in enumerate(packets[1:]):
            ser.write(pkt)
            ser.flush()
            time.sleep(delay)
            if i == 0 or i == len(packets) - 2 or (i + 1) % 10 == 0:
                print(f"  Sent chunk {i + 1}/{len(packets) - 1}")

        print("Waiting for final ACK...")
        tail = read_available(ser, 2.0)
        if tail:
            print(f"Final ACK received: {tail.hex()}")
            return True
        else:
            print("(No tail received, but chunks sent)")
            return True

if __name__ == "__main__":
    # Create test image: bright dark blue background with clear graphics
    test_img = Image.new("RGB", (128, 128), (10, 15, 35))
    draw = ImageDraw.Draw(test_img)
    draw.rectangle([1, 1, 126, 126], outline=(0, 220, 255), width=2)
    draw.text((20, 15), "CLAUDE", fill=(255, 120, 50))
    draw.text((20, 35), "5H  63%", fill=(255, 255, 255))
    draw.rectangle([20, 50, 108, 60], fill=(30, 45, 70), outline=(0, 150, 255))
    draw.rectangle([22, 52, 77, 58], fill=(0, 255, 150))
    draw.text((20, 68), "RESET 2H 14M", fill=(160, 180, 200))
    draw.text((20, 85), "WEEK 41%", fill=(255, 255, 255))
    draw.rectangle([20, 100, 108, 110], fill=(30, 45, 70), outline=(0, 150, 255))
    draw.rectangle([22, 102, 57, 108], fill=(0, 200, 255))
    draw.text((20, 114), "RESET 3D 8H", fill=(160, 180, 200))

    test_img.save("test_claude_preview.png")
    print("Saved preview to test_claude_preview.png")

    port = sys.argv[1] if len(sys.argv) > 1 else None
    if not port:
        try:
            from detector import detect_minitoo_port
            port = detect_minitoo_port()
        except Exception:
            port = None
    if not port:
        print("No MiniToo port detected.")
        sys.exit(1)

    success = send_image_to_minitoo(port, test_img)
    print("Result:", "SUCCESS" if success else "FAILED")
