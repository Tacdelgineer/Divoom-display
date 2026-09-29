# Divoom Ditoo / Ditoo Plus 16x16 Protocol & Integration Specification

This document details the reverse-engineered hardware architecture, transport protocol, frame serialization, and operational behavior for the **Divoom Ditoo / Ditoo Plus** 16x16 RGB pixel display.

---

## 1. Hardware Detection & Windows Identification

### A. Bluetooth Low Energy (Control & Pixel Streaming)
- **Advertised Device Name:** `DitooPro-Light` (or `Ditoo-Light`)
- **BLE MAC Address:** `B1:21:81:5B:E3:16`
- **Signal Strength:** ~ -80 dBm
- **Primary Service:** Microchip ISSC Transparent UART (`49535343-fe7d-4ae5-8fa9-9fafd205e455`)
- **ATT MTU:** Negotiated up to 527 bytes
- **Pairing Requirement:** **None**. Direct GATT connection via Windows WinRT / Bleak without SMP PIN bonding.

### B. USB Composite Interface (When Tethered by Cable)
- **Device Description:** `Ditoo usb audio`
- **Hardware ID:** `USB\VID_8888&PID_1719\20190808`
- **Interfaces:**
  - `MI_00`: USB Audio Endpoint (Speakers & Microphone)
  - `MI_03`: USB HID Consumer Control
  - `MI_04`: USB HID Vendor-Defined Interface

### C. Classic Bluetooth Audio (A2DP / AVRCP)
- **Device Name:** `DitooPro-Audio` (or `Ditoo-Audio`)
- **Vendor ID:** `0x05D6` (Divoom) / `PID 0x000A`
- **SPP COM Port:** Automatically mapped if user pairs the device under Windows Settings > Bluetooth.

---

## 2. GATT Characteristic Mapping

| Characteristic UUID | Direction | Properties | Function |
|---|---|---|---|
| `49535343-8841-43f4-a8d4-ecbe34729bb3` | Host → Device (TX) | `Write`, `WriteWithoutResponse` | Transparent UART Data Write |
| `49535343-1e4d-4bd9-ba61-23c647249616` | Device → Host (RX) | `Notify`, `WriteWithoutResponse` | Transparent UART Notifications |
| `49535343-aca3-481c-91ec-d85e28a60318` | Bidirectional | `Write`, `Notify` | Flow Control / Air Patch |
| `49535343-6daa-4d02-abf6-19569aca69fe` | Device → Host | `Read` | Status Register |

---

## 3. Divoom Packet Framing Envelope

All communication frames sent over BLE or SPP must adhere to the standard Divoom serial envelope:

```
[0x01] [Length LSB] [Length MSB] [CMD] [PAYLOAD...] [CRC LSB] [CRC MSB] [0x02]
```

- **`0x01`**: Start of Frame delimiter.
- **`Length`** (2 bytes, Little-Endian): Declared length = `len(PAYLOAD) + 3` (includes CMD and Length bytes).
- **`CMD`** (1 byte): Command identifier (e.g. `0x8B`, `0x49`, `0x45`, `0x09`).
- **`CRC`** (2 bytes, Little-Endian): Arithmetic sum of all bytes between `0x01` and `CRC`:
  $$\text{CRC} = \left(\sum_{i=1}^{N-3} \text{byte}[i]\right) \pmod{65536}$$
- **`0x02`**: End of Frame delimiter.

---

## 4. 16x16 Pixel Art Frame Binary Encoding

A 16x16 pixel frame uses a compressed indexed-color bitmap structure:

```
[0xAA] [Length 2B LE] [Delay 2B LE] [ReusePalette 1B] [ColorCount 1B] [Palette N*3B] [PixelData M*B]
```

1. **Magic Header:** Fixed `0xAA`.
2. **Length (2B LE):** Total frame bytes = `7 + (ColorCount * 3) + len(PixelData)`.
3. **Delay (2B LE):** Frame dwell time in milliseconds (0 for static).
4. **Reuse Palette (1B):** `0x00` (new palette) or `0x01` (reuse previous).
5. **Color Count (1B):** Number of colors in the local palette (e.g. 2 for binary, up to 256).
6. **Local Palette:** $N \times 3$ bytes in sequential RGB order.
7. **Pixel Data:** Bit-packed color indices in little-endian order.
   - Bits per pixel = $\max(1, \lceil\log_2(\text{ColorCount})\rceil)$.
   - 256 pixels total ($16 \times 16$).
   - Packed into $\lceil (256 \times \text{bpp}) / 8 \rceil$ bytes.

