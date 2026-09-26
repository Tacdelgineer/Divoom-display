#!/usr/bin/env python3
"""
Test script to send an image to Divoom MiniToo over Bluetooth RFCOMM on Windows.
"""
import io
import socket
import sys
import time
from PIL import Image, ImageDraw, ImageFont

MINITOO_MAC = "B1:21:81:94:22:9C"
RFCOMM_CHANNEL = 1
CHUNK_SIZE = 256
CMD_APP_NEW_GIF_CMD2020 = 0x8B

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

def wait_for_response(sock: socket.socket, timeout: float = 3.0) -> bytes | None:
    sock.settimeout(timeout)
    buf = b""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            chunk = sock.recv(1024)
            if chunk:
                buf += chunk
                if len(buf) >= 7 and buf[0] == 0x01:
                    pkt_len = buf[1] | (buf[2] << 8)
                    expected_total = pkt_len + 4
                    if len(buf) >= expected_total:
                        return buf[:expected_total]
        except socket.timeout:
            break
        except Exception as e:
            print("Recv err:", e)
            break
    return buf if buf else None

def encode_image_payload(img: Image.Image, jpeg_quality: int = 85) -> bytes:
    # MiniToo expects 160x128 JPEG landscape for 8x10 tile grid
    if img.size != (160, 128):
        img = img.resize((160, 128), Image.Resampling.LANCZOS)
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    jpeg_data = buf.getvalue()

    # Payload header: [0x23, frame_count=1, speed_hi=0, speed_lo=0, tile_rows=8, tile_cols=10]
    header = bytes([0x23, 0x01, 0x00, 0x00, 0x08, 0x0A])
    # Frame: encode_type 0x01 (JPEG) + length (4B BE) + jpeg_data
    frame = bytes([0x01]) + len(jpeg_data).to_bytes(4, "big") + jpeg_data
    return header + frame

def build_chunks(payload: bytes) -> list[bytes]:
    chunks = []
    total_len = len(payload)
    num_chunks = (total_len + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(num_chunks):
        offset = i * CHUNK_SIZE
        chunk_data = payload[offset : offset + CHUNK_SIZE]
        # Chunk inner data: [0x01] + total_len (4B LE) + chunk_index (2B LE) + chunk_data
        inner = bytes([0x01])
        inner += total_len.to_bytes(4, "little")
        inner += i.to_bytes(2, "little")
        inner += chunk_data
        chunks.append(build_packet(CMD_APP_NEW_GIF_CMD2020, inner))
    return chunks

def send_all_chunks(sock: socket.socket, chunks: list[bytes], delay: float = 0.02):
    for i, chunk in enumerate(chunks):
        sock.sendall(chunk)
        time.sleep(delay)
        if (i + 1) % 10 == 0 or i == len(chunks) - 1:
            print(f"    Sent chunk {i + 1}/{len(chunks)}")

def handle_device_requests(sock: socket.socket, chunks: list[bytes], timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        rem = deadline - time.monotonic()
        if rem <= 0: break
        resp = wait_for_response(sock, timeout=min(2.0, rem))
        if not resp:
            break
        print(f"    RX: {hex_dump(resp)}")
        if len(resp) > 6:
            ctrl = resp[6]
            if ctrl == 0x00:
                print("    Device: SEND ALL")
                send_all_chunks(sock, chunks)
                return
            elif ctrl == 0x01 and len(resp) > 10:
                idx = int.from_bytes(resp[7:11], "little")
                if 0 <= idx < len(chunks):
                    sock.sendall(chunks[idx])
                    print(f"    Resent chunk {idx}")
                else:
                    print(f"    Chunk {idx} out of range!")
            else:
                print(f"    Unknown control: 0x{ctrl:02x}")
                break
        else:
            break

def send_image(sock: socket.socket, img: Image.Image, jpeg_quality: int = 85):
    payload = encode_image_payload(img, jpeg_quality)
    print(f"Payload encoded: {len(payload)} bytes (JPEG q={jpeg_quality})")
    chunks = build_chunks(payload)
    print(f"Split into {len(chunks)} chunks of {CHUNK_SIZE} bytes")

    # START packet: [0x00, payload_len_4B_LE, circle_flag=0]
    start_data = bytes([0x00]) + len(payload).to_bytes(4, "little") + bytes([0x00])
    start_pkt = build_packet(CMD_APP_NEW_GIF_CMD2020, start_data)
    print(f"Sending START packet: {hex_dump(start_pkt)}")
    sock.sendall(start_pkt)

    print("Waiting for device response...")
    resp = wait_for_response(sock, timeout=5.0)
    if not resp:
        print("No response to START! Sending all chunks blindly...")
        send_all_chunks(sock, chunks)
    elif len(resp) > 6:
        print(f"Received START response: {hex_dump(resp)}")
        ctrl = resp[6]
        if ctrl == 0x00:
            print("Device requested: SEND ALL")
            send_all_chunks(sock, chunks)
        elif ctrl == 0x01:
            idx = int.from_bytes(resp[7:11], "little") if len(resp) > 10 else 0
            print(f"Device requested chunk {idx}")
            if 0 <= idx < len(chunks):
                sock.sendall(chunks[idx])
            handle_device_requests(sock, chunks)
        else:
            print(f"Unknown control 0x{ctrl:02x}, sending all chunks...")
            send_all_chunks(sock, chunks)
    else:
        print(f"Short response ({len(resp)}B), sending all chunks...")
        send_all_chunks(sock, chunks)

    print("Waiting for final ACK...")
    final = wait_for_response(sock, timeout=3.0)
    if final:
        print(f"Final ACK: {hex_dump(final)}")
    else:
        print("(No final ACK received)")
    print("Done!")

if __name__ == "__main__":
    # Create a test image: Dark background with bright text and colored boxes
    img = Image.new("RGB", (160, 128), (15, 20, 30))
    draw = ImageDraw.Draw(img)
    
    # Draw border
    draw.rectangle([2, 2, 157, 125], outline=(0, 200, 255), width=2)
    # Draw header text
    draw.text((30, 20), "CLAUDE CODE", fill=(255, 120, 50))
    draw.text((25, 45), "MiniToo CONNECTED", fill=(0, 255, 150))
    draw.rectangle([20, 75, 140, 95], fill=(40, 50, 80), outline=(0, 200, 255))
    draw.rectangle([22, 77, 95, 93], fill=(0, 255, 150))
    draw.text((35, 105), "Milestone 1 PROOF", fill=(220, 220, 220))
    
    # Save a copy locally
    img.save("test_proof.png")
    print("Saved test_proof.png")
    
    print(f"Connecting to {MINITOO_MAC} channel {RFCOMM_CHANNEL}...")
    sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    sock.settimeout(5.0)
    sock.connect((MINITOO_MAC, RFCOMM_CHANNEL))
    print("Connected!")
    
    try:
        send_image(sock, img, jpeg_quality=85)
    finally:
        sock.close()
        print("Connection closed.")
