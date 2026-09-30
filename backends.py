#!/usr/bin/env python3
"""
Display backends for Divoom MiniToo AI Desk Dashboard.
Decouples display hardware and presentation from data collection and rendering.
"""
from __future__ import annotations

import os
import sys
import time
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image

try:
    import serial
except ImportError:
    serial = None


class DisplayBackend(ABC):
    """Abstract base class for dashboard display targets."""

    @abstractmethod
    def show(self, img: Image.Image, **kwargs) -> bool:
        """Render or transfer a PIL Image. Return True on success."""
        pass

    def close(self) -> None:
        """Release any hardware handles or resources."""
        pass


class DesktopPreviewDisplay(DisplayBackend):
    """
    Renders dashboard frames locally to a file and optional high-DPI desktop preview.
    Allows testing and development without the physical MiniToo device.
    """

    def __init__(
        self,
        output_path: str = "preview_dashboard.png",
        scale: int = 3,
        auto_open: bool = False,
    ):
        self.output_path = output_path
        self.scale = scale
        self.auto_open = auto_open
        self._has_opened = False

    def show(self, img: Image.Image, **kwargs) -> bool:
        try:
            # Save native 128x128 image
            img.save("screen.png")

            # Upscale using nearest-neighbor for sharp pixel-art text preview
            scaled_w = 128 * self.scale
            scaled_h = 128 * self.scale
            scaled = img.resize((scaled_w, scaled_h), Image.Resampling.NEAREST)
            scaled.save(self.output_path)
            print(f"[PREVIEW] Saved frame -> {self.output_path} ({scaled_w}x{scaled_h})")

            if self.auto_open and not self._has_opened:
                if sys.platform == "win32":
                    os.startfile(self.output_path)
                    self._has_opened = True
            return True
        except Exception as e:
            print(f"[PREVIEW] Error saving preview: {e}")
            return False


