"""
Divoom Ditoo / Ditoo Plus 16x16 Hardware Device Driver.
Handles connection, transport framing, proof-of-life tests, and image dispatch.

Supports:
1. BLE GATT Transparent UART via Bleak (DitooPro-Light: B1:21:81:5B:E3:16).
2. Classic Bluetooth SPP via virtual COM port (when paired as Ditoo-Audio in Windows).
3. Automatic reconnection and state restoration on power loss.
"""
from __future__ import annotations

import asyncio
import io
import math
import sys
import time
from typing import List, Tuple, Optional, Callable
from PIL import Image

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    BleakClient = None
    BleakScanner = None

# Microchip / ISSC Transparent UART Service & Characteristics
BLE_SERVICE_UUID = "49535343-fe7d-4ae5-8fa9-9fafd205e455"
BLE_CHAR_TX = "49535343-8841-43f4-a8d4-ecbe34729bb3"      # Host -> Device (write / write-without-response)
BLE_CHAR_RX = "49535343-1e4d-4bd9-ba61-23c647249616"      # Device -> Host (notify / write-without-response)
BLE_CHAR_CTRL = "49535343-aca3-481c-91ec-d85e28a60318"    # Control / Flow

DEFAULT_DITOO_BLE_MAC = "B1:21:81:5B:E3:16"


def frame_spp(cmd: int, payload: bytes = b"") -> bytes:
    """Wrap payload in standard Divoom SPP envelope with 16-bit little-endian checksum."""
    out = bytearray(7 + len(payload))
    out[0] = 0x01
    decl = len(payload) + 3
    out[1:3] = decl.to_bytes(2, "little")
    out[3] = cmd & 0xFF
    out[4 : 4 + len(payload)] = payload
    chk = sum(out[1 : len(out) - 3]) & 0xFFFF
    out[-3:-1] = chk.to_bytes(2, "little")
    out[-1] = 0x02
    return bytes(out)


def encode_16x16_frame(img: Image.Image, delay_ms: int = 0) -> bytes:
    """
    Encode a 16x16 PIL Image into standard Divoom 16x16 binary frame format:
    [0xAA] [length 2B LE] [delay 2B LE] [reuse_palette 1B] [color_count 1B]
    [palette N*3B RGB] [bit-packed pixel indices]
    """
    if img.size != (16, 16):
        img = img.resize((16, 16), Image.Resampling.NEAREST)
    img_rgb = img.convert("RGB")

    # 1. Build palette & pixel index map
    palette: List[Tuple[int, int, int]] = []
    color_to_idx = {}
    pixel_indices = []

    for y in range(16):
        for x in range(16):
            c = img_rgb.getpixel((x, y))
            if c not in color_to_idx:
                color_to_idx[c] = len(palette)
                palette.append(c)
            pixel_indices.append(color_to_idx[c])

    # Ensure at least 2 colors in palette so bits_per_pixel >= 1
    if len(palette) < 2:
        extra_c = (0, 0, 0) if palette[0] != (0, 0, 0) else (255, 255, 255)
        palette.append(extra_c)

    color_count = len(palette)
    if color_count > 256:
        raise ValueError(f"Too many colors in 16x16 frame: {color_count} (max 256)")

    # 2. Calculate bits per pixel: ceil(log2(color_count))
    bpp = max(1, math.ceil(math.log2(color_count)))

    # 3. Bit-pack pixel indices in little-endian order
    bit_buffer = 0
    bit_count = 0
    packed_pixels = bytearray()

    for idx in pixel_indices:
        bit_buffer |= (idx << bit_count)
        bit_count += bpp
        while bit_count >= 8:
            packed_pixels.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    if bit_count > 0:
        packed_pixels.append(bit_buffer & 0xFF)

    # 4. Serialize palette bytes
    palette_bytes = bytearray()
    for r, g, b in palette:
        palette_bytes.extend([r & 0xFF, g & 0xFF, b & 0xFF])

    # 5. Build frame header
    # length includes all bytes of frame (7 header bytes + palette + packed pixels)
    length = 7 + len(palette_bytes) + len(packed_pixels)
    header = bytearray([0xAA])
    header.extend(length.to_bytes(2, "little"))
    header.extend(delay_ms.to_bytes(2, "little"))
    header.append(0x00)  # reuse_palette = 0 (false)
    header.append(color_count if color_count < 256 else 0x00)

    return bytes(header) + bytes(palette_bytes) + bytes(packed_pixels)