---

## 5. Streaming Commands

### A. Command `0x8B` (New GIF / Multi-Packet Streaming)
Used by official Divoom apps for modern firmware:
1. **Start Packet:** `CMD=0x8B`, payload `[0x00, FileSize 4B LE, 0x00]`.
2. **Data Chunks:** `CMD=0x8B`, payload `[0x01, FileSize 4B LE, OffsetID 2B LE, ChunkData <= 256B]`.

### B. Command `0x45` (Lightning & Instant Screen Control)
- **Solid Color Fill:** Payload `[0x01, R, G, B, Brightness, 0x00, 0x01, 0x00, 0x00, 0x00]`.

---

## 6. Hardware Proof-of-Life Sequence

The proof-of-life sequence validates full end-to-end transport:
1. **Solid Red:** Full frame fill (255, 0, 0)
2. **Solid Green:** Full frame fill (0, 255, 0)
3. **Solid Blue:** Full frame fill (0, 0, 255)
4. **Checkerboard Pattern:** Alternating black/white pixel grid
5. **Simple Animation:** Concentric diamond cyan expansion pulse

---

## 7. Controls & Physical Input Events Investigation

- **Physical Controls on Hardware:**
  - Mechanical clicky keyboard (Left, Right, Enter, Menu, Up, Down)
  - Vintage pull lever / joystick
  - Side power button & volume buttons
- **GATT Notification Audit:**
  - An active hardware audit was conducted using `tools/test_ditoo_controls.py` by subscribing to notifications on the BLE Transparent UART RX characteristic (`49535343-1e4d-4bd9-ba61-23c647249616`) on physical hardware (`B1:21:81:5B:E3:16`).
  - Key presses and lever actions were executed while monitoring the notification stream.
- **Finding:**
  - **Zero notification packets** are emitted over BLE UART during physical keyboard or lever events.
  - The internal Ditoo MCU firmware routes mechanical keyboard and lever inputs exclusively to onboard applications (e.g. Pixel Games, Alarms, Voice Memos, Clock face) and local volume control. The standard pixel-streaming BLE firmware does not export raw key/joystick HID events over GATT.
  - Consequently, playlist navigation (Previous / Next / Pause / Resume) is controlled directly from the Desktop Dashboard UI.

---

## 8. Display Brightness Control

- **Command `0x74` (Set Brightness):**
  - Payload: `[Brightness 1B]` where Brightness is an integer from `0` to `100` (`0x00` - `0x64`).
  - Framing: `[0x01, 0x04, 0x00, 0x74, Brightness, CRC_L, CRC_H, 0x02]`.
  - Effect: Instantly adjusts LED panel illumination across all 256 RGB pixels without interrupting or invalidating active frame buffers.

---

## 9. Audio Isolation Guarantee

- The application communicates **exclusively** with the Bluetooth Low Energy endpoint:
  - Advertised name: `DitooPro-Light`
  - MAC address: `B1:21:81:5B:E3:16`
  - Service: ISSC Transparent UART (`49535343-fe7d-4ae5-8fa9-9fafd205e455`)
- The Bluetooth Classic audio endpoint `DitooPro-Audio` is **never** accessed, selected, or routed. Windows Default Audio Device settings and routing remain 100% untouched.

---

## 10. Power Loss, Auto-Reconnect & Offline Resilience

- **Connection Lifecycle:**
  - `DitooController` maintains an autonomous async background engine.
  - On startup or connection drop, the controller attempts reconnect to `DitooPro-Light` with a 3-second retry backoff.
  - If MAC address changes, an automatic BLE scanner fallback identifies `DitooPro-Light` by name.
  - Upon reconnection, brightness and active animation sequence resume automatically.
- **Data Caching:**
  - Market data for Cryptos (CoinGecko) and Stocks (Yahoo Finance) is polled independently every 35 seconds.
  - Last good quotes are persistently cached locally.
  - Network timeouts, rate-limits, or offline states never blank the display.