class MiniTooDisplay(DisplayBackend):
    """
    Divoom MiniToo 128x128 physical display backend over Bluetooth SPP.
    Wraps the proven frame protocol and retry transport.
    """

    def __init__(self, port: Optional[str] = None, delay: float = 0.02):
        self.port = port
        self.delay = delay
        # Diagnostics & Traffic Instrumentation
        self.frames_sent_total: int = 0
        self.bytes_sent_total: int = 0
        self.spp_writes_total: int = 0
        self.spp_reads_total: int = 0
        self._history: List[Tuple[float, str, int, int]] = []
        self._stats_lock = threading.Lock()

    def record_traffic(self, event_type: str, count: int = 1, byte_count: int = 0):
        """Record an SPP write/read/frame event for rolling rates."""
        now = time.time()
        with self._stats_lock:
            self._history.append((now, event_type, count, byte_count))
            cutoff = now - 60.0
            while self._history and self._history[0][0] < cutoff:
                self._history.pop(0)
            if event_type == "write":
                self.spp_writes_total += count
                self.bytes_sent_total += byte_count
            elif event_type == "read":
                self.spp_reads_total += count
            elif event_type == "frame":
                self.frames_sent_total += count

    def get_rolling_rates(self) -> Dict[str, Any]:
        """Calculate per-minute traffic and packet metrics over the last 60 seconds."""
        now = time.time()
        cutoff = now - 60.0
        with self._stats_lock:
            while self._history and self._history[0][0] < cutoff:
                self._history.pop(0)
            writes_min = sum(item[2] for item in self._history if item[1] == "write")
            reads_min = sum(item[2] for item in self._history if item[1] == "read")
            frames_min = sum(item[2] for item in self._history if item[1] == "frame")
            bytes_min = sum(item[3] for item in self._history if item[1] == "write")
        return {
            "writes_per_min": writes_min,
            "reads_per_min": reads_min,
            "frames_per_min": frames_min,
            "bytes_per_min": bytes_min,
            "kb_per_min": round(bytes_min / 1024.0, 2),
            "frames_sent_total": self.frames_sent_total,
            "bytes_sent_total": self.bytes_sent_total,
            "spp_writes_total": self.spp_writes_total,
            "spp_reads_total": self.spp_reads_total,
        }

    @staticmethod
    def find_minitoo_port() -> Optional[str]:
        """Auto-detect MiniToo COM port using hardware probing and metadata."""
        try:
            from detector import detect_minitoo_port
            p = detect_minitoo_port()
            if p:
                return p
        except Exception:
            pass
        return None

    @staticmethod
    def _crc16(data: bytes) -> int:
        return sum(data) & 0xFFFF

    @classmethod
    def _frame(cls, cmd: int, payload: bytes = b"") -> bytes:
        out = bytearray(7 + len(payload))
        out[0] = 0x01
        decl = len(out) - 4
        out[1:3] = decl.to_bytes(2, "little")
        out[3] = cmd & 0xFF
        out[4 : 4 + len(payload)] = payload
        chk = sum(out[1 : len(out) - 3]) & 0xFFFF
        out[-3:-1] = chk.to_bytes(2, "little")
        out[-1] = 0x02
        return bytes(out)

    @classmethod
    def _encode_image_payload(cls, img: Image.Image, jpeg_quality: int = 85) -> bytes:
        import io
        # MiniToo IPS LCD requires 160x128 resolution.
        # If image is 128x128, center it with 16px borders on left and right
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

        # MiniToo IPS LCD frame header: 8 tile rows x 10 tile cols
        header = bytes([
            0x23,        # LCD frame marker
            0x01,        # 1 frame
            0x00, 0x00,  # speed = 0
            0x08,        # tile rows = 8 (160 // 20)
            0x0A,        # tile cols = 10 (128 // ~13)
        ])
        frame = bytes([0x01]) + len(jpeg_data).to_bytes(4, "big") + jpeg_data
        return header + frame

    @classmethod
    def _build_packets(cls, payload: bytes, chunk_size: int = 256) -> list[bytes]:
        total_len = len(payload)
        # START packet: [0x00, total_len 4B LE, circle_flag 0]
        start_data = bytes([0x00]) + total_len.to_bytes(4, "little") + bytes([0x00])
        packets = [cls._frame(0x8B, start_data)]
        num_chunks = (total_len + chunk_size - 1) // chunk_size
        for i in range(num_chunks):
            offset = i * chunk_size
            chunk_data = payload[offset : offset + chunk_size]
            inner = bytes([0x01]) + total_len.to_bytes(4, "little") + i.to_bytes(2, "little") + chunk_data
            packets.append(cls._frame(0x8B, inner))
        return packets

    @staticmethod
    def _read_available(ser: serial.Serial, wait: float = 0.25) -> bytes:
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

    def show(self, img: Image.Image, ser: Optional[serial.Serial] = None) -> bool:
        if serial is None:
            print("[MINITOO] Error: pyserial is not installed.")
            return False

        payload = self._encode_image_payload(img)
        packets = self._build_packets(payload)

        # Fast path: stream immediately if an open connection is already maintained
        if ser is not None and getattr(ser, "is_open", False):
            try:
                if ser.in_waiting:
                    flushed = ser.read(ser.in_waiting)
                    self.record_traffic("read", 1, len(flushed))
                ser.write(packets[0])
                ser.flush()
                self.record_traffic("write", 1, len(packets[0]))
                # Wait briefly for device response
                deadline = time.time() + 2.0
                resp = bytearray()
                while time.time() < deadline:
                    if ser.in_waiting:
                        chunk = ser.read(ser.in_waiting)
                        resp.extend(chunk)
                        self.record_traffic("read", 1, len(chunk))
                        if len(resp) >= 7 and resp[0] == 0x01:
                            break
                    time.sleep(0.01)

                for pkt in packets[1:]:
                    ser.write(pkt)
                    ser.flush()
                    self.record_traffic("write", 1, len(pkt))
                    time.sleep(self.delay)
                time.sleep(0.05)
                if ser.in_waiting:
                    tail = ser.read(ser.in_waiting)
                    self.record_traffic("read", 1, len(tail))
                self.record_traffic("frame", 1, 0)
                return True
            except Exception as e:
                print(f"[MINITOO] Stream error on active connection: {e}")
                return False

        target_port = self.port or self.find_minitoo_port()
        if not target_port:
            print("[MINITOO] No Divoom MiniToo detected on any Bluetooth serial port.")
            return False
        print(f"Connecting to Divoom MiniToo on {target_port}...")
        for attempt in range(5):
            try:
                with serial.Serial(
                    target_port, baudrate=115200, timeout=0.1, write_timeout=3
                ) as ser:
                    time.sleep(0.3)
                    if ser.in_waiting:
                        flushed = ser.read(ser.in_waiting)
                        self.record_traffic("read", 1, len(flushed))

                    # Send START packet
                    ser.write(packets[0])
                    ser.flush()
                    self.record_traffic("write", 1, len(packets[0]))

                    # Wait for device ready
                    deadline = time.time() + 4.0
                    got = bytearray()
                    while time.time() < deadline:
                        if ser.in_waiting:
                            chunk = ser.read(ser.in_waiting)
                            got.extend(chunk)
                            self.record_traffic("read", 1, len(chunk))
                            if len(got) >= 7 and got[0] == 0x01:
                                break
                        time.sleep(0.01)

                    # Send chunks
                    for pkt in packets[1:]:
                        ser.write(pkt)
                        ser.flush()
                        self.record_traffic("write", 1, len(pkt))
                        time.sleep(self.delay)

                    time.sleep(0.1)
                    if ser.in_waiting:
                        tail = ser.read(ser.in_waiting)
                        self.record_traffic("read", 1, len(tail))
                        print(f"Display update confirmed! ({len(packets)-1} chunks)")
                    else:
                        print(f"Display chunks transferred ({len(packets)-1} chunks).")
                    self.record_traffic("frame", 1, 0)
                    return True
            except serial.SerialException as e:
                if attempt < 4 and ("Access is denied" in str(e) or "PermissionError" in str(e)):
                    time.sleep(1.0)
                    continue
                print(f"Error connecting to {target_port}: {e}")
                return False
        return False