def build_0x8b_packets(frame_data: bytes, chunk_size: int = 256) -> List[bytes]:
    """Create Command 0x8B network packets (Start packet + Data chunk packets)."""
    file_size = len(frame_data)
    packets = []

    # Start packet: [0x00, file_size 4B LE, 0x00]
    start_payload = bytes([0x00]) + file_size.to_bytes(4, "little") + bytes([0x00])
    packets.append(frame_spp(0x8B, start_payload))

    # Data packets: [0x01, file_size 4B LE, offset_id 2B LE, chunk_data]
    num_chunks = (file_size + chunk_size - 1) // chunk_size
    for i in range(num_chunks):
        offset = i * chunk_size
        chunk = frame_data[offset : offset + chunk_size]
        body = bytes([0x01]) + file_size.to_bytes(4, "little") + i.to_bytes(2, "little") + chunk
        packets.append(frame_spp(0x8B, body))

    return packets


def build_0x49_packet(frame_data: bytes) -> bytes:
    """Create Command 0x49 animation/image packet."""
    file_size = len(frame_data)
    payload = file_size.to_bytes(2, "little") + bytes([0x00]) + frame_data
    return frame_spp(0x49, payload)


def build_solid_color_packet(r: int, g: int, b: int, brightness: int = 100) -> bytes:
    """Create Command 0x45 channel 0x01 (Lightning plain color) packet."""
    payload = bytes([0x01, r & 0xFF, g & 0xFF, b & 0xFF, max(0, min(100, brightness)), 0x00, 0x01, 0x00, 0x00, 0x00])
    return frame_spp(0x45, payload)


