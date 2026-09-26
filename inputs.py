#!/usr/bin/env python3
"""
Input Adapters for AI Desk Dashboard.
Decouples physical hardware controls, rotary encoders, dials, and keyboards
from dashboard data collection and display rendering.
"""
from __future__ import annotations

import enum
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


class InputEvent(enum.Enum):
    """Normalized navigation actions emitted by input hardware."""
    NONE = "NONE"
    NEXT_PAGE = "NEXT_PAGE"
    PREV_PAGE = "PREV_PAGE"
    TOGGLE_PAUSE = "TOGGLE_PAUSE"


class BaseInputAdapter(ABC):
    """Abstract base class for all dashboard input devices."""

    @abstractmethod
    def poll_event(self) -> InputEvent:
        """Poll the input device for any pending user navigation event."""
        pass

    def close(self) -> None:
        """Release any hardware handles or resources."""
        pass


def frame_spp(cmd: int, payload: bytes = b"") -> bytes:
    """Frame a standard Divoom SPP envelope with correct checksum."""
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


def extract_packets(data: bytes) -> list[Tuple[int, bytes]]:
    """Extract all framed Divoom packets from a buffer, supporting multi-packet streams."""
    packets = []
    idx = 0
    while idx < len(data):
        start = data.find(b"\x01", idx)
        if start == -1:
            break
        if len(data) - start < 7:
            break
        decl_len = data[start + 1] | (data[start + 2] << 8)
        total_len = decl_len + 4
        if len(data) - start < total_len:
            break
        pkt = data[start : start + total_len]
        if pkt[-1] == 0x02:
            if total_len >= 8 and pkt[3] == 0x04:
                cmd = pkt[4]
                body = pkt[6:-3]
                packets.append((cmd, body))
            else:
                cmd = pkt[3]
                body = pkt[4:-3]
                packets.append((cmd, body))
            idx = start + total_len
        else:
            idx = start + 1
    return packets


def parse_response(data: bytes) -> Optional[Tuple[int, bytes]]:
    """Parse Divoom response frame and extract command echo and payload."""
    pkts = extract_packets(data)
    return pkts[0] if pkts else None