class DitooDisplay(DisplayBackend):
    """
    Divoom Ditoo / Ditoo Plus 16x16 physical display backend over BLE GATT or SPP.
    """

    def __init__(self, ble_address: str = "B1:21:81:5B:E3:16", port: Optional[str] = None):
        self.ble_address = ble_address
        self.port = port
        self._device = None

    def _get_device(self):
        if self._device is None:
            try:
                from src.devices.ditoo import DitooDevice
                self._device = DitooDevice(ble_address=self.ble_address, com_port=self.port)
            except Exception as e:
                print(f"[DITOO] Driver import error: {e}")
        return self._device

    def show(self, img: Image.Image, **kwargs) -> bool:
        device = self._get_device()
        if not device:
            return False

        import asyncio

        async def _push():
            if not device.is_connected:
                ok = await device.connect()
                if not ok:
                    return False
            return await device.show_frame(img)

        try:
            return asyncio.run(_push())
        except Exception as e:
            print(f"[DITOO] Display error: {e}")
            return False

    def close(self) -> None:
        if self._device and self._device.is_connected:
            import asyncio
            try:
                asyncio.run(self._device.disconnect())
            except Exception:
                pass


def get_display_backend(name: str = "minitoo", **kwargs) -> DisplayBackend:
    """Factory helper to obtain a configured DisplayBackend instance."""
    normalized = name.lower().strip()
    if normalized in ("minitoo", "hardware", "device"):
        return MiniTooDisplay(port=kwargs.get("port"))
    elif normalized in ("ditoo", "ditoo_16", "ditoo_plus"):
        return DitooDisplay(
            ble_address=kwargs.get("ble_address", "B1:21:81:5B:E3:16"),
            port=kwargs.get("port")
        )
    elif normalized in ("preview", "desktop", "desktop_preview"):
        return DesktopPreviewDisplay(
            output_path=kwargs.get("output_path", "preview_dashboard.png"),
            scale=kwargs.get("scale", 3),
            auto_open=kwargs.get("auto_open", False),
        )
    else:
        raise ValueError(f"Unknown display backend: {name}. Use 'minitoo', 'ditoo', or 'preview'.")