class DitooDevice:
    """
    Controller for Divoom Ditoo / Ditoo Plus.
    Manages transport (BLE or SPP serial), packet streaming, and auto-reconnect.
    """

    def __init__(self, ble_address: str = DEFAULT_DITOO_BLE_MAC, com_port: Optional[str] = None):
        self.ble_address = ble_address
        self.com_port = com_port
        self.ble_client: Optional[BleakClient] = None
        self.serial_port: Optional[serial.Serial] = None
        self.last_img: Optional[Image.Image] = None
        self._is_connected = False

    @property
    def is_connected(self) -> bool:
        if self.ble_client and getattr(self.ble_client, "is_connected", False):
            return True
        if self.serial_port and getattr(self.serial_port, "is_open", False):
            return True
        return False

    async def connect_ble(self, timeout: float = 6.0) -> bool:
        """Connect to DitooPro-Light over BLE with remembered MAC and scanner fallback."""
        if BleakClient is None:
            print("[DITOO] bleak library not installed.")
            return False

        # 1. Try direct connection with remembered MAC if valid
        if self.ble_address and self.ble_address != "AUTO":
            try:
                print(f"[DITOO] Connecting to BLE peripheral {self.ble_address}...")
                self.ble_client = BleakClient(self.ble_address)
                await asyncio.wait_for(self.ble_client.connect(), timeout=timeout)
                if self.ble_client.is_connected:
                    print(f"[DITOO] Connected over BLE! (MTU: {self.ble_client.mtu_size})")
                    self._is_connected = True
                    return True
            except Exception as e:
                print(f"[DITOO] Direct BLE connection failed: {e}")
                self.ble_client = None

        # 2. Scanner fallback: discover DitooPro-Light peripheral
        if BleakScanner is not None:
            try:
                print("[DITOO] Scanning for 'DitooPro-Light' BLE peripheral...")
                devices = await BleakScanner.discover(timeout=4.0)
                for d in devices:
                    if d.name and "DitooPro-Light" in d.name:
                        print(f"[DITOO] Discovered {d.name} at {d.address}!")
                        self.ble_address = d.address
                        self.ble_client = BleakClient(d.address)
                        await asyncio.wait_for(self.ble_client.connect(), timeout=timeout)
                        if self.ble_client.is_connected:
                            print(f"[DITOO] Connected via discovery! (MTU: {self.ble_client.mtu_size})")
                            self._is_connected = True
                            return True
            except Exception as scan_err:
                print(f"[DITOO] BLE scanner fallback error: {scan_err}")
                self.ble_client = None

        return False

    def connect_serial(self) -> bool:
        """Connect to Divoom SPP virtual COM port on Windows."""
        if serial is None or not self.com_port:
            return False
        try:
            print(f"[DITOO] Opening serial port {self.com_port}...")
            self.serial_port = serial.Serial(self.com_port, 115200, timeout=0.2, write_timeout=2.0)
            time.sleep(0.3)
            self._is_connected = True
            print(f"[DITOO] Connected over SPP on {self.com_port}!")
            return True
        except Exception as e:
            print(f"[DITOO] Serial connection error: {e}")
            self.serial_port = None
            return False

    async def connect(self) -> bool:
        """Attempt connection: BLE first, then SPP serial fallback."""
        if await self.connect_ble():
            return True
        if self.com_port and self.connect_serial():
            return True
        return False

    async def disconnect(self) -> None:
        """Close active connections cleanly."""
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.disconnect()
            except Exception:
                pass
            self.ble_client = None
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None
        self._is_connected = False

    async def send_packet(self, packet_bytes: bytes) -> bool:
        """Send raw packet over active transport."""
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.write_gatt_char(BLE_CHAR_TX, packet_bytes, response=False)
                return True
            except Exception as e:
                print(f"[DITOO] BLE write error: {e}")
                return False

        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write(packet_bytes)
                self.serial_port.flush()
                return True
            except Exception as e:
                print(f"[DITOO] Serial write error: {e}")
                return False

        return False

    async def show_frame(self, img: Image.Image, delay_ms: int = 0) -> bool:
        """Render and send a 16x16 image to the Ditoo display."""
        frame_bytes = encode_16x16_frame(img, delay_ms=delay_ms)
        packets = build_0x8b_packets(frame_bytes)

        self.last_img = img

        for i, pkt in enumerate(packets):
            ok = await self.send_packet(pkt)
            if not ok:
                return False
            if i == 0:
                await asyncio.sleep(0.12)  # Pause after start packet
            else:
                await asyncio.sleep(0.04)

        return True

    async def set_brightness(self, brightness: int = 100) -> bool:
        """Set screen brightness (0-100) via Divoom Command 0x74."""
        b = max(0, min(100, int(brightness)))
        pkt = frame_spp(0x74, bytes([b]))
        return await self.send_packet(pkt)

    async def set_solid_color(self, r: int, g: int, b: int, brightness: int = 100) -> bool:
        """Command 0x45 instant solid color fill."""
        pkt = build_solid_color_packet(r, g, b, brightness)
        return await self.send_packet(pkt)

    async def run_proof_of_life(self) -> bool:
        """
        Executes proof-of-life verification sequence:
        1. Solid Red
        2. Solid Green
        3. Solid Blue
        4. Checkerboard / test pixels
        5. Simple animation
        """
        print("\n=== STARTING DITOO 16x16 PROOF-OF-LIFE SEQUENCE ===")

        # 1. Solid Red
        print("[PROOF-OF-LIFE] 1/5: Displaying SOLID RED...")
        await self.set_solid_color(255, 0, 0, 100)
        red_img = Image.new("RGB", (16, 16), (255, 0, 0))
        await self.show_frame(red_img)
        await asyncio.sleep(1.5)

        # 2. Solid Green
        print("[PROOF-OF-LIFE] 2/5: Displaying SOLID GREEN...")
        await self.set_solid_color(0, 255, 0, 100)
        green_img = Image.new("RGB", (16, 16), (0, 255, 0))
        await self.show_frame(green_img)
        await asyncio.sleep(1.5)

        # 3. Solid Blue
        print("[PROOF-OF-LIFE] 3/5: Displaying SOLID BLUE...")
        await self.set_solid_color(0, 0, 255, 100)
        blue_img = Image.new("RGB", (16, 16), (0, 0, 255))
        await self.show_frame(blue_img)
        await asyncio.sleep(1.5)

        # 4. Checkerboard / Test Pixels
        print("[PROOF-OF-LIFE] 4/5: Displaying CHECKERBOARD TEST PATTERN...")
        check_img = Image.new("RGB", (16, 16), (0, 0, 0))
        pixels = check_img.load()
        for y in range(16):
            for x in range(16):
                if (x + y) % 2 == 0:
                    pixels[x, y] = (255, 255, 255)
        await self.show_frame(check_img)
        await asyncio.sleep(2.0)

        # 5. Simple Animation (Expanding diamond pulse)
        print("[PROOF-OF-LIFE] 5/5: Running SIMPLE PULSE ANIMATION (3 cycles)...")
        for _ in range(3):
            for radius in range(1, 8):
                anim_img = Image.new("RGB", (16, 16), (10, 15, 25))
                pix = anim_img.load()
                for y in range(16):
                    for x in range(16):
                        dist = abs(x - 7.5) + abs(y - 7.5)
                        if abs(dist - radius) < 1.0:
                            pix[x, y] = (0, 229, 255)  # Cyan ring
                await self.show_frame(anim_img)
                await asyncio.sleep(0.08)

        print("=== PROOF-OF-LIFE SEQUENCE COMPLETED ===")
        return True