class MiniTooInputAdapter(BaseInputAdapter):
    """
    Physical input adapter for Divoom MiniToo hardware controls.
    Polls device state over Bluetooth SPP at ~10-12 Hz and maps
    physical knob rotations to NEXT / PREV navigation.
    
    Features:
    - Remembers original base volume level and immediately restores it.
    - Prevents audible sound change and preserves sound state.
    - Debounces rapid knob pulses to ensure exactly 1 page transition per step.
    - Exposes its persistent serial connection to MiniTooDisplay for fast frame transfers.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 115200,
        debounce_secs: float = 0.25,
        target_base_vol: int = 10,
    ):
        self.port = port or self.find_port()
        self.baudrate = baudrate
        self.debounce_secs = debounce_secs
        self.target_base_vol = 8  # Middle of 0..16 scale for max headroom
        self.current_base_vol: int = 8
        self.last_event_time: float = 0.0
        self.last_poll_time: float = 0.0
        self.poll_interval: float = 0.06  # ~16 Hz responsiveness

        self._connect()

    @staticmethod
    def find_port() -> Optional[str]:
        """Auto-detect MiniToo COM port using hardware probing and metadata."""
        try:
            from detector import detect_minitoo_port
            p = detect_minitoo_port()
            if p:
                return p
        except Exception:
            pass
        return None

    def _connect(self) -> bool:
        if serial is None or not self.port:
            return False
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.04)
            time.sleep(0.3)
            if self.ser.in_waiting:
                self.ser.read(self.ser.in_waiting)

            # Ensure device is in Custom/DIY Channel 5
            self.set_channel(5)

            # Center base volume to 8 for symmetric headroom (+8 / -8)
            self.set_vol(self.target_base_vol)
            self.current_base_vol = self.target_base_vol
            print(f"[INPUT] Connected to MiniToo on {self.port} (Channel 5 active, Centered Base Vol: {self.current_base_vol})")
            return True
        except Exception as e:
            print(f"[INPUT] Warning: Could not open {self.port} for physical controls: {e}")
            self.ser = None
            return False

    def query_channel(self) -> Optional[int]:
        """Query current display channel (0xBD 0x13). Channel 5 = Custom/DIY."""
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")
        try:
            self.ser.write(frame_spp(0xBD, bytes([0x13])))
            self.ser.flush()
            t0 = time.time()
            buf = bytearray()
            while time.time() - t0 < 0.08:
                if self.ser.in_waiting:
                    buf.extend(self.ser.read(self.ser.in_waiting))
                    pkts = extract_packets(bytes(buf))
                    for cmd, body in pkts:
                        if cmd == 0xBD and len(body) >= 3 and body[0] == 0x13:
                            return body[2]
                time.sleep(0.005)
        except (serial.SerialException, OSError) as e:
            self.close()
            raise serial.SerialException(f"Serial communication lost: {e}")
        except Exception:
            pass
        return None

    def set_channel(self, channel: int = 5) -> bool:
        """Set display channel (0x45). Channel 5 = Custom/DIY."""
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")
        try:
            self.ser.write(frame_spp(0x45, bytes([channel & 0xFF])))
            self.ser.flush()
            time.sleep(0.02)
            if self.ser.in_waiting:
                self.ser.read(self.ser.in_waiting)
            return True
        except (serial.SerialException, OSError) as e:
            self.close()
            raise serial.SerialException(f"Serial communication lost: {e}")
        except Exception:
            return False

    def query_vol(self) -> Optional[int]:
        """Query current volume level (0x09 GET_VOL)."""
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")
        try:
            self.ser.write(frame_spp(0x09))
            self.ser.flush()
            t0 = time.time()
            buf = bytearray()
            while time.time() - t0 < 0.06:
                if self.ser.in_waiting:
                    buf.extend(self.ser.read(self.ser.in_waiting))
                    pkts = extract_packets(bytes(buf))
                    for cmd, body in pkts:
                        if cmd == 0x09 and len(body) >= 1:
                            return body[0]
                time.sleep(0.005)
        except (serial.SerialException, OSError) as e:
            self.close()
            raise serial.SerialException(f"Serial communication lost: {e}")
        except Exception:
            pass
        return None

    def set_vol(self, vol: int) -> bool:
        """Set volume level (0x08 SET_VOL)."""
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")
        try:
            self.ser.write(frame_spp(0x08, bytes([max(0, min(16, vol))])))
            self.ser.flush()
            time.sleep(0.01)
            if self.ser.in_waiting:
                self.ser.read(self.ser.in_waiting)
            return True
        except (serial.SerialException, OSError) as e:
            self.close()
            raise serial.SerialException(f"Serial communication lost: {e}")
        except Exception:
            return False

    def query_work_mode(self) -> Optional[int]:
        """Query work mode (0x13 GET_WORK_MODE)."""
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")
        try:
            self.ser.write(frame_spp(0x13))
            self.ser.flush()
            t0 = time.time()
            buf = bytearray()
            while time.time() - t0 < 0.06:
                if self.ser.in_waiting:
                    buf.extend(self.ser.read(self.ser.in_waiting))
                    pkts = extract_packets(bytes(buf))
                    for cmd, body in pkts:
                        if cmd == 0x13 and len(body) >= 1:
                            return body[0]
                time.sleep(0.005)
        except (serial.SerialException, OSError) as e:
            self.close()
            raise serial.SerialException(f"Serial communication lost: {e}")
        except Exception:
            pass
        return None

    def poll_event(self) -> InputEvent:
        """
        Poll MiniToo hardware state for knob turns or button presses.
        Returns NEXT_PAGE, PREV_PAGE, TOGGLE_PAUSE, or NONE.
        """
        if not self.ser or not self.ser.is_open:
            raise serial.SerialException("Serial port is not open")

        now = time.time()
        # Rate limit polling to ~16 Hz
        if now - self.last_poll_time < self.poll_interval:
            return InputEvent.NONE
        self.last_poll_time = now

        vol = self.query_vol()
        if vol is None:
            return InputEvent.NONE

        # Enforce debounce cooldown
        in_cooldown = (now - self.last_event_time < self.debounce_secs)

        # Check volume knob clockwise (increment) -> NEXT PAGE
        if vol > self.target_base_vol:
            # Immediately restore center volume
            self.set_vol(self.target_base_vol)
            if not in_cooldown:
                print(f"[INPUT] Knob Clockwise detected: vol {self.target_base_vol} -> {vol} => NEXT PAGE")
                self.last_event_time = now
                return InputEvent.NEXT_PAGE

        # Check volume knob counter-clockwise (decrement) -> PREV PAGE
        elif vol < self.target_base_vol:
            # Immediately restore center volume
            self.set_vol(self.target_base_vol)
            if not in_cooldown:
                print(f"[INPUT] Knob Counter-Clockwise detected: vol {self.target_base_vol} -> {vol} => PREVIOUS PAGE")
                self.last_event_time = now
                return InputEvent.PREV_PAGE

        return InputEvent.NONE

    def close(self) -> None:
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
